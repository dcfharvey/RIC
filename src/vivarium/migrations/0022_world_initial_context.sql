CREATE TABLE world_initial_context (
    world_id INTEGER PRIMARY KEY REFERENCES worlds(id),
    public_id TEXT NOT NULL UNIQUE,
    facts_json TEXT NOT NULL CHECK (json_valid(facts_json) = 1),
    created_at TEXT NOT NULL
);

CREATE TRIGGER world_initial_context_immutable_update
BEFORE UPDATE ON world_initial_context
BEGIN
    SELECT RAISE(ABORT, 'world initial context is immutable');
END;

CREATE TRIGGER world_initial_context_immutable_delete
BEFORE DELETE ON world_initial_context
BEGIN
    SELECT RAISE(ABORT, 'world initial context cannot be deleted');
END;
