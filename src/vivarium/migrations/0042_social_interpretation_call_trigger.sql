-- Ajoute le déclencheur technique SCC-1B social sans modifier une migration publiée.
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
        'social_interpretation'
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
WHEN NOT EXISTS (
    SELECT 1 FROM character ch
    WHERE ch.id = NEW.character_id AND ch.world_id = NEW.world_id
)
BEGIN
    SELECT RAISE(ABORT, 'cognition call admission character must be in same world');
END;

CREATE TRIGGER cognition_call_admission_no_update
BEFORE UPDATE ON cognition_call_admission
BEGIN
    SELECT RAISE(ABORT, 'cognition call admission is immutable: UPDATE forbidden');
END;

CREATE TRIGGER cognition_call_admission_no_delete
BEFORE DELETE ON cognition_call_admission
BEGIN
    SELECT RAISE(ABORT, 'cognition call admission is append-only: DELETE forbidden');
END;
