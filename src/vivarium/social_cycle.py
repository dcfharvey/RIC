"""Cycle social autonome, borné et fondé sur des faits canoniques.

Le cycle ne déduit jamais une relation, une permission ou une vérité depuis une
phrase. Il ne fait que :

* repérer une rencontre encore présente après un déplacement canonique ;
* ouvrir une scène append-only avec sa provenance dans la clé de scène ;
* offrir au plus une occasion de parole par tick ;
* fermer explicitement une scène arrivée à sa borne ou devenue impossible.

Les choix de mots restent au fournisseur de scène; l'existence de l'occasion,
ses participantes et sa limite restent déterministes.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from .cognition_policy import CognitionCallLimits
from .cognitive_flow import CognitiveFlowScheduler
from .diagnostics import DiagnosticRecorder
from .scene_scheduler import SceneSchedulerError, SceneTurnScheduler
from .scene_turn import SceneTurnProvider, SceneTurnResult, SceneTurnService
from .social_cognition_runtime import LiveSocialCognitionOutcome, LiveSocialCognitionService
from .scenes import SceneError, SocialSceneService
from .util import Clock, parse_iso, to_iso
from .world import WorldEngine


MAX_SCENE_TURNS = 4


class SocialCycleError(ValueError):
    """Paramètre de cycle invalide, sans écriture partielle."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SocialCycleOutcome:
    opened_scene_keys: tuple[str, ...]
    closed_scene_keys: tuple[str, ...]
    interrupted_scene_keys: tuple[str, ...]
    turn: SceneTurnResult | None
    cognition: tuple[LiveSocialCognitionOutcome, ...] = ()


class SocialSceneCycle:
    """Raccorde rencontres canoniques et tours LLM, sans boucle non bornée."""

    def __init__(
        self, conn: sqlite3.Connection, provider: SceneTurnProvider,
        clock: Clock | None = None, interpretation_provider: Any | None = None,
        admission_policy: Any = None, appraisal_provider: Any | None = None, affect_provider: Any | None = None,
        diagnostics: DiagnosticRecorder | None = None,
        flow_scheduler: CognitiveFlowScheduler | None = None,
    ) -> None:
        self._conn = conn
        self._provider = provider
        self._interpretation_provider = interpretation_provider
        self._admission_policy = admission_policy
        self._appraisal_provider = appraisal_provider
        self._affect_provider = affect_provider
        self._diagnostics = diagnostics
        self._flow_scheduler = flow_scheduler
        self._clock = clock or Clock()
        self._scenes = SocialSceneService(conn, clock=self._clock)
        self._scheduler = SceneTurnScheduler(conn)
        # Cache technique, reconstructible depuis le journal d'admissions.
        # Il ne fait pas partie du canon et évite de repoller un même tour à
        # chaque pulsation pendant que son budget est encore fermé.
        self._deferred_until_by_turn: dict[str, str] = {}

    def _budget_release_at(
        self, world_id: int, character_key: str, limits: CognitionCallLimits,
        reason_code: str,
    ) -> str | None:
        rows = self._conn.execute(
            "SELECT a.admitted_at FROM cognition_call_admission a "
            "JOIN character c ON c.id=a.character_id "
            "WHERE a.world_id=? AND c.key=? ORDER BY a.admitted_at, a.id",
            (world_id, character_key),
        ).fetchall()
        if not rows:
            return None
        now = parse_iso(WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id))
        instants = [parse_iso(row["admitted_at"]) for row in rows]
        if reason_code == "debounced":
            return to_iso(instants[-1] + timedelta(seconds=limits.debounce_seconds))
        if reason_code == "budget_exhausted":
            inside = [
                instant for instant in instants
                if (now - instant).total_seconds() < limits.budget_window_seconds
            ]
            if len(inside) >= limits.max_calls_per_window:
                return to_iso(
                    inside[0] + timedelta(seconds=limits.budget_window_seconds)
                )
        return None

    @staticmethod
    def _world_id(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise SocialCycleError("monde invalide", code="invalid_social_cycle")
        return value

    @staticmethod
    def _max_turns(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= MAX_SCENE_TURNS:
            raise SocialCycleError("borne de tours invalide", code="invalid_social_cycle")
        return value

    def _sapient(self, world_id: int, character_key: str) -> bool:
        row = self._conn.execute(
            "SELECT o.resolved_initial_definition_json "
            "FROM character_instance_origin o JOIN character c ON c.id = o.character_id "
            "WHERE o.world_id = ? AND c.key = ?",
            (world_id, character_key),
        ).fetchone()
        if row is None:
            return False
        try:
            definition = json.loads(row["resolved_initial_definition_json"])
            components = definition.get("components", [])
            return any(
                component.get("key") == "cognition.profile"
                and component.get("config", {}).get("level") == "sapient"
                for component in components
                if isinstance(component, dict)
            )
        except (TypeError, ValueError):
            return False

    def _active_participants(self, world_id: int) -> set[str]:
        rows = self._conn.execute(
            "SELECT c.key FROM social_scene s "
            "JOIN social_scene_participant p ON p.scene_id = s.id "
            "JOIN character c ON c.id = p.character_id "
            "WHERE s.world_id = ? AND s.status = 'active'",
            (world_id,),
        ).fetchall()
        return {row["key"] for row in rows}

    def _encounter_candidates(self, world_id: int) -> tuple[tuple[int, str, str], ...]:
        """Rencontres encore présentes, déduites des derniers déplacements.

        Une scène est ancrée dans le numéro du déplacement qui a créé la
        co-présence. La clé rend la découverte idempotente même après redémarrage
        et évite un curseur parallèle ou une seconde source de vérité.
        """
        active = self._active_participants(world_id)
        # Le contexte initial est un fait canonique : les volontaires arrivent
        # ensemble au point de départ. Sans ce cas explicite, une nouvelle
        # simulation pourrait attendre longtemps un déplacement fortuit avant
        # que sa première interaction sociale soit même admissible. Il est
        # volontairement unique : dès qu'une scène (même fermée) existe, les
        # rencontres ne sont plus déclenchées que par des déplacements réels.
        has_prior_scene = self._conn.execute(
            "SELECT 1 FROM social_scene WHERE world_id = ? LIMIT 1", (world_id,)
        ).fetchone()
        has_movement = self._conn.execute(
            "SELECT 1 FROM canonical_event "
            "WHERE world_id = ? AND event_type = 'character_moved' LIMIT 1",
            (world_id,),
        ).fetchone()
        if has_prior_scene is None and has_movement is None:
            initial = self._conn.execute(
                "SELECT seq FROM canonical_event "
                "WHERE world_id = ? AND event_type = 'world_initial_context_set' "
                "ORDER BY seq DESC LIMIT 1",
                (world_id,),
            ).fetchone()
            colocated = self._conn.execute(
                "SELECT c.key FROM character c JOIN location l ON l.id = c.current_location_id "
                "WHERE c.world_id = ? ORDER BY l.key, c.key",
                (world_id,),
            ).fetchall()
            sapients = [
                row["key"] for row in colocated if self._sapient(world_id, row["key"])
            ]
            if initial is not None and len(sapients) >= 2:
                first, second = sapients[0], sapients[1]
                first_location = self._conn.execute(
                    "SELECT l.key FROM character c JOIN location l ON l.id = c.current_location_id "
                    "WHERE c.world_id = ? AND c.key = ?",
                    (world_id, first),
                ).fetchone()
                second_location = self._conn.execute(
                    "SELECT l.key FROM character c JOIN location l ON l.id = c.current_location_id "
                    "WHERE c.world_id = ? AND c.key = ?",
                    (world_id, second),
                ).fetchone()
                if (
                    first_location is not None
                    and second_location is not None
                    and first_location["key"] == second_location["key"]
                ):
                    return ((initial["seq"], first, second),)
        events = self._conn.execute(
            "SELECT seq, payload FROM canonical_event "
            "WHERE world_id = ? AND event_type = 'character_moved' "
            "ORDER BY seq DESC LIMIT 32",
            (world_id,),
        ).fetchall()
        found: list[tuple[int, str, str]] = []
        # L'état de présence lu est courant : le déplacement le plus récent est
        # donc le seul qui peut raisonnablement représenter l'arrivée encore
        # observée. Traiter les anciens d'abord créerait une rencontre attribuée
        # à tort à une position déjà dépassée.
        for event in events:
            try:
                payload = json.loads(event["payload"])
                actor = payload["character"]
                destination = payload["to"]
            except (KeyError, TypeError, ValueError):
                continue
            if not isinstance(actor, str) or not isinstance(destination, str):
                continue
            if actor in active or not self._sapient(world_id, actor):
                continue
            companions = self._conn.execute(
                "SELECT c.key FROM character c JOIN location l ON l.id = c.current_location_id "
                "WHERE c.world_id = ? AND l.key = ? AND c.key <> ? ORDER BY c.key",
                (world_id, destination, actor),
            ).fetchall()
            for companion_row in companions:
                companion = companion_row["key"]
                if companion in active or not self._sapient(world_id, companion):
                    continue
                found.append((event["seq"], actor, companion))
                active.update({actor, companion})
                break
        return tuple(found)

    def _idle_encounter_candidates(self, world_id: int) -> tuple[tuple[int, str, str], ...]:
        """Occasions sociales uniques ancrées au début d'un idle source.

        Ce n'est pas une minuterie sociale. Une activité `idle` active est un
        fait canonique avec un début, un lieu et une échéance; une co-présence
        sapiente à ce début peut donc ouvrir une seule scène bornée. La clé
        fondée sur `activity_started.seq` empêche toute réouverture après la
        fermeture normale de cette occasion.
        """
        active = self._active_participants(world_id)
        events = self._conn.execute(
            "SELECT seq, payload FROM canonical_event "
            "WHERE world_id = ? AND event_type = 'activity_started' "
            "ORDER BY seq DESC LIMIT 64",
            (world_id,),
        ).fetchall()
        found: list[tuple[int, str, str]] = []
        for event in events:
            try:
                payload = json.loads(event["payload"])
                actor = payload["character"]
                activity = payload["activity"]
                location = payload["location"]
            except (KeyError, TypeError, ValueError):
                continue
            if (
                activity != "idle"
                or not isinstance(actor, str)
                or not isinstance(location, str)
                or actor in active
                or not self._sapient(world_id, actor)
            ):
                continue
            # L'événement historique ne suffit pas : son attente doit encore
            # être l'activité active du personnage, dans ce même lieu.
            still_idle = self._conn.execute(
                "SELECT 1 FROM activity a "
                "JOIN character c ON c.id = a.character_id "
                "JOIN location l ON l.id = a.location_id "
                "WHERE a.world_id = ? AND c.key = ? AND a.status = 'active' "
                "AND a.type = 'idle' AND l.key = ?",
                (world_id, actor, location),
            ).fetchone()
            if still_idle is None:
                continue
            companions = self._conn.execute(
                "SELECT c.key FROM character c "
                "JOIN location l ON l.id = c.current_location_id "
                "WHERE c.world_id = ? AND l.key = ? AND c.key <> ? ORDER BY c.key",
                (world_id, location, actor),
            ).fetchall()
            for companion_row in companions:
                companion = companion_row["key"]
                if companion in active or not self._sapient(world_id, companion):
                    continue
                found.append((event["seq"], actor, companion))
                active.update({actor, companion})
                break
        return tuple(found)

    def _open_candidate(self, world_id: int, scene_key: str, actor: str, companion: str) -> bool:
        """Ouvre une scène si sa provenance n'a jamais déjà été consommée."""
        try:
            before = self._scenes.sheet(world_id, scene_key)
        except SceneError as exc:
            if exc.code != "scene_not_found":
                raise SocialCycleError(str(exc), code=exc.code) from exc
            before = None
        if before is not None:
            return False
        try:
            self._scenes.open(world_id, scene_key, (actor, companion))
        except SceneError as exc:
            # Une participante peut avoir bougé entre la lecture et
            # l'ouverture : la rencontre est simplement devenue caduque.
            if exc.code == "scene_participants_not_colocated":
                return False
            raise SocialCycleError(str(exc), code=exc.code) from exc
        return True

    def discover(self, world_id: Any) -> tuple[str, ...]:
        """Ouvre au plus une scène par nouvelle rencontre disponible."""
        world_id = self._world_id(world_id)
        opened: list[str] = []
        for event_seq, actor, companion in self._encounter_candidates(world_id):
            scene_key = f"encounter_{event_seq}_{actor}_{companion}"
            if self._open_candidate(world_id, scene_key, actor, companion):
                opened.append(scene_key)
        for event_seq, actor, companion in self._idle_encounter_candidates(world_id):
            scene_key = f"idle_encounter_{event_seq}_{actor}_{companion}"
            if self._open_candidate(world_id, scene_key, actor, companion):
                opened.append(scene_key)
        return tuple(opened)

    def tick(
        self, world_id: Any, limits: Any, *, max_turns: Any = MAX_SCENE_TURNS
    ) -> SocialCycleOutcome:
        """Découvre des rencontres puis traite au plus un tour de scène."""
        world_id, max_turns = self._world_id(world_id), self._max_turns(max_turns)
        if not isinstance(limits, CognitionCallLimits):
            raise SocialCycleError("limites cognitives invalides", code="invalid_social_cycle")
        limits.validated()
        opened = self.discover(world_id)
        closed: list[str] = []
        interrupted: list[str] = []
        cognition: list[LiveSocialCognitionOutcome] = []
        if self._interpretation_provider is not None:
            pending = LiveSocialCognitionService(
                self._conn, self._interpretation_provider, clock=self._clock,
                admission_policy=self._admission_policy,
                appraisal_provider=self._appraisal_provider,
                affect_provider=self._affect_provider,
                diagnostics=self._diagnostics,
                flow_scheduler=self._flow_scheduler,
            ).retry_one_pending(world_id, limits)
            if pending is not None:
                cognition.append(pending)
        active = self._conn.execute(
            "SELECT scene_key FROM social_scene WHERE world_id = ? AND status = 'active' ORDER BY id",
            (world_id,),
        ).fetchall()
        for row in active:
            scene_key = row["scene_key"]
            try:
                opportunity = self._scheduler.next_opportunity(world_id, scene_key, max_turns=max_turns)
            except SceneSchedulerError as exc:
                if exc.code == "scene_participants_not_colocated":
                    self._scenes.close(world_id, scene_key, reason="participant_departed", interrupted=True)
                    interrupted.append(scene_key)
                    continue
                raise SocialCycleError(str(exc), code=exc.code) from exc
            if opportunity is None:
                self._scenes.close(world_id, scene_key, reason="turn_budget_complete")
                closed.append(scene_key)
                continue
            canonical_now = WorldEngine(
                self._conn, clock=self._clock
            ).read_canonical_time(world_id)
            deferred_until = self._deferred_until_by_turn.get(opportunity.turn_key)
            if deferred_until is not None and canonical_now < deferred_until:
                continue
            self._deferred_until_by_turn.pop(opportunity.turn_key, None)
            result = SceneTurnService(
                self._conn, self._provider, clock=self._clock, diagnostics=self._diagnostics,
                flow_scheduler=self._flow_scheduler,
            ).run(
                world_id, scene_key, opportunity.speaker_key, opportunity.turn_key, limits
            )
            if result.deferred_reason_code in {"debounced", "budget_exhausted"}:
                release_at = self._budget_release_at(
                    world_id, opportunity.speaker_key, limits,
                    result.deferred_reason_code,
                )
                if release_at is not None and release_at > canonical_now:
                    self._deferred_until_by_turn[opportunity.turn_key] = release_at
            if result.speech is not None and self._interpretation_provider is not None:
                cognition.extend(LiveSocialCognitionService(
                    self._conn, self._interpretation_provider, clock=self._clock,
                    admission_policy=self._admission_policy,
                    appraisal_provider=self._appraisal_provider,
                    affect_provider=self._affect_provider,
                    diagnostics=self._diagnostics,
                    flow_scheduler=self._flow_scheduler,
                ).process_speech(self._world_id(world_id), scene_key, opportunity.turn_key, limits))
            return SocialCycleOutcome(tuple(opened), tuple(closed), tuple(interrupted), result, tuple(cognition))
        return SocialCycleOutcome(tuple(opened), tuple(closed), tuple(interrupted), None, tuple(cognition))
