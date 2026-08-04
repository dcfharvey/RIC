-- Migration 0006 : Sous-lot 3.2B (activités et effets) + passage au
-- dénominateur canonique commun 36 pour les taux/restes existants.

-- Étape 1 — convertir les restes de need_state au dénominateur 36, en utilisant
-- l'ancien dénominateur de la définition (avant la conversion de cette dernière).
UPDATE need_state
SET rate_remainder = rate_remainder * (
    36 / (SELECT rate_den FROM need_definition nd
          WHERE nd.world_id = need_state.world_id
            AND nd.need_key = need_state.need_key)
);

-- Étape 2 — convertir les taux des définitions : nouveau = ancien × (36 / ancien_den).
-- Exact car tous les dénominateurs du MVP divisent 36.
UPDATE need_definition
SET rate_num = rate_num * (36 / rate_den),
    rate_den = 36;

-- Étape 3 — catalogue des activités (taux nets en unités /36 par seconde).
CREATE TABLE activity_definition (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL,
    activity_type TEXT NOT NULL,
    min_duration_seconds INTEGER NOT NULL CHECK (min_duration_seconds >= 0),
    max_duration_seconds INTEGER NOT NULL CHECK (max_duration_seconds >= min_duration_seconds),
    satiete_rate INTEGER NOT NULL,
    repos_rate INTEGER NOT NULL,
    energie_rate INTEGER NOT NULL,
    hygiene_rate INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (world_id, activity_type)
);

-- Étape 4 — lieux autorisés par activité (clé OU type de lieu, jamais les deux).
CREATE TABLE activity_allowed_location (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL,
    activity_type TEXT NOT NULL,
    location_key TEXT,
    location_kind TEXT,
    created_at TEXT NOT NULL,
    CHECK (
        (location_key IS NOT NULL AND location_kind IS NULL)
        OR (location_key IS NULL AND location_kind IS NOT NULL)
    )
);
-- Deux index uniques partiels : UNIQUE simple avec NULL n'empêche pas les doublons.
CREATE UNIQUE INDEX activity_allowed_key
    ON activity_allowed_location(world_id, activity_type, location_key)
    WHERE location_key IS NOT NULL;
CREATE UNIQUE INDEX activity_allowed_kind
    ON activity_allowed_location(world_id, activity_type, location_kind)
    WHERE location_kind IS NOT NULL;

-- Étape 5 — activité runtime (une seule active par personnage).
CREATE TABLE activity (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    location_id INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    planned_end_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'completed', 'aborted')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (world_id, character_id) REFERENCES character(world_id, id),
    FOREIGN KEY (world_id, location_id) REFERENCES location(world_id, id)
);
CREATE UNIQUE INDEX activity_one_active
    ON activity(world_id, character_id) WHERE status = 'active';
