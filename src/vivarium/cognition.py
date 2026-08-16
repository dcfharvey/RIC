"""Frontière locale entre un LLM et le Vivarium.

Le modèle reçoit seulement un contexte déjà autorisé. Sa réponse est une
proposition structurée : elle ne touche jamais SQLite et repasse par le
contrat d'action canonique.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .action_contract import ActionOrchestrator, IntentProposal, ValidationResult
from .action_options import ActionOptionService
from .affect import AffectService
from .attention import AttentionService
from .beliefs import BeliefService
from .decision import DecisionFrameService
from .character import CharacterEngine
from .instances import CharacterInstanceService, InstanceError
from .perception import PerceptionService
from .personality import PersonalityService
from .registry import KEY_RE as _KEY_RE
from .resources import ResourceEngine
from .social import SocialService
from .subjective_memory import SubjectiveMemoryService
from .util import Clock
from .values import ValuesService


COGNITION_SCHEMA_VERSION = 8
DEFAULT_LM_STUDIO_BASE_URL = "http://127.0.0.1:1234"
DEFAULT_TIMEOUT_SECONDS = 45.0
MAX_DIRECT_EVENTS, MAX_MEMORIES, MAX_ATTENTION, MAX_BELIEFS, MAX_EMOTIONS, MAX_RELATIONSHIPS, MAX_BOUNDARIES = 10, 10, 8, 10, 6, 8, 8


class CognitionError(ValueError):
    """Erreur de contrat ou de transport cognitif, sans écriture implicite."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _key(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise CognitionError(f"{label} invalide", code="invalid_cognition_request")
    return value


def _world_id(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise CognitionError("monde invalide", code="invalid_cognition_request")
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _freeze(value: Any) -> Any:
    """Empêche un fournisseur Python de modifier son contexte après lecture."""
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_freeze(item) for item in value)
    return value


def _fact_wire(source_kind: str, priority_milli: int | None, fact: Any) -> Mapping[str, Any]:
    return _freeze({
        "source_kind": source_kind, "priority_milli": priority_milli,
        "event_seq": fact.event_seq, "fact_type": fact.event_type,
        "occurred_at": fact.occurred_at, "payload": _plain(fact.payload),
    })


def _autobiographical_retrieval_context(attention: Any, feed: Any) -> Mapping[str, Any]:
    """Construit des cues depuis les seules perceptions déjà accessibles."""
    cues: list[str] = []
    for item in attention.selected:
        if isinstance(item.fact.event_type, str):
            cues.append(item.fact.event_type)
    for item in feed.candidates[:MAX_DIRECT_EVENTS]:
        if isinstance(item.fact.event_type, str):
            cues.append(item.fact.event_type)
    return {"cues": tuple(dict.fromkeys(cues))}


def _dotenv_values() -> dict[str, str]:
    """Lit le petit fichier ``config/.env`` sans dépendance externe.

    Les variables déjà exportées gardent toujours priorité. Le format reste
    volontairement simple : ``NOM=valeur``, commentaires et guillemets simples
    ou doubles autour d'une valeur.
    """
    config_dir = Path(os.environ.get("VIVARIUM_CONFIG_DIR", "config"))
    path = config_dir / ".env"
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        name, value = name.strip(), value.strip()
        if name.startswith("VIVARIUM_") and name:
            values[name] = value[1:-1] if len(value) >= 2 and value[:1] == value[-1:] and value[:1] in {"'", '"'} else value
    return values


@dataclass(frozen=True)
class LocalLLMSettings:
    """Configuration du serveur local, sans chargement de poids ni secret."""

    base_url: str
    model_id: str
    api_token: str | None
    timeout_seconds: float

    @classmethod
    def from_environment(cls, *, require_model: bool = True) -> "LocalLLMSettings":
        dotenv = _dotenv_values()
        value = lambda name, default="": os.environ.get(name, dotenv.get(name, default))
        raw = value("VIVARIUM_LLM_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
        try:
            timeout = float(raw)
        except ValueError as exc:
            raise CognitionError("délai LLM invalide", code="invalid_llm_configuration") from exc
        return cls(
            value("VIVARIUM_LLM_BASE_URL", DEFAULT_LM_STUDIO_BASE_URL),
            value("VIVARIUM_LLM_MODEL").strip(),
            value("VIVARIUM_LLM_API_TOKEN") or None,
            timeout,
        ).validated(require_model=require_model)

    def validated(self, *, require_model: bool = True) -> "LocalLLMSettings":
        parsed = urlparse(self.base_url)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise CognitionError("le serveur LLM doit être local", code="unsafe_llm_endpoint")
        if parsed.params or parsed.query or parsed.fragment or parsed.path not in {"", "/", "/v1", "/v1/"}:
            raise CognitionError("URL LLM locale invalide", code="invalid_llm_configuration")
        if require_model and not self.model_id:
            raise CognitionError("modèle LLM non configuré", code="missing_llm_model")
        if not isinstance(self.timeout_seconds, (int, float)) or not 1 <= self.timeout_seconds <= 300:
            raise CognitionError("délai LLM hors limites", code="invalid_llm_configuration")
        return self

    @property
    def api_root(self) -> str:
        """Origine locale; accepte aussi l'ancienne valeur ``.../v1``."""
        parsed = urlparse(self.base_url)
        return f"{parsed.scheme}://{parsed.netloc}"


@dataclass
class CognitionProviderTrace:
    """Trace technique d'un appel provider, sans effet sur la décision.

    Le contenu est volontairement séparé de ``CognitionDecision`` : le texte
    brut reçu du provider ne devient jamais une croyance ni un fait canonique.
    ``request_body`` est limité au corps effectivement envoyé; les secrets
    d'authentification restent hors de la trace.
    """

    model_id: str | None = None
    request_body: dict[str, Any] | None = None
    raw_response_body: str | None = None
    raw_message: str | None = None
    parsed_response: Any = None
    status: str = "started"
    error_code: str | None = None
    duration_ms: int | None = None
    _started_monotonic: float | None = None

    def start(self) -> None:
        self._started_monotonic = time.perf_counter()

    def finish(self, *, status: str, error_code: str | None = None) -> None:
        self.status = status
        self.error_code = error_code
        if self._started_monotonic is not None:
            self.duration_ms = max(0, round((time.perf_counter() - self._started_monotonic) * 1000))

    def wire(self) -> dict[str, Any]:
        parameters = {}
        if isinstance(self.request_body, Mapping):
            parameters = {
                key: value for key, value in self.request_body.items()
                if key not in {"model", "system_prompt", "input"}
            }
        return {
            "available": True,
            "model_id": self.model_id,
            "generation_parameters": parameters,
            "request_body": self.request_body,
            "raw_response_body": self.raw_response_body,
            "raw_message": self.raw_message,
            "parsed_response": self.parsed_response,
            "status": self.status,
            "error_code": self.error_code,
            "duration_ms": self.duration_ms,
        }


@dataclass(frozen=True)
class CognitionContext:
    """Entrée non canonique, bornée et sérialisable d'un tour LLM."""

    world_id: int
    character_key: str
    character_name: str
    observed_at: str
    latest_event_seq: int
    attention: tuple[Mapping[str, Any], ...]
    direct_events: tuple[Mapping[str, Any], ...]
    memories: tuple[Mapping[str, Any], ...]
    autobiographical_memories: tuple[Mapping[str, Any], ...]
    beliefs: tuple[Mapping[str, Any], ...]
    mood: Mapping[str, Any] | None
    emotions: tuple[Mapping[str, Any], ...]
    relationships: tuple[Mapping[str, Any], ...]
    boundaries: tuple[Mapping[str, Any], ...]
    decision_frame: Mapping[str, Any]
    allowed_traversals: tuple[Mapping[str, str], ...]
    allowed_activities: tuple[Mapping[str, Any], ...]
    self_profile: Mapping[str, Any]
    decision_cue: Mapping[str, Any]
    schema_version: int = COGNITION_SCHEMA_VERSION

    def wire(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "character": {"key": self.character_key, "name": self.character_name},
            "observed_at": self.observed_at, "latest_event_seq": self.latest_event_seq,
            "attention": _plain(self.attention), "direct_events": _plain(self.direct_events),
            "memories": _plain(self.memories),
            "autobiographical_memories": _plain(self.autobiographical_memories),
            "beliefs": _plain(self.beliefs),
            "mood": _plain(self.mood), "emotions": _plain(self.emotions),
            "relationships": _plain(self.relationships), "boundaries": _plain(self.boundaries),
            "decision_frame": _plain(self.decision_frame),
            "allowed_traversals": _plain(self.allowed_traversals),
            "allowed_activities": _plain(self.allowed_activities),
            "self_profile": _plain(self.self_profile),
            "decision_cue": _plain(self.decision_cue),
        }


class CognitionContextService:
    """Assemble seulement des données accessibles au personnage concerné."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _self_profile(
        self, world_id: int, character_key: str, observed_at: str
    ) -> Mapping[str, Any]:
        """Expose une calibration propre au personnage, jamais celle d'autrui.

        Les textes des composants restent des directions d'expression; ils ne
        constituent pas une règle qui force l'action ni une connaissance partagée.
        """
        try:
            origin = CharacterInstanceService(self._conn, clock=self._clock).origin(
                world_id, character_key
            )
        except InstanceError:
            origin = {"resolved_initial_definition": {}}
        summaries: list[str] = []
        morphology: dict[str, str] = {}
        definition = origin["resolved_initial_definition"]
        components = definition.get("components", []) if isinstance(definition, Mapping) else []
        for component in components:
            if not isinstance(component, Mapping):
                continue
            key = component.get("key")
            config = component.get("config")
            if not isinstance(config, Mapping):
                continue
            if key in {"appearance.descriptive", "personality.initial_dispositions"}:
                summary = config.get("summary")
                if isinstance(summary, str) and summary:
                    summaries.append(summary)
            if key == "body.morphology":
                body_plan = config.get("body_plan")
                if isinstance(body_plan, str) and body_plan:
                    morphology["body_plan"] = body_plan
        personality = PersonalityService(self._conn, clock=self._clock).read(world_id, character_key)
        traits = {} if personality is None else {
            key: value["mean_milli"] for key, value in personality["traits"].items()
        }
        values = ValuesService(self._conn, clock=self._clock).read(world_id, character_key)
        operational_grounding = self._operational_grounding(
            world_id, character_key, observed_at
        )
        if morphology:
            operational_grounding = {
                "morphology": morphology,
                **operational_grounding,
            }
        return _freeze({
            "expression_summaries": tuple(summaries),
            "trait_means_milli": traits,
            "ranked_values": () if values is None else tuple(values["ranked_value_keys"][:5]),
            "preferences": () if values is None else tuple(values["preferences"]),
            "operational_grounding": operational_grounding,
        })

    def _operational_grounding(
        self, world_id: int, character_key: str, observed_at: str
    ) -> Mapping[str, Any]:
        """Project generic owner-backed self-state without engine metadata."""
        capabilities: dict[str, str] = {}
        context_signals: dict[str, int] = {}
        resource_effects = ResourceEngine(self._conn, clock=self._clock).active_effects_for_character(
            world_id, character_key, observed_at
        )
        for resource in resource_effects:
            for effect in resource["effects"]:
                effect_type = effect.get("effect_type")
                effect_key = effect.get("effect_key")
                if not isinstance(effect_key, str):
                    continue
                if effect_type == "capability_availability":
                    availability = effect.get("availability")
                    if isinstance(availability, str):
                        if effect_key in capabilities:
                            raise CognitionError(
                                "effets opérationnels ambigus pour le contexte cognitif",
                                code="ambiguous_operational_grounding",
                            )
                        capabilities[effect_key] = availability
                elif effect_type == "context_signal":
                    value = effect.get("value_milli")
                    if isinstance(value, int) and not isinstance(value, bool):
                        if effect_key in context_signals:
                            raise CognitionError(
                                "effets opérationnels ambigus pour le contexte cognitif",
                                code="ambiguous_operational_grounding",
                            )
                        context_signals[effect_key] = value
        return {
            "capabilities": dict(sorted(capabilities.items())),
            "context_signals": dict(sorted(context_signals.items())),
        }

    def build(
        self,
        world_id: Any,
        character_key: Any,
        *,
        after_event_seq: Any = 0,
        decision_cue: Mapping[str, Any] | None = None,
        exclude_memory_source_social_speech_act_ids: tuple[int, ...] = (),
    ) -> CognitionContext:
        world_id, character_key = _world_id(world_id), _key(character_key, "personnage")
        character = CharacterEngine(self._conn, clock=self._clock).character_sheet(world_id, character_key)
        attention = AttentionService(self._conn, clock=self._clock).snapshot(world_id, character_key, limit=MAX_ATTENTION)
        feed = PerceptionService(self._conn, clock=self._clock).events_since(world_id, character_key, after_event_seq)
        memory_service = SubjectiveMemoryService(self._conn, clock=self._clock)
        memories = memory_service.recall_recent_cognitive(
            world_id,
            character_key,
            limit=MAX_MEMORIES,
            exclude_source_social_speech_act_ids=exclude_memory_source_social_speech_act_ids,
        )
        autobiographical_memories = memory_service.recall_autobiographical(
            world_id,
            character_key,
            context=_autobiographical_retrieval_context(attention, feed),
            limit=MAX_MEMORIES,
        )
        beliefs = BeliefService(self._conn, clock=self._clock).list(world_id, character_key, limit=MAX_BELIEFS)
        affect = AffectService(self._conn, clock=self._clock)
        mood = affect.mood(world_id, character_key)
        emotions = affect.active_episodes(world_id, character_key, limit=MAX_EMOTIONS)
        social = SocialService(self._conn, clock=self._clock)
        relationships = social.relationships(world_id, character_key, limit=MAX_RELATIONSHIPS)
        boundaries = social.active_boundaries(world_id, character_key, limit=MAX_BOUNDARIES)
        decision_frame = DecisionFrameService(self._conn).build_current(world_id, character_key).wire()
        visible_traversals: list[Mapping[str, str]] = []
        for item in attention.available:
            if item.source_kind != "perception:adjacent_connector":
                continue
            payload = item.fact.payload
            candidate = _freeze({"connector_key": payload["connector"], "target_location_key": payload["destination"]})
            if candidate not in visible_traversals:
                visible_traversals.append(candidate)
        options = ActionOptionService(self._conn, clock=self._clock).visible_traversals(
            world_id, character_key, (_plain(item) for item in visible_traversals)
        )
        allowed = tuple(_freeze({
            "connector_key": option.connector_key,
            "target_location_key": option.target_location_key,
        }) for option in options)
        cue = {} if decision_cue is None else _freeze(_plain(decision_cue))
        activity_options = ()
        if cue.get("trigger") == "planned_reflection":
            activity_options = tuple(
                _freeze(option.wire())
                for option in ActionOptionService(self._conn, clock=self._clock).available_activities(
                    world_id, character_key
                )
            )
        return CognitionContext(
            world_id, character_key, character["name"], attention.observed_at, feed.latest_seq,
            tuple(_fact_wire(item.source_kind, item.priority_milli, item.fact) for item in attention.selected),
            tuple(_fact_wire(item.access_kind, None, item.fact) for item in feed.candidates[:MAX_DIRECT_EVENTS]),
            tuple(_freeze(_plain(memory)) for memory in memories),
            tuple(_freeze(_plain(memory)) for memory in autobiographical_memories),
            tuple(_freeze(_plain(belief)) for belief in beliefs),
            None if mood is None else _freeze(_plain(mood)),
            tuple(_freeze(_plain(emotion)) for emotion in emotions),
            tuple(_freeze(_plain(relationship)) for relationship in relationships),
            tuple(_freeze(_plain(boundary)) for boundary in boundaries), _freeze(decision_frame), tuple(allowed),
            activity_options, self._self_profile(world_id, character_key, attention.observed_at), cue,
        )


@dataclass(frozen=True)
class CognitionDecision:
    """Sortie minimale du LLM, avant validation canonique."""

    action: str  # no_action | traverse | start_activity
    connector_key: str | None = None
    target_location_key: str | None = None
    activity_type: str | None = None
    schema_version: int = COGNITION_SCHEMA_VERSION

    @classmethod
    def parse(cls, value: Any) -> "CognitionDecision":
        allowed_fields = {
            "schema_version", "action", "connector_key", "target_location_key", "activity_type"
        }
        if not isinstance(value, Mapping) or set(value) - allowed_fields:
            raise CognitionError("réponse LLM hors contrat", code="invalid_llm_response")
        if value.get("schema_version") != COGNITION_SCHEMA_VERSION:
            raise CognitionError("version de réponse LLM incompatible", code="invalid_llm_response")
        if value.get("action") == "no_action" and set(value) == {"schema_version", "action"}:
            return cls("no_action")
        if value.get("action") == "traverse" and set(value) == allowed_fields - {"activity_type"}:
            return cls("traverse", _key(value["connector_key"], "connecteur"), _key(value["target_location_key"], "destination"))
        if value.get("action") == "start_activity" and set(value) == allowed_fields - {"connector_key"}:
            return cls(
                "start_activity", None, _key(value["target_location_key"], "destination"),
                _key(value["activity_type"], "activité"),
            )
        raise CognitionError("réponse LLM hors contrat", code="invalid_llm_response")

    def validated(self) -> "CognitionDecision":
        """Valide aussi une décision fournie par un adaptateur Python."""
        if self.action == "no_action":
            wire = {"schema_version": self.schema_version, "action": self.action}
        elif self.action == "traverse":
            wire = {
                "schema_version": self.schema_version, "action": self.action,
                "connector_key": self.connector_key, "target_location_key": self.target_location_key,
            }
        else:
            wire = {
                "schema_version": self.schema_version, "action": self.action,
                "activity_type": self.activity_type,
                "target_location_key": self.target_location_key,
            }
        return self.parse(wire)


class CognitionProvider(Protocol):
    def decide(self, context: CognitionContext) -> CognitionDecision: ...


def request_local_model(
    settings: LocalLLMSettings, *, system_prompt: str, input_text: str,
    trace: CognitionProviderTrace | None = None,
) -> str:
    """Exécute une requête native locale et retourne son unique message.

    Les tâches cognitives possèdent des schémas distincts, mais elles doivent
    partager cette frontière réseau : loopback seulement, raisonnement coupé,
    aucune limite de génération imposée par le Vivarium et aucune conservation
    par le fournisseur.
    """
    settings = settings.validated(require_model=False)
    if not settings.model_id:
        raise CognitionError("modèle LLM non configuré", code="missing_llm_model")
    body = {
        "model": settings.model_id,
        "system_prompt": system_prompt,
        "input": input_text,
        "temperature": 0.2,
        "store": False,
    }
    reasoning = _reasoning_parameter(settings)
    if reasoning is not None:
        body["reasoning"] = reasoning
    if trace is not None:
        trace.request_body = dict(body)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if settings.api_token:
        headers["Authorization"] = f"Bearer {settings.api_token}"
    request = Request(
        settings.api_root + "/api/v1/chat",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.timeout_seconds) as response:  # endpoint validated loopback
            raw = response.read().decode("utf-8")
            if trace is not None:
                trace.raw_response_body = raw
    except HTTPError as exc:
        raise CognitionError(f"LM Studio a refusé la requête HTTP {exc.code}", code="llm_http_error") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise CognitionError("LM Studio est inaccessible", code="llm_unavailable") from exc
    try:
        output = json.loads(raw)["output"]
        messages = [item["content"] for item in output if item.get("type") == "message"]
        if len(messages) != 1 or not isinstance(messages[0], str):
            raise TypeError("message absent ou ambigu")
        return messages[0]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise CognitionError("réponse LM Studio illisible", code="invalid_llm_response") from exc


def _reasoning_parameter(settings: LocalLLMSettings) -> str | None:
    """Negotiate reasoning without silently enabling a configurable mode."""
    request = Request(settings.api_root + "/api/v1/models", headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=settings.timeout_seconds) as response:  # endpoint validated loopback
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raise CognitionError(f"LM Studio refused HTTP request {exc.code}", code="llm_http_error") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise CognitionError("LM Studio is inaccessible", code="llm_unavailable") from exc
    try:
        records = json.loads(raw)["models"]
        record = next(
            (item for item in records if isinstance(item, Mapping) and item.get("key") == settings.model_id),
            None,
        )
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise CognitionError("LM Studio response is unreadable", code="invalid_llm_response") from exc
    capabilities = record.get("capabilities") if isinstance(record, Mapping) else None
    reasoning = capabilities.get("reasoning") if isinstance(capabilities, Mapping) else None
    if not isinstance(reasoning, Mapping):
        return None
    allowed_options = reasoning.get("allowed_options")
    if isinstance(allowed_options, (list, tuple)) and "off" in allowed_options:
        return "off"
    raise CognitionError(
        "model does not authorize reasoning=off under the local recipe",
        code="reasoning_not_supported",
    )


class LMStudioProvider:
    """Client de l'API native LM Studio, avec raisonnement explicitement coupé.

    L'API native expose ``reasoning: off`` pour les modèles Gemma. La forme de
    sortie est renforcée dans le prompt puis refusée par ``CognitionDecision``
    si elle ne respecte pas exactement le contrat local.
    """

    def __init__(self, settings: LocalLLMSettings) -> None:
        self._settings = settings.validated(require_model=False)
        self._last_call: CognitionProviderTrace | None = None

    @property
    def last_call(self) -> CognitionProviderTrace | None:
        """Dernière trace provider, lue immédiatement par le routeur."""
        return self._last_call

    @staticmethod
    def _prompt(context: CognitionContext) -> str:
        valid_actions: list[dict[str, Any]] = [
            {"schema_version": COGNITION_SCHEMA_VERSION, "action": "no_action"}
        ]
        valid_actions.extend({
            "schema_version": COGNITION_SCHEMA_VERSION,
            "action": "traverse",
            "connector_key": item["connector_key"],
            "target_location_key": item["target_location_key"],
        } for item in context.allowed_traversals)
        valid_actions.extend({
            "schema_version": COGNITION_SCHEMA_VERSION,
            "action": "start_activity",
            "activity_type": item["activity_type"],
            "target_location_key": item["target_location_key"],
        } for item in context.allowed_activities)
        arrival_note = ""
        if context.decision_cue.get("trigger") == "initial_arrival":
            arrival_note = (
                "Les initial_shared_facts sont des faits communs établis : une résidente arrivée "
                "volontairement peut normalement entrer, mais peut aussi attendre si son contexte le justifie. "
            )
        return (
            "Tu es un composant de décision du Vivarium. Tu ne connais que le JSON fourni. "
            "decision_cue décrit la raison technique d'une unique occasion de décider; ce n'est jamais un ordre. "
            + arrival_note
            + "Les seules réponses valides sont énumérées dans valid_actions. Copie exactement un de ces objets; "
            "n'en combine pas les champs, n'invente ni clé ni destination, et n'ajoute aucun texte ou Markdown.\n"
            + "valid_actions=" + json.dumps(valid_actions, ensure_ascii=False, separators=(",", ":")) + "\n\n"
            + json.dumps(context.wire(), ensure_ascii=False, separators=(",", ":"))
        )

    def decide(self, context: CognitionContext) -> CognitionDecision:
        trace = CognitionProviderTrace(model_id=self._settings.model_id)
        trace.start()
        self._last_call = trace
        try:
            raw_message = request_local_model(
                self._settings,
                system_prompt="Tu proposes une seule action structurée, jamais un fait du monde.",
                input_text=self._prompt(context),
                trace=trace,
            )
            trace.raw_message = raw_message
            payload = json.loads(raw_message)
            trace.parsed_response = payload
        except json.JSONDecodeError as exc:
            trace.finish(status="error", error_code="invalid_llm_response")
            raise CognitionError("réponse LM Studio illisible", code="invalid_llm_response") from exc
        except CognitionError as exc:
            trace.finish(status="error", error_code=exc.code)
            raise
        # Adaptation syntaxique étroite, identique dans son principe à celle
        # des actes de scène : Gemma emploie parfois directement le type
        # d'activité comme verbe d'action. La paire doit déjà être une option
        # exacte du moteur; aucune destination ni activité n'est inférée.
        if (
            isinstance(payload, Mapping)
            and set(payload) == {"schema_version", "action", "target_location_key"}
            and any(
                payload.get("action") == item["activity_type"]
                and payload.get("target_location_key") == item["target_location_key"]
                for item in context.allowed_activities
            )
        ):
            payload = {
                "schema_version": payload["schema_version"],
                "action": "start_activity",
                "activity_type": payload["action"],
                "target_location_key": payload["target_location_key"],
            }
        try:
            decision = CognitionDecision.parse(payload)
        except CognitionError as exc:
            trace.finish(status="error", error_code=exc.code)
            raise
        trace.finish(status="completed")
        return decision

    def list_models(self) -> tuple[str, ...]:
        """Diagnostic en lecture seule des identifiants chargés par LM Studio."""
        return tuple(record["key"] for record in self.list_model_records())

    def list_model_records(self) -> tuple[dict[str, Any], ...]:
        """Retourne les enregistrements locaux disponibles sans secrets ni inférence."""
        request = Request(self._settings.api_root + "/api/v1/models", headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=self._settings.timeout_seconds) as response:  # endpoint validated loopback
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            raise CognitionError(f"LM Studio a refusé la requête HTTP {exc.code}", code="llm_http_error") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise CognitionError("LM Studio est inaccessible", code="llm_unavailable") from exc
        try:
            data = json.loads(raw)["models"]
            records = tuple(dict(item) for item in data if isinstance(item, Mapping) and isinstance(item.get("key"), str))
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise CognitionError("réponse LM Studio illisible", code="invalid_llm_response") from exc
        return records


@dataclass(frozen=True)
class CognitionTurnResult:
    context: CognitionContext
    decision: CognitionDecision
    validation: ValidationResult | None


class CognitionTurnService:
    """Prépare un tour, appelle un fournisseur et route une action autorisée."""

    def __init__(self, conn: sqlite3.Connection, provider: CognitionProvider, clock: Clock | None = None) -> None:
        self._conn, self._provider, self._clock = conn, provider, clock or Clock()
        self.last_context: CognitionContext | None = None
        self.last_provider_trace: Any = None
        self.provider_call_attempted = False

    def run(
        self,
        world_id: Any,
        character_key: Any,
        proposal_id: Any,
        *,
        after_event_seq: Any = 0,
        decision_cue: Mapping[str, Any] | None = None,
    ) -> CognitionTurnResult:
        proposal_id = _key(proposal_id, "identifiant de proposition")
        context = CognitionContextService(self._conn, clock=self._clock).build(
            world_id, character_key, after_event_seq=after_event_seq, decision_cue=decision_cue
        )
        self.last_context = context
        self.provider_call_attempted = True
        try:
            decision = self._provider.decide(context)
        finally:
            self.last_provider_trace = getattr(self._provider, "last_call", None)
        if not isinstance(decision, CognitionDecision):
            raise CognitionError("fournisseur cognitif hors contrat", code="invalid_llm_response")
        decision = decision.validated()
        if decision.action == "no_action":
            return CognitionTurnResult(context, decision, None)
        assert decision.target_location_key is not None
        if decision.action == "traverse":
            assert decision.connector_key is not None
            allowed = {(item["connector_key"], item["target_location_key"]) for item in context.allowed_traversals}
            if (decision.connector_key, decision.target_location_key) not in allowed:
                raise CognitionError("traversée LLM non perceptible", code="llm_action_not_perceived")
            proposal = IntentProposal.traverse(
                proposal_id, context.character_key, decision.connector_key, decision.target_location_key
            )
        else:
            assert decision.activity_type is not None
            allowed = {(item["activity_type"], item["target_location_key"]) for item in context.allowed_activities}
            if (decision.activity_type, decision.target_location_key) not in allowed:
                raise CognitionError("activité LLM non disponible", code="llm_action_not_available")
            proposal = IntentProposal.start_activity(
                proposal_id, context.character_key, decision.activity_type, decision.target_location_key
            )
        validation = ActionOrchestrator(self._conn, clock=self._clock).execute(
            context.world_id,
            proposal,
            effective_at=context.observed_at,
            expected_event_seq=context.latest_event_seq,
        )
        return CognitionTurnResult(context, decision, validation)
