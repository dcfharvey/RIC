"""Frontière locale entre un LLM et le Vivarium.

Le modèle reçoit seulement un contexte déjà autorisé. Sa réponse est une
proposition structurée : elle ne touche jamais SQLite et repasse par le
contrat d'action canonique.
"""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .action_contract import ActionOrchestrator, IntentProposal, ValidationResult
from .attention import AttentionService
from .character import CharacterEngine
from .perception import PerceptionService
from .registry import _KEY_RE
from .subjective_memory import SubjectiveMemoryService
from .util import Clock


COGNITION_SCHEMA_VERSION = 1
DEFAULT_LM_STUDIO_BASE_URL = "http://127.0.0.1:1234/v1"
DEFAULT_TIMEOUT_SECONDS = 45.0
DEFAULT_MAX_TOKENS = 128
MAX_DIRECT_EVENTS, MAX_MEMORIES, MAX_ATTENTION = 10, 10, 8


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
    max_tokens: int = DEFAULT_MAX_TOKENS

    @classmethod
    def from_environment(cls) -> "LocalLLMSettings":
        dotenv = _dotenv_values()
        value = lambda name, default="": os.environ.get(name, dotenv.get(name, default))
        raw = value("VIVARIUM_LLM_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
        try:
            timeout = float(raw)
            max_tokens = int(value("VIVARIUM_LLM_MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))
        except ValueError as exc:
            raise CognitionError("budget ou délai LLM invalide", code="invalid_llm_configuration") from exc
        return cls(
            value("VIVARIUM_LLM_BASE_URL", DEFAULT_LM_STUDIO_BASE_URL),
            value("VIVARIUM_LLM_MODEL").strip(),
            value("VIVARIUM_LLM_API_TOKEN") or None,
            timeout,
            max_tokens,
        ).validated()

    def validated(self) -> "LocalLLMSettings":
        parsed = urlparse(self.base_url)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise CognitionError("le serveur LLM doit être local", code="unsafe_llm_endpoint")
        if not parsed.path.rstrip("/").endswith("/v1"):
            raise CognitionError("l'URL LLM doit se terminer par /v1", code="invalid_llm_configuration")
        if not self.model_id:
            raise CognitionError("modèle LLM non configuré", code="missing_llm_model")
        if not isinstance(self.timeout_seconds, (int, float)) or not 1 <= self.timeout_seconds <= 300:
            raise CognitionError("délai LLM hors limites", code="invalid_llm_configuration")
        if not isinstance(self.max_tokens, int) or isinstance(self.max_tokens, bool) or not 16 <= self.max_tokens <= 512:
            raise CognitionError("budget de sortie LLM hors limites", code="invalid_llm_configuration")
        return self


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
    allowed_traversals: tuple[Mapping[str, str], ...]
    schema_version: int = COGNITION_SCHEMA_VERSION

    def wire(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "character": {"key": self.character_key, "name": self.character_name},
            "observed_at": self.observed_at, "latest_event_seq": self.latest_event_seq,
            "attention": _plain(self.attention), "direct_events": _plain(self.direct_events),
            "memories": _plain(self.memories), "allowed_traversals": _plain(self.allowed_traversals),
        }


class CognitionContextService:
    """Assemble seulement des données accessibles au personnage concerné."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def build(self, world_id: Any, character_key: Any, *, after_event_seq: Any = 0) -> CognitionContext:
        world_id, character_key = _world_id(world_id), _key(character_key, "personnage")
        character = CharacterEngine(self._conn, clock=self._clock).character_sheet(world_id, character_key)
        attention = AttentionService(self._conn, clock=self._clock).snapshot(world_id, character_key, limit=MAX_ATTENTION)
        feed = PerceptionService(self._conn, clock=self._clock).events_since(world_id, character_key, after_event_seq)
        memories = SubjectiveMemoryService(self._conn, clock=self._clock).recall_recent(world_id, character_key, limit=MAX_MEMORIES)
        allowed: list[Mapping[str, str]] = []
        for item in attention.available:
            if item.source_kind != "perception:adjacent_connector":
                continue
            payload = item.fact.payload
            candidate = _freeze({"connector_key": payload["connector"], "target_location_key": payload["destination"]})
            if candidate not in allowed:
                allowed.append(candidate)
        return CognitionContext(
            world_id, character_key, character["name"], attention.observed_at, feed.latest_seq,
            tuple(_fact_wire(item.source_kind, item.priority_milli, item.fact) for item in attention.selected),
            tuple(_fact_wire(item.access_kind, None, item.fact) for item in feed.candidates[:MAX_DIRECT_EVENTS]),
            tuple(_freeze(_plain(memory)) for memory in memories), tuple(allowed),
        )


@dataclass(frozen=True)
class CognitionDecision:
    """Sortie minimale du LLM, avant validation canonique."""

    action: str  # no_action | traverse
    connector_key: str | None = None
    target_location_key: str | None = None
    schema_version: int = COGNITION_SCHEMA_VERSION

    @classmethod
    def parse(cls, value: Any) -> "CognitionDecision":
        allowed_fields = {"schema_version", "action", "connector_key", "target_location_key"}
        if not isinstance(value, Mapping) or set(value) - allowed_fields:
            raise CognitionError("réponse LLM hors contrat", code="invalid_llm_response")
        if value.get("schema_version") != COGNITION_SCHEMA_VERSION:
            raise CognitionError("version de réponse LLM incompatible", code="invalid_llm_response")
        if value.get("action") == "no_action" and set(value) == {"schema_version", "action"}:
            return cls("no_action")
        if value.get("action") == "traverse" and set(value) == allowed_fields:
            return cls("traverse", _key(value["connector_key"], "connecteur"), _key(value["target_location_key"], "destination"))
        raise CognitionError("réponse LLM hors contrat", code="invalid_llm_response")

    def validated(self) -> "CognitionDecision":
        """Valide aussi une décision fournie par un adaptateur Python."""
        if self.action == "no_action":
            wire = {"schema_version": self.schema_version, "action": self.action}
        else:
            wire = {
                "schema_version": self.schema_version, "action": self.action,
                "connector_key": self.connector_key, "target_location_key": self.target_location_key,
            }
        return self.parse(wire)


class CognitionProvider(Protocol):
    def decide(self, context: CognitionContext) -> CognitionDecision: ...


class LMStudioProvider:
    """Client de ``/v1/chat/completions`` avec JSON Schema de LM Studio."""

    _RESPONSE_SCHEMA = {
        "name": "vivarium_cognition_decision_v1",
        "schema": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "schema_version": {"type": "integer", "const": COGNITION_SCHEMA_VERSION},
                "action": {"type": "string", "enum": ["no_action", "traverse"]},
                "connector_key": {"type": "string", "pattern": "^[a-z][a-z0-9_]{0,62}$"},
                "target_location_key": {"type": "string", "pattern": "^[a-z][a-z0-9_]{0,62}$"},
            },
            "required": ["schema_version", "action"],
        },
    }

    def __init__(self, settings: LocalLLMSettings) -> None:
        self._settings = settings.validated()

    @staticmethod
    def _prompt(context: CognitionContext) -> str:
        return (
            "Tu es un composant de décision du Vivarium. Tu ne connais que le JSON fourni. "
            "N'invente aucun fait ni action hors de allowed_traversals; réponds no_action si nécessaire.\n\n"
            + json.dumps(context.wire(), ensure_ascii=False, separators=(",", ":"))
        )

    def decide(self, context: CognitionContext) -> CognitionDecision:
        body = {
            "model": self._settings.model_id, "temperature": 0.2,
            "max_tokens": self._settings.max_tokens,
            "messages": [
                {"role": "system", "content": "Tu proposes une seule action structurée, jamais un fait du monde."},
                {"role": "user", "content": self._prompt(context)},
            ],
            "response_format": {"type": "json_schema", "json_schema": self._RESPONSE_SCHEMA},
        }
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._settings.api_token:
            headers["Authorization"] = f"Bearer {self._settings.api_token}"
        request = Request(self._settings.base_url.rstrip("/") + "/chat/completions", data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers=headers, method="POST")
        try:
            with urlopen(request, timeout=self._settings.timeout_seconds) as response:  # endpoint validated loopback
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            raise CognitionError(f"LM Studio a refusé la requête HTTP {exc.code}", code="llm_http_error") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise CognitionError("LM Studio est inaccessible", code="llm_unavailable") from exc
        try:
            decoded = json.loads(raw)
            content = decoded["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise TypeError("content absent")
            return CognitionDecision.parse(json.loads(content))
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise CognitionError("réponse LM Studio illisible", code="invalid_llm_response") from exc

    def list_models(self) -> tuple[str, ...]:
        """Diagnostic en lecture seule des identifiants chargés par LM Studio."""
        request = Request(self._settings.base_url.rstrip("/") + "/models", headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=self._settings.timeout_seconds) as response:  # endpoint validated loopback
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            raise CognitionError(f"LM Studio a refusé la requête HTTP {exc.code}", code="llm_http_error") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise CognitionError("LM Studio est inaccessible", code="llm_unavailable") from exc
        try:
            data = json.loads(raw)["data"]
            model_ids = tuple(item["id"] for item in data if isinstance(item, Mapping) and isinstance(item.get("id"), str))
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise CognitionError("réponse LM Studio illisible", code="invalid_llm_response") from exc
        return model_ids


@dataclass(frozen=True)
class CognitionTurnResult:
    context: CognitionContext
    decision: CognitionDecision
    validation: ValidationResult | None


class CognitionTurnService:
    """Prépare un tour, appelle un fournisseur et route une action autorisée."""

    def __init__(self, conn: sqlite3.Connection, provider: CognitionProvider, clock: Clock | None = None) -> None:
        self._conn, self._provider, self._clock = conn, provider, clock or Clock()

    def run(self, world_id: Any, character_key: Any, proposal_id: Any, *, after_event_seq: Any = 0) -> CognitionTurnResult:
        proposal_id = _key(proposal_id, "identifiant de proposition")
        context = CognitionContextService(self._conn, clock=self._clock).build(world_id, character_key, after_event_seq=after_event_seq)
        decision = self._provider.decide(context)
        if not isinstance(decision, CognitionDecision):
            raise CognitionError("fournisseur cognitif hors contrat", code="invalid_llm_response")
        decision = decision.validated()
        if decision.action == "no_action":
            return CognitionTurnResult(context, decision, None)
        assert decision.connector_key is not None and decision.target_location_key is not None
        allowed = {(item["connector_key"], item["target_location_key"]) for item in context.allowed_traversals}
        if (decision.connector_key, decision.target_location_key) not in allowed:
            raise CognitionError("traversée LLM non perceptible", code="llm_action_not_perceived")
        validation = ActionOrchestrator(self._conn, clock=self._clock).execute(
            context.world_id,
            IntentProposal.traverse(proposal_id, context.character_key, decision.connector_key, decision.target_location_key),
        )
        return CognitionTurnResult(context, decision, validation)
