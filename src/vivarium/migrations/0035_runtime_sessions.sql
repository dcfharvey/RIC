-- Migration 0035 : l'horloge ne progresse que pendant une session runtime.

ALTER TABLE canonical_clock
ADD COLUMN runtime_state TEXT NOT NULL DEFAULT 'running'
CHECK (runtime_state IN ('running', 'stopped'));

CREATE TABLE runtime_session (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id),
    started_at TEXT NOT NULL,
    last_heartbeat_at TEXT NOT NULL,
    last_canonical_at TEXT NOT NULL,
    stopped_at TEXT,
    stop_kind TEXT CHECK (stop_kind IN ('clean', 'protective', 'crash_recovered')),
    CHECK ((stopped_at IS NULL AND stop_kind IS NULL) OR
           (stopped_at IS NOT NULL AND stop_kind IS NOT NULL))
);

CREATE UNIQUE INDEX one_open_runtime_session_per_world
ON runtime_session(world_id) WHERE stopped_at IS NULL;

CREATE TABLE runtime_session_event (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id),
    session_id INTEGER NOT NULL REFERENCES runtime_session(id),
    event_kind TEXT NOT NULL CHECK (
        event_kind IN ('started', 'clean_stop', 'protective_stop', 'crash_recovered')
    ),
    canonical_at TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE TRIGGER runtime_session_event_no_update
BEFORE UPDATE ON runtime_session_event
BEGIN
    SELECT RAISE(ABORT, 'runtime_session_event is append-only');
END;

CREATE TRIGGER runtime_session_event_no_delete
BEFORE DELETE ON runtime_session_event
BEGIN
    SELECT RAISE(ABORT, 'runtime_session_event is append-only');
END;
