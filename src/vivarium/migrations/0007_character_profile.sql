-- Migration 0007 : profil individuel typé (Sous-lot 3.2C).
-- Entier à précision fixe (milli) ; AUCUNE colonne REAL.
-- multiplicateurs de seuil : 500..1500 (1000 = 1,000)
-- préférence repos : -1000..1000 ; tolérance idle : 0..1000

CREATE TABLE character_profile (
    character_id INTEGER NOT NULL,
    world_id INTEGER NOT NULL,
    satiete_threshold_mult_milli INTEGER NOT NULL DEFAULT 1000 CHECK (satiete_threshold_mult_milli BETWEEN 500 AND 1500),
    repos_threshold_mult_milli     INTEGER NOT NULL DEFAULT 1000 CHECK (repos_threshold_mult_milli BETWEEN 500 AND 1500),
    energie_threshold_mult_milli   INTEGER NOT NULL DEFAULT 1000 CHECK (energie_threshold_mult_milli BETWEEN 500 AND 1500),
    hygiene_threshold_mult_milli   INTEGER NOT NULL DEFAULT 1000 CHECK (hygiene_threshold_mult_milli BETWEEN 500 AND 1500),
    rest_preference_milli          INTEGER NOT NULL DEFAULT 0    CHECK (rest_preference_milli BETWEEN -1000 AND 1000),
    idle_tolerance_milli           INTEGER NOT NULL DEFAULT 0    CHECK (idle_tolerance_milli BETWEEN 0 AND 1000),
    updated_at TEXT NOT NULL,
    PRIMARY KEY (world_id, character_id),
    FOREIGN KEY (world_id, character_id) REFERENCES character(world_id, id)
);
