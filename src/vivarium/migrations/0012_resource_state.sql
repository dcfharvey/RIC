-- Migration 0012 : ressources génériques, bandes et état dérivé (Phase 4.2G).
CREATE TABLE resource_definition (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id),
    resource_key TEXT NOT NULL,
    name TEXT NOT NULL,
    min_milli INTEGER NOT NULL DEFAULT 0 CHECK (min_milli = 0),
    max_milli INTEGER NOT NULL DEFAULT 100000 CHECK (max_milli = 100000),
    created_at TEXT NOT NULL,
    UNIQUE (world_id, resource_key)
);

CREATE TABLE resource_state (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    resource_key TEXT NOT NULL,
    value_milli INTEGER NOT NULL CHECK (value_milli BETWEEN 0 AND 100000),
    rate_num INTEGER NOT NULL,
    rate_den INTEGER NOT NULL CHECK (rate_den > 0),
    rate_remainder INTEGER NOT NULL DEFAULT 0 CHECK (rate_remainder >= 0),
    anchor_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (world_id, character_id) REFERENCES character(world_id, id),
    FOREIGN KEY (world_id, resource_key) REFERENCES resource_definition(world_id, resource_key),
    UNIQUE (character_id, resource_key)
);

CREATE TABLE resource_state_band (
    id INTEGER PRIMARY KEY,
    resource_state_id INTEGER NOT NULL REFERENCES resource_state(id),
    state_key TEXT NOT NULL,
    min_milli INTEGER NOT NULL CHECK (min_milli BETWEEN 0 AND 100000),
    max_milli INTEGER NOT NULL CHECK (max_milli BETWEEN 0 AND 100000 AND max_milli >= min_milli),
    UNIQUE (resource_state_id, state_key),
    UNIQUE (resource_state_id, min_milli),
    UNIQUE (resource_state_id, max_milli)
);

CREATE TRIGGER resource_state_band_immutable
BEFORE UPDATE ON resource_state_band
BEGIN
    SELECT RAISE(ABORT, 'resource state bands are immutable');
END;
