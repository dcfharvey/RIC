"""Contrats inactifs de checkpoints et de terminaison du sommeil.

La politique est une calibration d'ingenierie versionnee. L'evaluateur pur ne
lit ni les besoins legacy ni SQLite : dans un raccord futur, les entrees de
viabilite devront venir du proprietaire physiologique et un reveil externe
devra etre prouve par le moteur avant d'etre transmis ici. Aucun resultat de
ce module ne complete, n'interrompt ou ne reveille une activite par lui-meme.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Literal, Mapping

from .db import transaction
from .registry import _KEY_RE
from .sleep_physiology import OwnerBackedWakeViability, SleepPhysiologyService
from .util import Clock, new_uuid, parse_iso, to_iso


_BANDS = frozenset({"continue_sleep", "wake_admissible"})
_FIELDS = frozenset({
    "schema_version", "checkpoint_interval_seconds", "hard_cap_seconds",
    "wake_admissible_enter_milli", "wake_admissible_exit_milli",
})


class SleepTerminationError(ValueError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SleepTerminationPolicy:
    """Politique complete sans calibration implicite ni semantique biologique."""

    policy_key: str
    version: int
    checkpoint_interval_seconds: int
    hard_cap_seconds: int
    wake_admissible_enter_milli: int
    wake_admissible_exit_milli: int
    provenance: str
    created_at: str


@dataclass(frozen=True)
class SleepCheckpointEvaluation:
    """Projection pure; ``hard_cap`` ne rend jamais une completion eligible."""

    band: Literal["continue_sleep", "wake_admissible"]
    completion_eligible: bool
    reason_code: Literal[
        "continue_sleep", "wake_admissible", "external_wake_accessible", "hard_cap_protective"
    ]
    next_reassessment_after_seconds: int | None
    hard_cap_reached: bool


@dataclass(frozen=True)
class SleepCompletionAuthorization:
    """Preuve privee liee a un episode/frontiere, consommable une seule fois."""

    id: int
    checkpoint_id: int
    activity_id: int
    boundary_at: str
    reason_code: str
    consumed: bool


def _key(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise SleepTerminationError(f"{field} invalide", code="invalid_configuration")
    return value


def _integer(value: Any, *, field: str, minimum: int, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum \
            or (maximum is not None and value > maximum):
        raise SleepTerminationError(f"{field} invalide", code="invalid_configuration")
    return value


def _payload(value: Any) -> dict[str, int]:
    """Exige tous les parametres, sans fournir de valeur de production."""
    if not isinstance(value, Mapping) or set(value) != _FIELDS or value.get("schema_version") != 1:
        raise SleepTerminationError("politique de terminaison invalide", code="invalid_configuration")
    interval = _integer(value["checkpoint_interval_seconds"], field="intervalle", minimum=1)
    hard_cap = _integer(value["hard_cap_seconds"], field="hard cap", minimum=interval)
    enter = _integer(value["wake_admissible_enter_milli"], field="entree reveil", minimum=0, maximum=100_000)
    exit_ = _integer(value["wake_admissible_exit_milli"], field="sortie reveil", minimum=0, maximum=100_000)
    if exit_ >= enter:
        raise SleepTerminationError("hysterese de reveil invalide", code="invalid_configuration")
    return {
        "schema_version": 1,
        "checkpoint_interval_seconds": interval,
        "hard_cap_seconds": hard_cap,
        "wake_admissible_enter_milli": enter,
        "wake_admissible_exit_milli": exit_,
    }


def _json(value: Any, *, field: str) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise SleepTerminationError(f"{field} invalide", code="invalid_configuration") from exc


def evaluate_sleep_checkpoint(
    policy: SleepTerminationPolicy,
    *,
    elapsed_seconds: Any,
    wake_viability_milli: Any,
    previous_band: Any,
    external_wake_accessible: Any = False,
) -> SleepCheckpointEvaluation:
    """Evalue une frontiere sans appliquer de transition moteur.

    ``wake_viability_milli`` est une projection future du proprietaire
    physiologique, pas une lecture libre par cognition. L'argument de reveil
    externe n'existe ici que pour le banc : le raccord production devra le
    remplacer par une cause canonique accessible et validee.
    """
    elapsed = _integer(elapsed_seconds, field="duree de sommeil", minimum=0)
    viability = _integer(wake_viability_milli, field="viabilite de reveil", minimum=0, maximum=100_000)
    if previous_band not in _BANDS:
        raise SleepTerminationError("bande precedente invalide", code="invalid_checkpoint")
    if not isinstance(external_wake_accessible, bool):
        raise SleepTerminationError("reveil externe invalide", code="invalid_checkpoint")

    if previous_band == "continue_sleep":
        band = "wake_admissible" if viability >= policy.wake_admissible_enter_milli else "continue_sleep"
    else:
        band = "wake_admissible" if viability >= policy.wake_admissible_exit_milli else "continue_sleep"

    if external_wake_accessible:
        return SleepCheckpointEvaluation(band, True, "external_wake_accessible", None, False)
    if band == "wake_admissible":
        return SleepCheckpointEvaluation(band, True, "wake_admissible", None, False)
    if elapsed >= policy.hard_cap_seconds:
        return SleepCheckpointEvaluation(band, False, "hard_cap_protective", None, True)
    return SleepCheckpointEvaluation(
        band, False, "continue_sleep", min(policy.checkpoint_interval_seconds, policy.hard_cap_seconds - elapsed), False
    )


class SleepTerminationFoundationService:
    """Owner du catalogue/assignment et des preuves privees, jamais de l'activite."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _world_id(self, value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise SleepTerminationError("monde invalide", code="invalid_world")
        if self._conn.execute("SELECT 1 FROM worlds WHERE id = ?", (value,)).fetchone() is None:
            raise SleepTerminationError("monde introuvable", code="world_not_found")
        return value

    def register_policy(self, policy_key: Any, version: Any, configuration: Any, provenance: Any) -> SleepTerminationPolicy:
        key = _key(policy_key, field="politique")
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            raise SleepTerminationError("version invalide", code="invalid_configuration")
        payload, origin, now = _payload(configuration), _key(provenance, field="provenance"), self._clock.now_iso()
        try:
            with transaction(self._conn) as conn:
                conn.execute("INSERT INTO sleep_termination_policy (public_id,policy_key,version,policy_json,provenance,created_at) VALUES (?,?,?,?,?,?)", (new_uuid(),key,version,_json(payload,field="politique"),origin,now))
        except sqlite3.IntegrityError as exc:
            raise SleepTerminationError("politique de terminaison deja enregistree", code="duplicate_policy") from exc
        return self.policy(key, version)

    def policy(self, policy_key: Any, version: Any) -> SleepTerminationPolicy:
        key = _key(policy_key, field="politique")
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            raise SleepTerminationError("version invalide", code="invalid_configuration")
        row = self._conn.execute("SELECT policy_key,version,policy_json,provenance,created_at FROM sleep_termination_policy WHERE policy_key=? AND version=?", (key,version)).fetchone()
        if row is None:
            raise SleepTerminationError("politique de terminaison introuvable", code="policy_not_found")
        payload = _payload(json.loads(row["policy_json"]))
        return SleepTerminationPolicy(row["policy_key"], int(row["version"]), payload["checkpoint_interval_seconds"], payload["hard_cap_seconds"], payload["wake_admissible_enter_milli"], payload["wake_admissible_exit_milli"], row["provenance"], row["created_at"])

    def assign_policy(self, world_id: Any, policy_key: Any, version: Any, provenance: Any) -> SleepTerminationPolicy:
        world, policy = self._world_id(world_id), self.policy(policy_key, version)
        origin, now = _key(provenance, field="provenance"), self._clock.now_iso()
        policy_id = self._conn.execute("SELECT id FROM sleep_termination_policy WHERE policy_key=? AND version=?", (policy.policy_key,policy.version)).fetchone()["id"]
        try:
            with transaction(self._conn) as conn:
                conn.execute("INSERT INTO world_sleep_termination_policy_assignment (public_id,world_id,policy_id,assigned_at,provenance,created_at) VALUES (?,?,?,?,?,?)", (new_uuid(),world,policy_id,now,origin,now))
        except sqlite3.IntegrityError as exc:
            raise SleepTerminationError("monde deja assigne", code="duplicate_assignment") from exc
        return policy

    def world_policy(self, world_id: Any) -> SleepTerminationPolicy:
        world = self._world_id(world_id)
        row = self._conn.execute("SELECT p.policy_key,p.version FROM world_sleep_termination_policy_assignment a JOIN sleep_termination_policy p ON p.id=a.policy_id WHERE a.world_id=?", (world,)).fetchone()
        if row is None:
            raise SleepTerminationError("politique de terminaison non assignee", code="policy_not_assigned")
        return self.policy(row["policy_key"], int(row["version"]))

    @staticmethod
    def _authorization(row: sqlite3.Row) -> SleepCompletionAuthorization:
        try:
            evidence = json.loads(row["evaluation_json"])
        except (TypeError, ValueError) as exc:
            raise SleepTerminationError("autorisation illisible", code="invalid_authorization") from exc
        if not isinstance(evidence, Mapping) or not isinstance(evidence.get("reason_code"), str):
            raise SleepTerminationError("autorisation invalide", code="invalid_authorization")
        return SleepCompletionAuthorization(
            int(row["id"]), int(row["checkpoint_id"]), int(row["activity_id"]),
            row["boundary_at"], evidence["reason_code"], row["consumed_event_id"] is not None,
        )

    def authorize_completion(
        self,
        world_id: Any,
        character_key: Any,
        *,
        at_time: Any,
        wake_viability_milli: Any,
        external_wake_accessible: Any = False,
        _projection: OwnerBackedWakeViability | None = None,
    ) -> SleepCompletionAuthorization:
        """Emet une preuve seulement apres re-evaluation du checkpoint persiste.

        La preuve est liee au checkpoint, a l'episode, a la politique assignee et
        a la frontiere exacte. Elle n'applique aucune transition canonique. Le
        trigger de migration 0055 exige ensuite cette preuve lors de l'evenement
        ``activity_completed`` et la consomme dans la meme transaction.

        Tant qu'aucun owner Reality/Interaction ne fournit un evenement de reveil
        accessible type, cette API refuse explicitement de fabriquer cette cause.
        """
        world = self._world_id(world_id)
        character = _key(character_key, field="personnage")
        if not isinstance(external_wake_accessible, bool):
            raise SleepTerminationError("reveil externe invalide", code="invalid_checkpoint")
        if external_wake_accessible:
            raise SleepTerminationError(
                "reveil externe non raccorde", code="external_wake_not_supported"
            )
        try:
            at = to_iso(parse_iso(at_time))
        except (TypeError, ValueError) as exc:
            raise SleepTerminationError("frontiere d'autorisation invalide", code="invalid_checkpoint") from exc

        row = self._conn.execute(
            "SELECT cp.id AS checkpoint_id,cp.activity_id,cp.policy_id,cp.next_reassessment_at,"
            "cp.previous_band,cp.hard_cap_at,a.started_at,a.status,ch.id AS character_id "
            "FROM activity_sleep_checkpoint cp "
            "JOIN activity a ON a.id=cp.activity_id "
            "JOIN character ch ON ch.id=cp.character_id AND ch.world_id=cp.world_id "
            "WHERE cp.world_id=? AND ch.key=? ORDER BY cp.id DESC LIMIT 1",
            (world, character),
        ).fetchone()
        if row is None or row["status"] != "active":
            raise SleepTerminationError("checkpoint actif absent", code="checkpoint_missing")
        if parse_iso(at) < parse_iso(row["next_reassessment_at"]):
            raise SleepTerminationError("checkpoint pas encore du", code="checkpoint_not_due")
        if parse_iso(at) > parse_iso(row["hard_cap_at"]):
            raise SleepTerminationError("checkpoint apres hard cap", code="checkpoint_after_hard_cap")

        assignment = self._conn.execute(
            "SELECT policy_id FROM world_sleep_termination_policy_assignment WHERE world_id=?",
            (world,),
        ).fetchone()
        if assignment is None or int(assignment["policy_id"]) != int(row["policy_id"]):
            raise SleepTerminationError("politique de checkpoint desynchronisee", code="policy_mismatch")
        policy = self.world_policy(world)
        elapsed_exact = (parse_iso(at) - parse_iso(row["started_at"])).total_seconds()
        if elapsed_exact < 0:
            raise SleepTerminationError("duree de checkpoint invalide", code="invalid_checkpoint")
        elapsed = int(elapsed_exact)
        evaluation = evaluate_sleep_checkpoint(
            policy,
            elapsed_seconds=elapsed,
            wake_viability_milli=wake_viability_milli,
            previous_band=row["previous_band"],
            external_wake_accessible=False,
        )
        if not evaluation.completion_eligible:
            raise SleepTerminationError("completion non autorisee", code="completion_not_authorized")

        evidence = {
            "schema_version": 1,
            "reason_code": evaluation.reason_code,
            "wake_viability_milli": _integer(
                wake_viability_milli, field="viabilite de reveil", minimum=0, maximum=100_000
            ),
            "previous_band": row["previous_band"],
            "elapsed_seconds": elapsed,
            "external_wake_accessible": False,
        }
        if _projection is not None:
            if _projection.world_id != world or _projection.character_key != character \
                    or _projection.canonical_at != at:
                raise SleepTerminationError(
                    "projection de viabilite hors provenance", code="invalid_wake_provenance"
                )
            evidence.update({
                "model_key": _projection.model_key,
                "model_version": _projection.model_version,
                "provenance": _projection.provenance,
                "input_fingerprint": _projection.input_fingerprint,
            })
        wire = _json(evidence, field="preuve d'autorisation")
        existing = self._conn.execute(
            "SELECT id,checkpoint_id,activity_id,boundary_at,evaluation_json,consumed_event_id "
            "FROM sleep_completion_authorization WHERE checkpoint_id=? AND boundary_at=?",
            (row["checkpoint_id"], at),
        ).fetchone()
        if existing is not None:
            if existing["evaluation_json"] != wire:
                raise SleepTerminationError("autorisation conflictuelle", code="authorization_conflict")
            return self._authorization(existing)

        now = self._clock.now_iso()
        with transaction(self._conn) as conn:
            conn.execute(
                "INSERT INTO sleep_completion_authorization "
                "(public_id,world_id,character_id,activity_id,checkpoint_id,policy_id,boundary_at,"
                "evaluation_json,authorized_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    new_uuid(), world, int(row["character_id"]), int(row["activity_id"]),
                    int(row["checkpoint_id"]), int(row["policy_id"]), at, wire, now,
                ),
            )
        created = self._conn.execute(
            "SELECT id,checkpoint_id,activity_id,boundary_at,evaluation_json,consumed_event_id "
            "FROM sleep_completion_authorization WHERE checkpoint_id=? AND boundary_at=?",
            (row["checkpoint_id"], at),
        ).fetchone()
        if created is None:
            raise SleepTerminationError("autorisation non persistée", code="authorization_missing")
        return self._authorization(created)

    def authorize_completion_owner_backed(
        self,
        world_id: Any,
        character_key: Any,
        *,
        at_time: Any,
    ) -> SleepCompletionAuthorization:
        """Raccord V1 : seule une projection physiologique owner-backed est admise."""
        try:
            projection = SleepPhysiologyService(self._conn, clock=self._clock).project_wake_viability_owner_backed(
                world_id, character_key, at_time=at_time
            )
        except Exception as exc:
            if isinstance(exc, SleepTerminationError):
                raise
            raise SleepTerminationError(
                str(exc), code=getattr(exc, "code", "invalid_wake_provenance")
            ) from exc
        return self.authorize_completion(
            world_id,
            character_key,
            at_time=projection.canonical_at,
            wake_viability_milli=projection.value_milli,
            external_wake_accessible=False,
            _projection=projection,
        )
