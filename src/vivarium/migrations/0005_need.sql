-- Migration 0005 : besoins dérivés et matérialisation (Sous-lot 3.2A).
-- Valeur entière à précision fixe : value_milli ∈ [0, 100000] (0 déficient,
-- 100000 satisfait), affichage public = /1000.
-- Taux rationnel entier (milli / seconde simulée) : rate_num / rate_den.
-- `rate_remainder` conserve la fraction pour que l'évolution soit exactement
-- indépendante du découpage des matérialisations (0 <= reste < rate_den).

CREATE TABLE need_definition (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL,
    need_key TEXT NOT NULL,
    name TEXT NOT NULL,
    min_milli INTEGER NOT NULL DEFAULT 0 CHECK (min_milli BETWEEN 0 AND 100000),
    max_milli INTEGER NOT NULL DEFAULT 100000 CHECK (max_milli BETWEEN 0 AND 100000),
    rate_num INTEGER NOT NULL,
    rate_den INTEGER NOT NULL CHECK (rate_den > 0),
    threshold_milli INTEGER NOT NULL DEFAULT 50000 CHECK (threshold_milli BETWEEN 0 AND 100000),
    created_at TEXT NOT NULL,
    UNIQUE (world_id, need_key)
);
CREATE INDEX need_definition_world ON need_definition(world_id);

-- Prérequis : clé étrangère composite (world_id, character_id)
CREATE UNIQUE INDEX character_world_id_id ON character(world_id, id);

CREATE TABLE need_state (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    need_key TEXT NOT NULL,
    value_milli INTEGER NOT NULL CHECK (value_milli BETWEEN 0 AND 100000),
    rate_remainder INTEGER NOT NULL DEFAULT 0 CHECK (rate_remainder >= 0),
    anchor_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (world_id, character_id) REFERENCES character(world_id, id),
    FOREIGN KEY (world_id, need_key) REFERENCES need_definition(world_id, need_key),
    UNIQUE (character_id, need_key)
);
