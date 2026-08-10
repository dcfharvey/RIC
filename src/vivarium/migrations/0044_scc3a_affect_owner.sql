-- SCC-3A : decision owner-governed du seul domaine affect.
DROP TRIGGER cognition_call_admission_character_same_world_insert;
DROP TRIGGER cognition_call_admission_no_update;
DROP TRIGGER cognition_call_admission_no_delete;
DROP INDEX idx_cognition_call_admission_character_time;
ALTER TABLE cognition_call_admission RENAME TO cognition_call_admission_legacy;
CREATE TABLE cognition_call_admission (
    id INTEGER PRIMARY KEY, public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    trigger TEXT NOT NULL CHECK (trigger IN (
        'initial_arrival','direct_event','action_refused','intention_blocked',
        'intention_completed','scene_turn','planned_reflection','owner_intervention',
        'social_interpretation','social_appraisal','social_affect'
    )),
    source_key TEXT NOT NULL, idempotency_key TEXT NOT NULL, admitted_at TEXT NOT NULL,
    UNIQUE (world_id, character_id, trigger, source_key), UNIQUE (world_id, idempotency_key)
);
INSERT INTO cognition_call_admission
    (id, public_id, world_id, character_id, trigger, source_key, idempotency_key, admitted_at)
SELECT id, public_id, world_id, character_id, trigger, source_key, idempotency_key, admitted_at
FROM cognition_call_admission_legacy;
DROP TABLE cognition_call_admission_legacy;
CREATE INDEX idx_cognition_call_admission_character_time ON cognition_call_admission(world_id, character_id, admitted_at, id);
CREATE TRIGGER cognition_call_admission_character_same_world_insert
BEFORE INSERT ON cognition_call_admission
WHEN NOT EXISTS (SELECT 1 FROM character ch WHERE ch.id=NEW.character_id AND ch.world_id=NEW.world_id)
BEGIN SELECT RAISE(ABORT,'cognition call admission character must be in same world'); END;
CREATE TRIGGER cognition_call_admission_no_update BEFORE UPDATE ON cognition_call_admission
BEGIN SELECT RAISE(ABORT,'cognition call admission is immutable: UPDATE forbidden'); END;
CREATE TRIGGER cognition_call_admission_no_delete BEFORE DELETE ON cognition_call_admission
BEGIN SELECT RAISE(ABORT,'cognition call admission is append-only: DELETE forbidden'); END;

CREATE TABLE scc3a_decision (
    id INTEGER PRIMARY KEY, public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    candidate_id INTEGER NOT NULL REFERENCES social_appraisal_candidate(id) ON DELETE RESTRICT,
    decision_key TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('no_change','start_episode','rejected_invalid')),
    episode_key TEXT,
    detail_code TEXT, provider_model_id TEXT NOT NULL, provider_version TEXT NOT NULL,
    snapshot_fingerprint TEXT NOT NULL, provider_turn_id TEXT, recorded_at TEXT NOT NULL,
    UNIQUE (world_id, character_id, candidate_id), UNIQUE (world_id, character_id, decision_key)
);
CREATE TRIGGER scc3a_decision_same_owner_insert
BEFORE INSERT ON scc3a_decision
WHEN NOT EXISTS (
    SELECT 1 FROM social_appraisal_candidate c
    WHERE c.id=NEW.candidate_id AND c.world_id=NEW.world_id AND c.character_id=NEW.character_id
)
BEGIN SELECT RAISE(ABORT,'SCC-3A candidate must belong to same owner and world'); END;
CREATE TRIGGER scc3a_decision_no_update BEFORE UPDATE ON scc3a_decision
BEGIN SELECT RAISE(ABORT,'SCC-3A decision is immutable: UPDATE forbidden'); END;
CREATE TRIGGER scc3a_decision_no_delete BEFORE DELETE ON scc3a_decision
BEGIN SELECT RAISE(ABORT,'SCC-3A decision is append-only: DELETE forbidden'); END;

CREATE TABLE scc3a_attempt (
    id INTEGER PRIMARY KEY, public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    candidate_id INTEGER NOT NULL REFERENCES social_appraisal_candidate(id) ON DELETE RESTRICT,
    attempt_key TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('deferred','provider_unavailable','no_change','applied','rejected_invalid')),
    detail_code TEXT, recorded_at TEXT NOT NULL,
    UNIQUE (world_id, character_id, attempt_key)
);
CREATE TRIGGER scc3a_attempt_same_owner_insert
BEFORE INSERT ON scc3a_attempt
WHEN NOT EXISTS (
    SELECT 1 FROM social_appraisal_candidate c
    WHERE c.id=NEW.candidate_id AND c.world_id=NEW.world_id AND c.character_id=NEW.character_id
)
BEGIN SELECT RAISE(ABORT,'SCC-3A attempt candidate must belong to same owner and world'); END;
CREATE TRIGGER scc3a_attempt_no_update BEFORE UPDATE ON scc3a_attempt
BEGIN SELECT RAISE(ABORT,'SCC-3A attempt is immutable: UPDATE forbidden'); END;
CREATE TRIGGER scc3a_attempt_no_delete BEFORE DELETE ON scc3a_attempt
BEGIN SELECT RAISE(ABORT,'SCC-3A attempt is append-only: DELETE forbidden'); END;
