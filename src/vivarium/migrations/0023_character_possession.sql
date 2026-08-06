-- Possession physique d'objets par les personnages.
-- La position materielle de l'objet reste materialisee dans world_object;
-- les services la synchronisent lorsque le porteur se deplace.

CREATE TABLE character_carried_object (
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    object_id INTEGER NOT NULL REFERENCES world_object(id) ON DELETE CASCADE,
    acquired_at TEXT NOT NULL,
    PRIMARY KEY (world_id, object_id),
    UNIQUE (world_id, character_id, object_id)
);

CREATE INDEX idx_character_carried_object_character
    ON character_carried_object(world_id, character_id, object_id);

CREATE TRIGGER character_carried_object_character_same_world_insert
BEFORE INSERT ON character_carried_object
WHEN NOT EXISTS (
    SELECT 1 FROM character ch
    WHERE ch.id = NEW.character_id AND ch.world_id = NEW.world_id
)
BEGIN
    SELECT RAISE(ABORT, 'carrying character must be in same world');
END;

CREATE TRIGGER character_carried_object_object_same_world_insert
BEFORE INSERT ON character_carried_object
WHEN NOT EXISTS (
    SELECT 1 FROM world_object o
    WHERE o.id = NEW.object_id AND o.world_id = NEW.world_id
)
BEGIN
    SELECT RAISE(ABORT, 'carried object must be in same world');
END;

CREATE TRIGGER character_carried_object_portable_top_level_insert
BEFORE INSERT ON character_carried_object
WHEN NOT EXISTS (
    SELECT 1 FROM world_object o
    WHERE o.id = NEW.object_id AND o.portable = 1 AND o.parent_object_id IS NULL
)
BEGIN
    SELECT RAISE(ABORT, 'carried object must be portable and top level');
END;

CREATE TRIGGER character_carried_object_location_matches_insert
BEFORE INSERT ON character_carried_object
WHEN NOT EXISTS (
    SELECT 1 FROM character ch JOIN world_object o
    WHERE ch.id = NEW.character_id
      AND o.id = NEW.object_id
      AND ch.current_location_id = o.location_id
)
BEGIN
    SELECT RAISE(ABORT, 'carried object must be at character location');
END;

CREATE TRIGGER character_carried_object_no_update
BEFORE UPDATE ON character_carried_object
BEGIN
    SELECT RAISE(ABORT, 'character possession must be changed by release and pickup');
END;
