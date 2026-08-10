-- SCC-2A: appraisal privee et candidates generiques, sans mutation descendante.
DROP TRIGGER cognition_call_admission_character_same_world_insert;
DROP TRIGGER cognition_call_admission_no_update;
DROP TRIGGER cognition_call_admission_no_delete;
DROP INDEX idx_cognition_call_admission_character_time;
ALTER TABLE cognition_call_admission RENAME TO cognition_call_admission_legacy;

CREATE TABLE cognition_call_admission (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    trigger TEXT NOT NULL CHECK (trigger IN (
        'initial_arrival', 'direct_event', 'action_refused', 'intention_blocked',
        'intention_completed', 'scene_turn', 'planned_reflection', 'owner_intervention',
        'social_interpretation', 'social_appraisal'
    )),
    source_key TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    admitted_at TEXT NOT NULL,
    UNIQUE (world_id, character_id, trigger, source_key),
    UNIQUE (world_id, idempotency_key)
);
INSERT INTO cognition_call_admission
    (id, public_id, world_id, character_id, trigger, source_key, idempotency_key, admitted_at)
SELECT id, public_id, world_id, character_id, trigger, source_key, idempotency_key, admitted_at
FROM cognition_call_admission_legacy;
DROP TABLE cognition_call_admission_legacy;
CREATE INDEX idx_cognition_call_admission_character_time
    ON cognition_call_admission(world_id, character_id, admitted_at, id);
CREATE TRIGGER cognition_call_admission_character_same_world_insert
BEFORE INSERT ON cognition_call_admission
WHEN NOT EXISTS (SELECT 1 FROM character ch WHERE ch.id = NEW.character_id AND ch.world_id = NEW.world_id)
BEGIN SELECT RAISE(ABORT, 'cognition call admission character must be in same world'); END;
CREATE TRIGGER cognition_call_admission_no_update
BEFORE UPDATE ON cognition_call_admission
BEGIN SELECT RAISE(ABORT, 'cognition call admission is immutable: UPDATE forbidden'); END;
CREATE TRIGGER cognition_call_admission_no_delete
BEFORE DELETE ON cognition_call_admission
BEGIN SELECT RAISE(ABORT, 'cognition call admission is append-only: DELETE forbidden'); END;

CREATE TABLE social_appraisal (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    source_interpretation_id INTEGER NOT NULL REFERENCES social_interpretation(id) ON DELETE RESTRICT,
    appraisal_key TEXT NOT NULL,
    appraisal_status TEXT NOT NULL CHECK (appraisal_status IN ('relevant','not_relevant','ambiguous','unresolved')),
    qualitative_meaning TEXT NOT NULL CHECK (qualitative_meaning IN ('favorable','defavorable','mixed','neutral','uncertain')),
    importance TEXT NOT NULL CHECK (importance IN ('low','moderate','high','uncertain')),
    bases_json TEXT NOT NULL CHECK (json_valid(bases_json) AND json_type(bases_json) = 'array'),
    origin_kind TEXT NOT NULL CHECK (origin_kind IN ('llm','direct_controlled')),
    model_id TEXT NOT NULL,
    provider_version TEXT NOT NULL,
    snapshot_fingerprint TEXT NOT NULL,
    provider_turn_id TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (world_id, character_id, appraisal_key)
);
CREATE TRIGGER social_appraisal_same_owner_insert
BEFORE INSERT ON social_appraisal
WHEN NOT EXISTS (
    SELECT 1 FROM social_interpretation i
    WHERE i.id = NEW.source_interpretation_id AND i.world_id = NEW.world_id AND i.character_id = NEW.character_id
)
BEGIN SELECT RAISE(ABORT, 'social appraisal source must belong to same owner and world'); END;
CREATE TRIGGER social_appraisal_no_update BEFORE UPDATE ON social_appraisal
BEGIN SELECT RAISE(ABORT, 'social appraisal is immutable: UPDATE forbidden'); END;
CREATE TRIGGER social_appraisal_no_delete BEFORE DELETE ON social_appraisal
BEGIN SELECT RAISE(ABORT, 'social appraisal is append-only: DELETE forbidden'); END;

CREATE TABLE social_appraisal_candidate (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    appraisal_id INTEGER NOT NULL REFERENCES social_appraisal(id) ON DELETE RESTRICT,
    candidate_key TEXT NOT NULL,
    domain TEXT NOT NULL CHECK (domain IN ('affect','belief','relationship','goal_or_intention','memory')),
    basis_refs_json TEXT NOT NULL CHECK (json_valid(basis_refs_json) AND json_type(basis_refs_json) = 'array'),
    justification TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (appraisal_id, candidate_key)
);
CREATE TRIGGER social_appraisal_candidate_same_owner_insert
BEFORE INSERT ON social_appraisal_candidate
WHEN NOT EXISTS (SELECT 1 FROM social_appraisal a WHERE a.id = NEW.appraisal_id AND a.world_id = NEW.world_id AND a.character_id = NEW.character_id)
BEGIN SELECT RAISE(ABORT, 'candidate must belong to appraisal owner and world'); END;
CREATE TRIGGER social_appraisal_candidate_no_update BEFORE UPDATE ON social_appraisal_candidate
BEGIN SELECT RAISE(ABORT, 'social appraisal candidate is immutable: UPDATE forbidden'); END;
CREATE TRIGGER social_appraisal_candidate_no_delete BEFORE DELETE ON social_appraisal_candidate
BEGIN SELECT RAISE(ABORT, 'social appraisal candidate is append-only: DELETE forbidden'); END;

CREATE TABLE social_appraisal_event (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    appraisal_id INTEGER NOT NULL REFERENCES social_appraisal(id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL CHECK (event_type = 'appraisal_created'),
    payload_json TEXT NOT NULL CHECK (json_valid(payload_json) AND json_type(payload_json) = 'object'),
    recorded_at TEXT NOT NULL
);
CREATE TRIGGER social_appraisal_event_no_update BEFORE UPDATE ON social_appraisal_event
BEGIN SELECT RAISE(ABORT, 'social appraisal event is immutable: UPDATE forbidden'); END;
CREATE TRIGGER social_appraisal_event_no_delete BEFORE DELETE ON social_appraisal_event
BEGIN SELECT RAISE(ABORT, 'social appraisal event is append-only: DELETE forbidden'); END;

CREATE TABLE scc2a_attempt (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    source_interpretation_id INTEGER NOT NULL REFERENCES social_interpretation(id) ON DELETE RESTRICT,
    attempt_key TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('deferred','provider_unavailable','appraised')),
    detail_code TEXT,
    recorded_at TEXT NOT NULL,
    UNIQUE (world_id, character_id, attempt_key)
);
CREATE TRIGGER scc2a_attempt_same_owner_insert
BEFORE INSERT ON scc2a_attempt
WHEN NOT EXISTS (SELECT 1 FROM social_interpretation i WHERE i.id = NEW.source_interpretation_id AND i.world_id = NEW.world_id AND i.character_id = NEW.character_id)
BEGIN SELECT RAISE(ABORT, 'SCC-2A attempt source must belong to same owner and world'); END;
CREATE TRIGGER scc2a_attempt_no_update BEFORE UPDATE ON scc2a_attempt
BEGIN SELECT RAISE(ABORT, 'SCC-2A attempt is immutable: UPDATE forbidden'); END;
CREATE TRIGGER scc2a_attempt_no_delete BEFORE DELETE ON scc2a_attempt
BEGIN SELECT RAISE(ABORT, 'SCC-2A attempt is append-only: DELETE forbidden'); END;
