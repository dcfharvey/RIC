-- Migration 0001_initial : schéma initial de la persistance canonique.
-- Chaque migration est appliquée de façon atomique par le runner.

CREATE TABLE worlds (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE canonical_clock (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL UNIQUE REFERENCES worlds(id),
    simulated_now TEXT NOT NULL,
    real_updated_at TEXT NOT NULL
);

CREATE TABLE location (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id),
    key TEXT NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    capacity INTEGER,
    created_at TEXT NOT NULL,
    UNIQUE (world_id, key)
);

CREATE TABLE world_object (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id),
    location_id INTEGER NOT NULL REFERENCES location(id),
    key TEXT NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'present',
    created_at TEXT NOT NULL,
    UNIQUE (world_id, key)
);

CREATE TABLE canonical_event (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id),
    seq INTEGER NOT NULL,
    occurred_at TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL CHECK (json_valid(payload) = 1),
    UNIQUE (world_id, seq)
);

CREATE TRIGGER canonical_event_no_update
BEFORE UPDATE ON canonical_event
BEGIN
    SELECT RAISE(ABORT, 'canonical_event is append-only: UPDATE forbidden');
END;

CREATE TRIGGER canonical_event_no_delete
BEFORE DELETE ON canonical_event
BEGIN
    SELECT RAISE(ABORT, 'canonical_event is append-only: DELETE forbidden');
END;
