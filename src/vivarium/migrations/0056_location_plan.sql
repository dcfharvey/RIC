-- Plans de lieu génériques : intention de retour/arrivée, sans mutation de position.
CREATE TABLE character_location_plan (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL,
    target_location_id INTEGER NOT NULL,
    plan_kind TEXT NOT NULL CHECK (plan_kind IN ('return','arrival','relocation')),
    planned_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('planned','fulfilled','cancelled')),
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (world_id, character_id) REFERENCES character(world_id, id) ON DELETE CASCADE,
    FOREIGN KEY (world_id, target_location_id) REFERENCES location(world_id, id) ON DELETE CASCADE,
    UNIQUE (world_id, character_id, plan_kind, planned_at)
);
CREATE INDEX idx_character_location_plan_due
ON character_location_plan(world_id, character_id, status, planned_at);
CREATE TRIGGER character_location_plan_no_update
BEFORE UPDATE ON character_location_plan
BEGIN SELECT RAISE(ABORT, 'character location plan is append-only'); END;
CREATE TRIGGER character_location_plan_no_delete
BEFORE DELETE ON character_location_plan
BEGIN SELECT RAISE(ABORT, 'character location plan is append-only'); END;
