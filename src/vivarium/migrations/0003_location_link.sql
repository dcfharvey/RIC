-- Migration 0003 : connectivité spatiale (location_link).
-- Modèle orienté : une ligne = possibilité de passer de from_location_id vers
-- to_location_id. Un passage bidirectionnel = deux lignes réciproques.
-- Champs futurs (verrou, blocage, restriction, coût) volontairement absents :
-- ils seront ajoutés lorsqu'ils auront un comportement défini et testé.

-- Prérequis : clé étrangère composite (world_id, location_id) nécessite une
-- contrainte d'unicité sur ces deux colonnes de `location`.
CREATE UNIQUE INDEX location_world_id_id ON location(world_id, id);

CREATE TABLE location_link (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL,
    from_location_id INTEGER NOT NULL,
    to_location_id INTEGER NOT NULL,
    kind TEXT NOT NULL DEFAULT 'door',
    created_at TEXT NOT NULL,
    FOREIGN KEY (world_id, from_location_id) REFERENCES location(world_id, id),
    FOREIGN KEY (world_id, to_location_id) REFERENCES location(world_id, id),
    CHECK (from_location_id <> to_location_id),
    UNIQUE (world_id, from_location_id, to_location_id)
);
