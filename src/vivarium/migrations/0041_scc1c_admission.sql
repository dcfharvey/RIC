-- SCC-1C : admission cognitive sélective, séparée de l'interprétation SCC-1B.
CREATE TABLE scc1c_admission (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    trace_id INTEGER NOT NULL REFERENCES subjective_trace(id) ON DELETE RESTRICT,
    interaction_role TEXT NOT NULL CHECK (interaction_role IN ('speaker','addressee','side_participant')),
    decision TEXT NOT NULL CHECK (decision IN ('selected','not_selected')),
    policy_version TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    UNIQUE(world_id, character_id, trace_id)
);

CREATE INDEX idx_scc1c_admission_owner_time
ON scc1c_admission(world_id, character_id, decided_at, id);

CREATE TRIGGER scc1c_admission_source_same_owner
BEFORE INSERT ON scc1c_admission
WHEN NOT EXISTS (
    SELECT 1 FROM subjective_trace trace
    WHERE trace.id = NEW.trace_id
      AND trace.world_id = NEW.world_id
      AND trace.character_id = NEW.character_id
      AND trace.fact_type = 'social_speech_act'
      AND trace.source_social_speech_act_id IS NOT NULL
)
BEGIN
    SELECT RAISE(ABORT, 'SCC-1C source must be an owned social trace');
END;

CREATE TRIGGER scc1c_admission_no_update
BEFORE UPDATE ON scc1c_admission
BEGIN
    SELECT RAISE(ABORT, 'SCC-1C admission is immutable');
END;

CREATE TRIGGER scc1c_admission_no_delete
BEFORE DELETE ON scc1c_admission
BEGIN
    SELECT RAISE(ABORT, 'SCC-1C admission is append-only');
END;

CREATE TABLE scc1c_attempt (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    admission_id INTEGER NOT NULL REFERENCES scc1c_admission(id) ON DELETE RESTRICT,
    attempt_key TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('deferred','provider_unavailable','interpreted')),
    detail_code TEXT,
    recorded_at TEXT NOT NULL,
    UNIQUE(world_id, character_id, attempt_key)
);

CREATE INDEX idx_scc1c_attempt_admission
ON scc1c_attempt(admission_id, recorded_at, id);

CREATE TRIGGER scc1c_attempt_selected_same_owner
BEFORE INSERT ON scc1c_attempt
WHEN NOT EXISTS (
    SELECT 1 FROM scc1c_admission admission
    WHERE admission.id = NEW.admission_id
      AND admission.world_id = NEW.world_id
      AND admission.character_id = NEW.character_id
      AND admission.decision = 'selected'
)
BEGIN
    SELECT RAISE(ABORT, 'SCC-1C attempt requires selected admission');
END;

CREATE TRIGGER scc1c_attempt_no_update
BEFORE UPDATE ON scc1c_attempt
BEGIN
    SELECT RAISE(ABORT, 'SCC-1C attempt is append-only');
END;

CREATE TRIGGER scc1c_attempt_no_delete
BEFORE DELETE ON scc1c_attempt
BEGIN
    SELECT RAISE(ABORT, 'SCC-1C attempt is append-only');
END;
