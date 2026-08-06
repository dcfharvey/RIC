from datetime import datetime, timezone
import json

import pytest

from vivarium.cognition import (
    CognitionContextService, CognitionDecision, CognitionError, CognitionTurnService,
    DEFAULT_LM_STUDIO_BASE_URL, LMStudioProvider, LocalLLMSettings,
)
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest, max_seq
from vivarium.util import to_iso


class Clock:
    def now(self): return datetime(2026, 8, 6, 12, tzinfo=timezone.utc)
    def now_iso(self): return to_iso(self.now())


class Provider:
    def __init__(self, decision): self.decision, self.context = decision, None
    def decide(self, context): self.context = context; return self.decision


@pytest.fixture
def setup():
    conn = connect_database(":memory:"); ensure_schema(conn); clock = Clock()
    wid = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    yield conn, wid, clock
    conn.close()


def test_local_settings_are_loopback_only_and_require_an_explicit_model(monkeypatch, tmp_path):
    monkeypatch.setenv("VIVARIUM_CONFIG_DIR", str(tmp_path / "empty-config"))
    monkeypatch.delenv("VIVARIUM_LLM_MODEL", raising=False)
    with pytest.raises(CognitionError) as raised:
        LocalLLMSettings.from_environment()
    assert raised.value.code == "missing_llm_model"
    monkeypatch.setenv("VIVARIUM_LLM_MODEL", "gemma-local")
    assert LocalLLMSettings.from_environment().base_url == DEFAULT_LM_STUDIO_BASE_URL
    with pytest.raises(CognitionError) as raised:
        LocalLLMSettings("https://example.test/v1", "gemma-local", None, 45).validated()
    assert raised.value.code == "unsafe_llm_endpoint"


def test_context_contains_only_bounded_authorized_inputs(setup):
    conn, wid, clock = setup
    context = CognitionContextService(conn, clock=clock).build(wid, "sophie")
    assert context.character_name == "Sophie"
    assert 0 < len(context.attention) <= 8 and len(context.memories) == 0 and len(context.beliefs) == 0
    assert context.mood is None and context.emotions == ()
    assert {item["connector_key"] for item in context.allowed_traversals} == {
        "porte_entree", "passage_stationnement"
    }
    assert all("action_provenance" not in str(item) for item in context.direct_events)
    with pytest.raises(TypeError):
        context.allowed_traversals[0]["connector_key"] = "porte_patio"


def test_local_env_file_is_loaded_but_an_exported_variable_wins(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"; config_dir.mkdir()
    (config_dir / ".env").write_text("VIVARIUM_LLM_MODEL=from_file\n", encoding="utf-8")
    monkeypatch.setenv("VIVARIUM_CONFIG_DIR", str(config_dir))
    monkeypatch.delenv("VIVARIUM_LLM_MODEL", raising=False)
    assert LocalLLMSettings.from_environment().model_id == "from_file"
    monkeypatch.setenv("VIVARIUM_LLM_MODEL", "from_shell")
    assert LocalLLMSettings.from_environment().model_id == "from_shell"


def test_no_action_never_writes_and_visible_traversal_is_validated_by_engine(setup):
    conn, wid, clock = setup
    result = CognitionTurnService(conn, Provider(CognitionDecision("no_action")), clock=clock).run(wid, "sophie", "gemma_wait")
    assert result.validation is None
    result = CognitionTurnService(conn, Provider(CognitionDecision("traverse", "porte_entree", "salon")), clock=clock).run(wid, "sophie", "gemma_enter")
    assert result.validation is not None and result.validation.status == "accepted"


def test_llm_cannot_invent_a_hidden_action_even_with_a_well_formed_response(setup):
    conn, wid, clock = setup
    provider = Provider(CognitionDecision("traverse", "porte_patio", "cour"))
    with pytest.raises(CognitionError) as raised:
        CognitionTurnService(conn, provider, clock=clock).run(wid, "sophie", "gemma_hidden")
    assert raised.value.code == "llm_action_not_perceived"


def test_provider_cannot_bypass_the_response_contract(setup):
    conn, wid, clock = setup
    provider = Provider(CognitionDecision("unknown"))
    with pytest.raises(CognitionError) as raised:
        CognitionTurnService(conn, provider, clock=clock).run(wid, "sophie", "gemma_invalid")
    assert raised.value.code == "invalid_llm_response"


def test_unavailable_model_cannot_leave_a_canonical_side_effect(setup):
    conn, wid, clock = setup

    class UnavailableProvider:
        def decide(self, context):
            raise CognitionError("LM Studio est inaccessible", code="llm_unavailable")

    before_state, before_seq = canonical_state_digest(conn, wid), max_seq(conn, wid)
    with pytest.raises(CognitionError) as raised:
        CognitionTurnService(conn, UnavailableProvider(), clock=clock).run(wid, "sophie", "gemma_offline")
    assert raised.value.code == "llm_unavailable"
    assert canonical_state_digest(conn, wid) == before_state and max_seq(conn, wid) == before_seq


def test_lm_studio_request_uses_native_reasoning_off_endpoint(monkeypatch, setup):
    conn, wid, clock = setup
    context = CognitionContextService(conn, clock=clock).build(wid, "sophie")
    captured = {}

    class Response:
        def read(self):
            return b'{"output":[{"type":"message","content":"{\\"schema_version\\":3,\\"action\\":\\"no_action\\"}"}]}'
        def __enter__(self): return self
        def __exit__(self, *args): return False

    def fake_urlopen(request, timeout):
        captured["url"], captured["body"], captured["timeout"] = request.full_url, request.data, timeout
        return Response()

    monkeypatch.setattr("vivarium.cognition.urlopen", fake_urlopen)
    decision = LMStudioProvider(LocalLLMSettings(DEFAULT_LM_STUDIO_BASE_URL, "gemma-local", None, 12)).decide(context)
    sent = json.loads(captured["body"])
    assert decision.action == "no_action"
    assert captured["url"].endswith("/api/v1/chat") and captured["timeout"] == 12
    assert sent["reasoning"] == "off" and sent["store"] is False
    assert sent["max_output_tokens"] == 128


def test_lm_studio_model_listing_is_read_only(monkeypatch):
    class Response:
        def read(self): return b'{"models":[{"key":"gemma-local"}]}'
        def __enter__(self): return self
        def __exit__(self, *args): return False

    monkeypatch.setattr("vivarium.cognition.urlopen", lambda request, timeout: Response())
    provider = LMStudioProvider(LocalLLMSettings(DEFAULT_LM_STUDIO_BASE_URL, "gemma-local", None, 12))
    assert provider.list_models() == ("gemma-local",)
