-- Etat subjectif et journal technique de l'agence non sapiente CAT-0.
CREATE TABLE non_sapient_intention (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    target_kind TEXT NOT NULL CHECK(target_kind IN ('location')),
    target_key TEXT NOT NULL,
    origin_event_seq INTEGER NOT NULL CHECK(origin_event_seq >= 1),
    created_at TEXT NOT NULL,
    UNIQUE(world_id, character_id, origin_event_seq)
);
CREATE TABLE non_sapient_intention_transition (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    intention_id INTEGER NOT NULL REFERENCES non_sapient_intention(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK(status IN ('active','suspended','completed','abandoned')),
    reason_code TEXT NOT NULL,
    effective_at TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);
CREATE TABLE non_sapient_decision_event (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    source_event_seq INTEGER NOT NULL CHECK(source_event_seq >= 1),
    candidates_json TEXT NOT NULL CHECK(json_valid(candidates_json)),
    selected_action TEXT NOT NULL CHECK(selected_action IN ('traverse','wait')),
    target_key TEXT,
    outcome TEXT NOT NULL CHECK(outcome IN ('accepted','blocked','no_opportunity')),
    reason_code TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    UNIQUE(world_id, character_id, source_event_seq)
);
CREATE TRIGGER non_sapient_intention_no_update BEFORE UPDATE ON non_sapient_intention BEGIN SELECT RAISE(ABORT,'non-sapient intention is append-only'); END;
CREATE TRIGGER non_sapient_intention_no_delete BEFORE DELETE ON non_sapient_intention BEGIN SELECT RAISE(ABORT,'non-sapient intention is append-only'); END;
CREATE TRIGGER non_sapient_intention_transition_no_update BEFORE UPDATE ON non_sapient_intention_transition BEGIN SELECT RAISE(ABORT,'non-sapient intention transition is append-only'); END;
CREATE TRIGGER non_sapient_intention_transition_no_delete BEFORE DELETE ON non_sapient_intention_transition BEGIN SELECT RAISE(ABORT,'non-sapient intention transition is append-only'); END;
CREATE TRIGGER non_sapient_decision_event_no_update BEFORE UPDATE ON non_sapient_decision_event BEGIN SELECT RAISE(ABORT,'non-sapient decision event is append-only'); END;
CREATE TRIGGER non_sapient_decision_event_no_delete BEFORE DELETE ON non_sapient_decision_event BEGIN SELECT RAISE(ABORT,'non-sapient decision event is append-only'); END;
