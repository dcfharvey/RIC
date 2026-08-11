-- Raccord persistant encore inactif du domaine veille-sommeil.
-- Cette migration n'initialise aucun état, ne touche pas l'histoire canonique
-- et ne branche aucun cycle runtime. L'activation reste un cutover distinct.

ALTER TABLE world_physiology_system RENAME TO world_physiology_system_0046;

CREATE TABLE world_physiology_system (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL UNIQUE REFERENCES worlds(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('inactive', 'prepared', 'active')),
    prepared_model_key TEXT,
    prepared_model_version INTEGER,
    prepared_at TEXT,
    prepared_by TEXT,
    activated_at TEXT,
    activated_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (
        (status = 'inactive' AND prepared_model_key IS NULL AND prepared_model_version IS NULL
         AND prepared_at IS NULL AND prepared_by IS NULL
         AND activated_at IS NULL AND activated_by IS NULL)
        OR
        (status = 'prepared' AND prepared_model_key IS NOT NULL AND prepared_model_version >= 1
         AND prepared_at IS NOT NULL AND prepared_by IS NOT NULL
         AND activated_at IS NULL AND activated_by IS NULL)
        OR
        (status = 'active' AND prepared_model_key IS NOT NULL AND prepared_model_version >= 1
         AND prepared_at IS NOT NULL AND prepared_by IS NOT NULL
         AND activated_at IS NOT NULL AND activated_by IS NOT NULL)
    )
);

INSERT INTO world_physiology_system (
    id, public_id, world_id, status,
    prepared_model_key, prepared_model_version, prepared_at, prepared_by,
    activated_at, activated_by, created_at, updated_at
)
SELECT
    id, public_id, world_id, status,
    prepared_model_key, prepared_model_version, prepared_at, prepared_by,
    NULL, NULL, created_at, updated_at
FROM world_physiology_system_0046;

DROP TABLE world_physiology_system_0046;

-- `previous_band` est une mémoire physiologique minimale pour l'hystérésis.
-- L'anti-répétition d'une interruption n'est délibérément PAS ici : l'activité
-- canonique et sa transition `aborted` restent possédées par ActivityEngine.
CREATE TABLE sleep_wake_hysteresis_state (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    previous_band TEXT NOT NULL CHECK (previous_band IN ('stable', 'fragile', 'critical')),
    anchor_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (world_id, character_id) REFERENCES character(world_id, id) ON DELETE CASCADE,
    UNIQUE (world_id, character_id)
);
