-- Résolution append-only des engagements temporels de lieu.
CREATE TABLE character_location_plan_resolution (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    plan_id INTEGER NOT NULL REFERENCES character_location_plan(id) ON DELETE CASCADE,
    outcome TEXT NOT NULL CHECK (outcome IN ('fulfilled','refused','cancelled','deferred')),
    resolved_at TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    details_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (world_id, plan_id)
);
CREATE INDEX idx_character_location_plan_resolution_world
ON character_location_plan_resolution(world_id, resolved_at);
CREATE TRIGGER character_location_plan_resolution_no_update
BEFORE UPDATE ON character_location_plan_resolution
BEGIN SELECT RAISE(ABORT, 'character location plan resolution is append-only'); END;
CREATE TRIGGER character_location_plan_resolution_no_delete
BEFORE DELETE ON character_location_plan_resolution
BEGIN SELECT RAISE(ABORT, 'character location plan resolution is append-only'); END;
