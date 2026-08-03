-- Migration 0004 : personnages (Lot 3.1 — identités et présence canonique).
-- Quatre habitantes adultes persistantes, identité stable, position canonique.
-- La clé étrangère composite garantit que le lieu appartient au même monde que
-- le personnage. `character.key` est une identité technique immuable.

CREATE TABLE character (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    name TEXT NOT NULL,
    adult INTEGER NOT NULL DEFAULT 1,
    current_location_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (world_id, current_location_id) REFERENCES location(world_id, id),
    CHECK (adult = 1),
    UNIQUE (world_id, key)
);

-- La clé interne ne doit jamais être modifiée (remplacement des fiches par
-- changement de `name`, jamais de `key`).
CREATE TRIGGER character_key_immutable
BEFORE UPDATE OF key ON character
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'character.key is immutable');
END;
