import json

from vivarium.cognition import LocalLLMSettings
from vivarium.cognition_policy import CognitionCallLimits
from vivarium.db import connect_database
from vivarium.diagnostics import DiagnosticRecorder
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest
from vivarium.scene_turn import LMStudioSceneTurnProvider, SceneTurnContextService, SceneTurnDecision, SceneTurnService
from vivarium.scenes import SocialSceneService
from vivarium.subjective_memory import SubjectiveMemoryService
from vivarium.traversal import TraversalEngine
from vivarium.util import Clock


def _world():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = Clock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    traversal = TraversalEngine(conn, clock=clock)
    traversal.traverse_character(world_id, "sophie", "porte_entree", "salon")
    traversal.traverse_character(world_id, "erika", "porte_entree", "salon")
    scenes = SocialSceneService(conn, clock=clock)
    scenes.open(world_id, "context_scene", ("sophie", "erika"))
    return conn, world_id, clock, scenes


def _source_id(conn, scene_key, act_key):
    return conn.execute(
        "SELECT a.id FROM social_speech_act a "
        "JOIN social_scene s ON s.id=a.scene_id "
        "WHERE s.scene_key=? AND a.act_key=?",
        (scene_key, act_key),
    ).fetchone()[0]


def test_current_speech_is_exactly_once_in_provider_prompt_and_memory_is_preserved():
    conn, world_id, clock, scenes = _world()
    try:
        text = "La porte est ouverte, mais ce n'est qu'une parole."
        scenes.speak(world_id, "context_scene", "speech-1", "erika", act_kind="inform", content=text, recipient_key="sophie")
        source_id = _source_id(conn, "context_scene", "speech-1")
        SubjectiveMemoryService(conn, clock=clock).encode_social_speech(
            world_id, "sophie", "memory-speech-1", "context_scene", "speech-1"
        )

        context = SceneTurnContextService(conn, clock=clock).build(world_id, "context_scene", "sophie")
        assert context.recent_acts[-1]["source_social_speech_act_id"] == source_id
        assert all(item.get("source_social_speech_act_id") != source_id for item in context.subjective_context.memories)
        assert context.deduplicated_memory_source_ids == (source_id,)

        captured = {}
        raw = '{"schema_version":2,"action":"no_action"}'

        def fake_request(_settings, *, system_prompt, input_text):
            captured["system_prompt"] = system_prompt
            captured["input_text"] = input_text
            return raw

        import vivarium.scene_turn as scene_turn
        original = scene_turn.request_local_model
        scene_turn.request_local_model = fake_request
        try:
            decision = LMStudioSceneTurnProvider(
                LocalLLMSettings("http://127.0.0.1:1234", "qwen3-14b", None, 1)
            ).decide(context)
        finally:
            scene_turn.request_local_model = original

        assert decision.action == "no_action"
        assert captured["input_text"].count(text) == 1
        assert context.subjective_context.memories == () or all(
            item.get("source_social_speech_act_id") != source_id
            for item in context.subjective_context.memories
        )
        persisted = conn.execute(
            "SELECT content_text FROM social_speech_act WHERE id=?", (source_id,)
        ).fetchone()[0]
        assert persisted == text
    finally:
        conn.close()


def test_identical_text_from_distinct_sources_remains_distinct():
    conn, world_id, clock, scenes = _world()
    try:
        text = "Même texte, deux actes distincts."
        scenes.speak(world_id, "context_scene", "speech-1", "erika", act_kind="inform", content=text, recipient_key="sophie")
        scenes.speak(world_id, "context_scene", "speech-2", "sophie", act_kind="answer", content=text, recipient_key="erika")
        context = SceneTurnContextService(conn, clock=clock).build(world_id, "context_scene", "sophie")
        ids = [item["source_social_speech_act_id"] for item in context.recent_acts]
        assert len(ids) == 2 and len(set(ids)) == 2
        assert [item["content"] for item in context.recent_acts] == [text, text]
        assert context.deduplicated_memory_source_ids == ()
    finally:
        conn.close()


def test_new_scene_has_no_recent_acts_but_keeps_historical_memory():
    conn, world_id, clock, scenes = _world()
    try:
        text = "Historique exact conservé."
        scenes.speak(world_id, "context_scene", "speech-1", "erika", act_kind="inform", content=text, recipient_key="sophie")
        SubjectiveMemoryService(conn, clock=clock).encode_social_speech(
            world_id, "sophie", "memory-speech-1", "context_scene", "speech-1"
        )
        scenes.close(world_id, "context_scene", reason="completed")
        scenes.open(world_id, "new_scene", ("sophie", "erika"))
        context = SceneTurnContextService(conn, clock=clock).build(world_id, "new_scene", "sophie")
        assert context.recent_acts == ()
        assert any(
            item.get("source_social_speech_act_id") == _source_id(conn, "context_scene", "speech-1")
            and item["payload"]["content"] == text
            for item in context.subjective_context.memories
        )
        assert context.deduplicated_memory_source_ids == ()
    finally:
        conn.close()


def test_private_memory_does_not_leak_to_another_character_context():
    conn, world_id, clock, scenes = _world()
    try:
        scenes.speak(world_id, "context_scene", "speech-1", "erika", act_kind="inform", content="Privé pour Sophie.", recipient_key="sophie")
        source_id = _source_id(conn, "context_scene", "speech-1")
        SubjectiveMemoryService(conn, clock=clock).encode_social_speech(
            world_id, "sophie", "memory-speech-1", "context_scene", "speech-1"
        )
        erika = SceneTurnContextService(conn, clock=clock).build(world_id, "context_scene", "erika")
        assert all(item.get("source_social_speech_act_id") != source_id for item in erika.subjective_context.memories)
        assert erika.recent_acts[-1]["recipient_key"] == "sophie"
    finally:
        conn.close()


class _NoActionProvider:
    def __init__(self):
        self.calls = 0

    def decide(self, context):
        self.calls += 1
        return SceneTurnDecision("no_action")


class _SpeechProvider:
    def __init__(self):
        self.calls = 0

    def decide(self, context):
        self.calls += 1
        return SceneTurnDecision("speak", "answer", "Réponse exacte.", "erika")


def test_diagnostics_link_prompt_output_validation_and_persisted_speech(tmp_path):
    conn, world_id, clock, scenes = _world()
    try:
        scenes.speak(
            world_id, "context_scene", "speech-1", "erika", act_kind="inform",
            content="Question exacte.", recipient_key="sophie",
        )
        diagnostics = DiagnosticRecorder(tmp_path / "diag.jsonl", enabled=True)
        provider = _SpeechProvider()
        before = canonical_state_digest(conn, world_id)
        result = SceneTurnService(
            conn, provider, clock=clock, diagnostics=diagnostics
        ).run(world_id, "context_scene", "sophie", "turn-1", CognitionCallLimits(0, 3600, 2))
        after = canonical_state_digest(conn, world_id)
        assert result.decision.action == "speak"
        assert provider.calls == 1 and before == after
        assert conn.execute(
            "SELECT content_text FROM social_speech_act WHERE act_key=?", ("turn-1",)
        ).fetchone()[0] == "Réponse exacte."
        records = [json.loads(line) for line in (tmp_path / "diag.jsonl").read_text(encoding="utf-8").splitlines()]
        record = next(item for item in records if item["kind"] == "scene_turn_result")
        assert record["payload"]["persisted_speech"]["content"] == "Réponse exacte."
        assert record["payload"]["validation"] == "accepted"
        assert record["payload"]["context_wire"]["scene"]["recent_acts"]
    finally:
        conn.close()


def test_provider_diagnostic_proves_exact_prompt_output_and_repeat_source(tmp_path, monkeypatch):
    conn, world_id, clock, scenes = _world()
    try:
        text = "Je répète exactement cette phrase."
        scenes.speak(world_id, "context_scene", "speech-1", "erika", act_kind="inform", content=text, recipient_key="sophie")
        source_id = _source_id(conn, "context_scene", "speech-1")
        SubjectiveMemoryService(conn, clock=clock).encode_social_speech(
            world_id, "sophie", "memory-speech-1", "context_scene", "speech-1"
        )
        context = SceneTurnContextService(conn, clock=clock).build(world_id, "context_scene", "sophie")
        raw = json.dumps({
            "schema_version": 2, "action": "speak", "act_kind": "answer",
            "content": text, "recipient_key": "erika",
        }, ensure_ascii=False)
        monkeypatch.setattr("vivarium.scene_turn.request_local_model", lambda *args, **kwargs: raw)
        recorder = DiagnosticRecorder(tmp_path / "provider.jsonl", enabled=True)
        provider = LMStudioSceneTurnProvider(
            LocalLLMSettings("http://127.0.0.1:1234", "qwen3-14b", None, 1),
            diagnostics=recorder,
        )
        assert provider.decide(context).content == text
        record = json.loads((tmp_path / "provider.jsonl").read_text(encoding="utf-8").splitlines()[0])
        payload = record["payload"]
        assert payload["prompt_text"].count(text) == 1
        assert payload["raw_output"] == raw
        assert payload["validated_output"]["content"] == text
        assert payload["deduplicated_memory_source_ids"] == [source_id]
        assert payload["exact_repeat_source_social_speech_act_ids"] == [source_id]
    finally:
        conn.close()


def test_diagnostics_on_and_off_are_functionally_equivalent(tmp_path):
    def run(enabled, path):
        conn, world_id, clock, scenes = _world()
        provider = _NoActionProvider()
        try:
            recorder = DiagnosticRecorder(path, enabled=enabled)
            before = canonical_state_digest(conn, world_id)
            result = SceneTurnService(
                conn, provider, clock=clock, diagnostics=recorder
            ).run(world_id, "context_scene", "sophie", "turn-1", CognitionCallLimits(0, 3600, 2))
            after = canonical_state_digest(conn, world_id)
            return before == after, result.decision.action
        finally:
            conn.close()

    off_unchanged, action_off = run(False, tmp_path / "off.jsonl")
    on_unchanged, action_on = run(True, tmp_path / "on.jsonl")
    assert off_unchanged and on_unchanged and action_off == action_on == "no_action"
    assert not (tmp_path / "off.jsonl").exists()
    assert (tmp_path / "on.jsonl").exists()


def test_speech_remains_expression_and_does_not_create_door_fact():
    conn, world_id, clock, scenes = _world()
    try:
        scenes.speak(
            world_id, "context_scene", "door-claim", "erika", act_kind="inform",
            content="La porte est ouverte.", recipient_key="sophie",
        )
        rows = conn.execute("SELECT payload FROM canonical_event WHERE world_id=?", (world_id,)).fetchall()
        assert all("La porte est ouverte." not in row[0] for row in rows)
        assert conn.execute("SELECT COUNT(*) FROM social_speech_act WHERE content_text=?", ("La porte est ouverte.",)).fetchone()[0] == 1
    finally:
        conn.close()
