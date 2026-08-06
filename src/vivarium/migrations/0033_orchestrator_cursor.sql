-- Curseurs techniques de l'orchestrateur : ni mémoire ni vérité canonique.
CREATE TABLE orchestrator_cursor (
    id INTEGER PRIMARY KEY,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    last_event_seq INTEGER NOT NULL CHECK(last_event_seq >= 0),
    updated_at TEXT NOT NULL,
    UNIQUE(world_id, character_id)
);
CREATE TABLE orchestrator_run_event (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    source_event_seq INTEGER NOT NULL CHECK(source_event_seq >= 1),
    outcome TEXT NOT NULL CHECK(outcome IN ('routed','deferred','unperceived','provider_degraded')),
    detail_code TEXT,
    recorded_at TEXT NOT NULL,
    UNIQUE(world_id, character_id, source_event_seq)
);
CREATE TRIGGER orchestrator_run_event_no_update BEFORE UPDATE ON orchestrator_run_event BEGIN SELECT RAISE(ABORT,'orchestrator run event is append-only'); END;
CREATE TRIGGER orchestrator_run_event_no_delete BEFORE DELETE ON orchestrator_run_event BEGIN SELECT RAISE(ABORT,'orchestrator run event is append-only'); END;
