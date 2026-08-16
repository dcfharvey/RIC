"""Tour de parole LLM borné dans une scène sociale active.

Le texte reste une expression enregistrée. Il n'est jamais promu en fait,
croyance, permission, relation ou consentement par cette couche. Ces effets
exigent leurs contrats causaux propres.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Protocol

from .cognition import (
    CognitionContext,
    CognitionContextService,
    CognitionError,
    LocalLLMSettings,
    request_local_model,
)
from .cognition_call_ledger import CognitionCallAdmission, CognitionCallLedgerService
from .cognitive_flow import CognitiveFlowRequest, CognitiveFlowScheduler, CognitiveFlowTelemetry, flow_failure_state
from .cognition_policy import CALL_TRIGGER_SCENE_TURN, CognitionCallLimits
from .diagnostics import DiagnosticRecorder
from .registry import KEY_RE as _KEY_RE
from .scenes import SceneError, SocialSceneService
from .subjective_memory import SubjectiveMemoryService
from .util import Clock


SCENE_TURN_SCHEMA_VERSION = 2
MAX_SCENE_TURN_CONTENT = 320
MAX_SCENE_CONTEXT_ACTS = 8
_ACT_KINDS = frozenset({
    "greet", "ask", "answer", "inform", "offer", "decline", "apologize", "acknowledge", "leave",
})


class SceneTurnError(ValueError):
    """Entrée, contexte ou sortie hors du contrat de parole."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _key(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise SceneTurnError(f"{label} invalide", code="invalid_scene_turn")
    return value


def _world_id(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise SceneTurnError("monde invalide", code="invalid_scene_turn")
    return value


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_freeze(item) for item in value)
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _internal_source_ids(context: "SceneTurnContext") -> dict[str, list[int]]:
    return {
        "recent_act_source_social_speech_act_ids": [
            item["source_social_speech_act_id"]
            for item in context.recent_acts
            if isinstance(item.get("source_social_speech_act_id"), int)
        ],
        "subjective_memory_source_social_speech_act_ids": [
            item["source_social_speech_act_id"]
            for item in context.subjective_context.memories
            if isinstance(item.get("source_social_speech_act_id"), int)
        ],
    }


@dataclass(frozen=True)
class SceneTurnContext:
    """Contexte privé du personnage, enrichi du seul cadre de sa scène."""

    world_id: int
    scene_key: str
    speaker_key: str
    participants: tuple[Mapping[str, str], ...]
    recent_acts: tuple[Mapping[str, Any], ...]
    subjective_context: CognitionContext
    schema_version: int = SCENE_TURN_SCHEMA_VERSION
    deduplicated_memory_source_ids: tuple[int, ...] = ()

    def wire(self) -> dict[str, Any]:
        subjective = self.subjective_context.wire()
        subjective["memories"] = [
            {
                key: value for key, value in memory.items()
                if key != "source_social_speech_act_id"
            }
            for memory in subjective["memories"]
        ]
        return {
            "schema_version": self.schema_version,
            "scene": {
                "key": self.scene_key,
                "speaker_key": self.speaker_key,
                "participants": _plain(self.participants),
                "recent_acts": [
                    {
                        key: _plain(value) for key, value in act.items()
                        if key != "source_social_speech_act_id"
                    }
                    for act in self.recent_acts
                ],
            },
            "allowed_act_kinds": sorted(_ACT_KINDS),
            "max_content_chars": MAX_SCENE_TURN_CONTENT,
            "subjective_context": subjective,
        }


class SceneTurnContextService:
    """Joint un cadre de scène réel au contexte subjectif déjà filtré."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn, self._clock = conn, clock or Clock()

    def build(self, world_id: Any, scene_key: Any, speaker_key: Any) -> SceneTurnContext:
        world_id, scene_key, speaker_key = (
            _world_id(world_id), _key(scene_key, "scène"), _key(speaker_key, "locutrice")
        )
        try:
            scene = SocialSceneService(self._conn, clock=self._clock).turn_context(
                world_id, scene_key, speaker_key, recent_limit=MAX_SCENE_CONTEXT_ACTS
            )
        except SceneError as exc:
            raise SceneTurnError(str(exc), code=exc.code) from exc
        recent_acts = tuple(_freeze(item) for item in scene["recent_acts"])
        source_ids = frozenset(
            item.get("source_social_speech_act_id")
            for item in recent_acts
            if isinstance(item.get("source_social_speech_act_id"), int)
        )
        audit_memories = SubjectiveMemoryService(self._conn, clock=self._clock).recall_recent(
            world_id, speaker_key,
        )
        duplicate_ids = tuple(sorted(
            source_id for source_id in source_ids
            if any(memory.get("source_social_speech_act_id") == source_id for memory in audit_memories)
        ))
        subjective = CognitionContextService(self._conn, clock=self._clock).build(
            world_id,
            speaker_key,
            exclude_memory_source_social_speech_act_ids=duplicate_ids,
        )
        return SceneTurnContext(
            world_id,
            scene_key,
            speaker_key,
            tuple(_freeze(item) for item in scene["participants"]),
            recent_acts,
            subjective,
            deduplicated_memory_source_ids=duplicate_ids,
        )


@dataclass(frozen=True)
class SceneTurnDecision:
    """Une absence de parole ou un unique acte de parole, rien de plus."""

    action: str  # no_action | speak
    act_kind: str | None = None
    content: str | None = None
    recipient_key: str | None = None
    schema_version: int = SCENE_TURN_SCHEMA_VERSION

    @classmethod
    def parse(cls, value: Any) -> "SceneTurnDecision":
        no_action = {"schema_version", "action"}
        speak = {"schema_version", "action", "act_kind", "content", "recipient_key"}
        if not isinstance(value, Mapping) or set(value) not in (no_action, speak):
            raise SceneTurnError("réponse de scène hors contrat", code="invalid_scene_turn_response")
        if value.get("schema_version") != SCENE_TURN_SCHEMA_VERSION:
            raise SceneTurnError("version de tour de scène incompatible", code="invalid_scene_turn_response")
        if value.get("action") == "no_action" and set(value) == no_action:
            return cls("no_action")
        if value.get("action") != "speak" or set(value) != speak or value.get("act_kind") not in _ACT_KINDS:
            raise SceneTurnError("acte de scène inconnu", code="invalid_scene_turn_response")
        content = value.get("content")
        if not isinstance(content, str) or not 1 <= len(content) <= MAX_SCENE_TURN_CONTENT:
            raise SceneTurnError("contenu de scène invalide", code="invalid_scene_turn_response")
        recipient = value.get("recipient_key")
        if recipient is not None:
            recipient = _key(recipient, "destinataire")
        return cls("speak", value["act_kind"], content, recipient)

    def validated(self) -> "SceneTurnDecision":
        if self.action == "no_action":
            wire = {"schema_version": self.schema_version, "action": self.action}
        else:
            wire = {
                "schema_version": self.schema_version,
                "action": self.action,
                "act_kind": self.act_kind,
                "content": self.content,
                "recipient_key": self.recipient_key,
            }
        return self.parse(wire)


class SceneTurnProvider(Protocol):
    def decide(self, context: SceneTurnContext) -> SceneTurnDecision: ...


class LMStudioSceneTurnProvider:
    """Adaptateur local dédié au schéma d'un unique tour social."""

    def __init__(self, settings: LocalLLMSettings, diagnostics: DiagnosticRecorder | None = None) -> None:
        self._settings = settings.validated(require_model=False)
        self._diagnostics = diagnostics
        self.last_diagnostic_id: str | None = None

    @staticmethod
    def _parse_model_response(raw: str) -> SceneTurnDecision:
        """Adapte une seule variation connue de Gemma avant le contrat strict.

        Certains modèles locaux renvoient ``action: "greet"`` tout en donnant
        déjà ``act_kind: "greet"`` et tous les champs imposés. C'est une
        proposition sans ambiguïté, mais pas la forme de transport retenue par
        le moteur. L'adaptateur corrige uniquement cette redondance; toute
        autre forme reste refusée par ``SceneTurnDecision.parse``.
        """
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CognitionError("réponse LM Studio illisible", code="invalid_scene_turn_response") from exc
        if (
            isinstance(payload, Mapping)
            and payload.get("action") in _ACT_KINDS
            and payload.get("act_kind") == payload.get("action")
            and set(payload) == {"schema_version", "action", "act_kind", "content", "recipient_key"}
        ):
            payload = dict(payload)
            payload["action"] = "speak"
        return SceneTurnDecision.parse(payload)

    @staticmethod
    def _prompt(context: SceneTurnContext) -> str:
        return (
            "Tu es un composant de dialogue du Vivarium. Utilise uniquement le JSON fourni. "
            "Tu peux soit attendre, soit produire UNE parole brève dans la scène. "
            "Le texte est une expression, jamais un fait prouvé, un consentement, une relation ou une permission. "
            "N'invente ni participante, ni objet, ni événement. Réponds UNIQUEMENT en JSON, sans Markdown : "
            f'{{"schema_version":{SCENE_TURN_SCHEMA_VERSION},"action":"no_action"}} OU '
            f'{{"schema_version":{SCENE_TURN_SCHEMA_VERSION},"action":"speak","act_kind":"une clé de allowed_act_kinds","content":"1 à {MAX_SCENE_TURN_CONTENT} caractères","recipient_key":"une participante ou null"}}.\n\n'
            + json.dumps(context.wire(), ensure_ascii=False, separators=(",", ":"))
        )

    def decide(self, context: SceneTurnContext) -> SceneTurnDecision:
        raw: str | None = None
        prompt_text = self._prompt(context)
        payload = {"model_id": self._settings.model_id, "provider_version": "scene-turn-v2",
                   "context_wire": context.wire(), "prompt_text": prompt_text,
                   "deduplicated_memory_source_ids": list(context.deduplicated_memory_source_ids),
                   "scene_key": context.scene_key, "speaker_key": context.speaker_key}
        payload.update(_internal_source_ids(context))
        try:
            raw = request_local_model(
                self._settings,
                system_prompt="Tu produis au plus un acte de parole structuré, jamais un fait du monde.",
                input_text=prompt_text,
            )
            decision = self._parse_model_response(raw)
            repeated_ids = []
            if decision.content is not None:
                repeated_ids = sorted({
                    act["source_social_speech_act_id"]
                    for act in context.recent_acts
                    if act.get("content") == decision.content
                    and isinstance(act.get("source_social_speech_act_id"), int)
                })
            payload.update({
                "raw_output": raw,
                "validation": "accepted",
                "validated_output": decision.__dict__,
                "exact_repeat_source_social_speech_act_ids": repeated_ids,
            })
            self.last_diagnostic_id = None if self._diagnostics is None else self._diagnostics.record("scene_turn_provider", payload)
            return decision
        except CognitionError as exc:
            payload.update({"raw_output": raw, "validation": "rejected", "validation_code": exc.code})
            self.last_diagnostic_id = None if self._diagnostics is None else self._diagnostics.record("scene_turn_provider", payload)
            raise
        except SceneTurnError as exc:
            payload.update({"raw_output": raw, "validation": "rejected", "validation_code": exc.code})
            self.last_diagnostic_id = None if self._diagnostics is None else self._diagnostics.record("scene_turn_provider", payload)
            raise CognitionError(str(exc), code="invalid_scene_turn_response") from exc


@dataclass(frozen=True)
class SceneTurnResult:
    """Résultat explicitement distinct de l'admission et de l'expression."""

    context: SceneTurnContext | None
    admission: CognitionCallAdmission | None
    decision: SceneTurnDecision | None
    speech: Mapping[str, Any] | None
    provider_error_code: str | None
    validation_error_code: str | None
    deferred_reason_code: str | None = None
    replayed: bool = False

    @property
    def attempted(self) -> bool:
        return self.admission is not None and self.admission.verdict.eligible


class SceneTurnService:
    """Garde un tour de scène : contexte, admission, LLM puis acte validé."""

    def __init__(
        self, conn: sqlite3.Connection, provider: SceneTurnProvider,
        clock: Clock | None = None, diagnostics: DiagnosticRecorder | None = None,
        flow_scheduler: CognitiveFlowScheduler | None = None,
    ) -> None:
        self._conn, self._provider, self._clock = conn, provider, clock or Clock()
        self._diagnostics = diagnostics
        self._flow_scheduler = flow_scheduler
        self._flow_telemetry = CognitiveFlowTelemetry(conn, clock=self._clock)
        self._ledger = CognitionCallLedgerService(
            conn, clock=self._clock, flow_scheduler=flow_scheduler,
        )
        self._scenes = SocialSceneService(conn, clock=self._clock)

    def run(
        self,
        world_id: Any,
        scene_key: Any,
        speaker_key: Any,
        turn_key: Any,
        limits: Any,
    ) -> SceneTurnResult:
        world_id, scene_key, speaker_key, turn_key = (
            _world_id(world_id), _key(scene_key, "scène"), _key(speaker_key, "locutrice"), _key(turn_key, "tour")
        )
        try:
            existing = self._scenes.existing_act(world_id, scene_key, turn_key)
        except SceneError as exc:
            raise SceneTurnError(str(exc), code=exc.code) from exc
        if existing is not None:
            if existing["speaker_key"] != speaker_key:
                raise SceneTurnError("clé de tour déjà utilisée par une autre locutrice", code="scene_turn_key_conflict")
            return SceneTurnResult(
                None,
                None,
                SceneTurnDecision("speak", existing["act_kind"], existing["content"], existing["recipient_key"]),
                _freeze({key: existing[key] for key in ("act_key", "act_kind", "content", "payload")}),
                None,
                None,
                replayed=True,
            )

        context = SceneTurnContextService(self._conn, clock=self._clock).build(world_id, scene_key, speaker_key)
        try:
            admission = self._ledger.admit(world_id, speaker_key, CALL_TRIGGER_SCENE_TURN, turn_key, limits)
        except ValueError as exc:
            raise SceneTurnError(str(exc), code=getattr(exc, "code", "invalid_scene_turn")) from exc
        if not admission.verdict.eligible:
            return SceneTurnResult(
                context, admission, None, None, None, None, admission.verdict.reason_code
            )

        flow_request = CognitiveFlowRequest(
            world_id, speaker_key, CALL_TRIGGER_SCENE_TURN, turn_key,
            admission.admitted_at or self._clock.now_iso(),
        )
        provider_started = self._clock.now_iso()
        if self._flow_scheduler is not None:
            self._flow_telemetry.record(
                flow_request, "executing", canonical_at=admission.admitted_at,
                provider_started_at=provider_started,
            )
        try:
            decision = self._provider.decide(context)
            if not isinstance(decision, SceneTurnDecision):
                raise SceneTurnError("fournisseur de scène hors contrat", code="invalid_scene_turn_response")
            decision = decision.validated()
        except (CognitionError, SceneTurnError) as exc:
            if self._flow_scheduler is not None:
                self._flow_telemetry.record(
                    flow_request, flow_failure_state(getattr(exc, "code", "invalid_scene_turn_response")), reason_code=getattr(exc, "code", "invalid_scene_turn_response"),
                    canonical_at=admission.admitted_at,
                    provider_started_at=provider_started,
                    provider_finished_at=self._clock.now_iso(),
                )
            self._record_result(scene_key, speaker_key, turn_key, context, None, getattr(self._provider, "last_diagnostic_id", None), getattr(exc, "code", "invalid_scene_turn_response"))
            return SceneTurnResult(
                context, admission, None, None, getattr(exc, "code", "invalid_scene_turn_response"), None
            )
        if decision.action == "no_action":
            if self._flow_scheduler is not None:
                self._flow_telemetry.record(
                    flow_request, "completed", reason_code="no_action",
                    canonical_at=admission.admitted_at,
                    provider_started_at=provider_started,
                    provider_finished_at=self._clock.now_iso(),
                )
            self._record_result(scene_key, speaker_key, turn_key, context, decision, getattr(self._provider, "last_diagnostic_id", None), None)
            return SceneTurnResult(context, admission, decision, None, None, None)

        assert decision.act_kind is not None and decision.content is not None
        participant_keys = {participant["key"] for participant in context.participants}
        if decision.recipient_key == speaker_key or (
            decision.recipient_key is not None and decision.recipient_key not in participant_keys
        ):
            if self._flow_scheduler is not None:
                self._flow_telemetry.record(
                    flow_request, "completed", reason_code="scene_recipient_not_in_scene",
                    canonical_at=admission.admitted_at,
                    provider_started_at=provider_started,
                    provider_finished_at=self._clock.now_iso(),
                )
            self._record_result(scene_key, speaker_key, turn_key, context, decision, getattr(self._provider, "last_diagnostic_id", None), "scene_recipient_not_in_scene")
            return SceneTurnResult(context, admission, decision, None, None, "scene_recipient_not_in_scene")
        try:
            speech = self._scenes.speak(
                world_id,
                scene_key,
                turn_key,
                speaker_key,
                act_kind=decision.act_kind,
                content=decision.content,
                recipient_key=decision.recipient_key,
            )
        except SceneError as exc:
            if self._flow_scheduler is not None:
                self._flow_telemetry.record(
                    flow_request, "completed", reason_code=exc.code,
                    canonical_at=admission.admitted_at,
                    provider_started_at=provider_started,
                    provider_finished_at=self._clock.now_iso(),
                )
            self._record_result(scene_key, speaker_key, turn_key, context, decision, getattr(self._provider, "last_diagnostic_id", None), exc.code)
            return SceneTurnResult(context, admission, decision, None, None, exc.code)
        self._record_result(
            scene_key, speaker_key, turn_key, context, decision,
            getattr(self._provider, "last_diagnostic_id", None), None,
            persisted_speech=speech,
        )
        if self._flow_scheduler is not None:
            self._flow_telemetry.record(
                flow_request, "completed",
                canonical_at=admission.admitted_at,
                provider_started_at=provider_started,
                provider_finished_at=self._clock.now_iso(),
            )
        return SceneTurnResult(context, admission, decision, _freeze(speech), None, None)

    def _record_result(self, scene_key: str, speaker_key: str, turn_key: str,
                       context: SceneTurnContext, decision: SceneTurnDecision | None,
                       provider_call_id: str | None, validation_code: str | None,
                       persisted_speech: Mapping[str, Any] | None = None) -> None:
        if self._diagnostics is not None:
            payload = {
                "scene_key": scene_key, "speaker_key": speaker_key, "turn_key": turn_key,
                "provider_call_id": provider_call_id, "context_wire": context.wire(),
                "deduplicated_memory_source_ids": list(context.deduplicated_memory_source_ids),
                "validated_output": None if decision is None else decision.__dict__,
                "persisted_speech": None if persisted_speech is None else dict(persisted_speech),
                "validation": "accepted" if validation_code is None else "rejected",
                "validation_code": validation_code,
            }
            payload.update(_internal_source_ids(context))
            self._diagnostics.record("scene_turn_result", payload)
