-- Résidus numériques minimaux du raccord synthétique veille-sommeil.
-- Ils complètent les projections milli-unitaires existantes afin que les
-- frontières artificielles de matérialisation ne deviennent pas la dynamique
-- H/phi. Aucun état n'est initialisé ici et aucun fait canonique n'est créé.

CREATE TABLE sleep_regulation_precision_state (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    homeostatic_load_residue REAL NOT NULL,
    circadian_phase_residue REAL NOT NULL,
    anchor_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (world_id, character_id) REFERENCES character(world_id, id) ON DELETE CASCADE,
    UNIQUE (world_id, character_id)
);

-- Les lignes antérieures sont déjà des projections milli-unitaires : le seul
-- état exact reconstructible à la migration est donc ce point, avec résidu 0.
INSERT INTO sleep_regulation_precision_state (
    public_id, world_id, character_id,
    homeostatic_load_residue, circadian_phase_residue,
    anchor_at, updated_at
)
SELECT
    'sleep_precision_' || public_id, world_id, character_id,
    0.0, 0.0, anchor_at, updated_at
FROM sleep_regulation_state;
