-- Objets portables, installations fixes et contenance objet-a-objet.
-- `location_id` reste toujours le lieu effectif materialise de l'objet,
-- y compris lorsqu'il est dans un conteneur. Cette redondance volontaire rend
-- les lectures de lieu simples; les triggers imposent sa coherence.

ALTER TABLE world_object ADD COLUMN portable INTEGER NOT NULL DEFAULT 0
    CHECK (portable IN (0, 1));

ALTER TABLE world_object ADD COLUMN container_capacity INTEGER
    CHECK (container_capacity IS NULL OR container_capacity >= 0);

ALTER TABLE world_object ADD COLUMN parent_object_id INTEGER
    REFERENCES world_object(id)
    CHECK (parent_object_id IS NULL OR parent_object_id <> id);

CREATE INDEX idx_world_object_parent ON world_object(world_id, parent_object_id, key);

CREATE TRIGGER world_object_location_same_world_insert
BEFORE INSERT ON world_object
WHEN NOT EXISTS (
    SELECT 1 FROM location l
    WHERE l.id = NEW.location_id AND l.world_id = NEW.world_id
)
BEGIN
    SELECT RAISE(ABORT, 'object location must be in same world');
END;

CREATE TRIGGER world_object_location_same_world_update
BEFORE UPDATE OF world_id, location_id ON world_object
WHEN NOT EXISTS (
    SELECT 1 FROM location l
    WHERE l.id = NEW.location_id AND l.world_id = NEW.world_id
)
BEGIN
    SELECT RAISE(ABORT, 'object location must be in same world');
END;

CREATE TRIGGER world_object_parent_same_world_insert
BEFORE INSERT ON world_object
WHEN NEW.parent_object_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM world_object p
    WHERE p.id = NEW.parent_object_id AND p.world_id = NEW.world_id
)
BEGIN
    SELECT RAISE(ABORT, 'object parent must be in same world');
END;

CREATE TRIGGER world_object_parent_same_world_update
BEFORE UPDATE OF world_id, parent_object_id ON world_object
WHEN NEW.parent_object_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM world_object p
    WHERE p.id = NEW.parent_object_id AND p.world_id = NEW.world_id
)
BEGIN
    SELECT RAISE(ABORT, 'object parent must be in same world');
END;

CREATE TRIGGER world_object_parent_location_insert
BEFORE INSERT ON world_object
WHEN NEW.parent_object_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM world_object p
    WHERE p.id = NEW.parent_object_id AND p.location_id = NEW.location_id
)
BEGIN
    SELECT RAISE(ABORT, 'contained object location must match parent');
END;

CREATE TRIGGER world_object_parent_location_update
BEFORE UPDATE OF parent_object_id, location_id ON world_object
WHEN NEW.parent_object_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM world_object p
    WHERE p.id = NEW.parent_object_id AND p.location_id = NEW.location_id
)
BEGIN
    SELECT RAISE(ABORT, 'contained object location must match parent');
END;

CREATE TRIGGER world_object_parent_no_cycle
BEFORE UPDATE OF parent_object_id ON world_object
WHEN NEW.parent_object_id IS NOT NULL
BEGIN
    SELECT CASE WHEN EXISTS (
        WITH RECURSIVE ancestors(id) AS (
            SELECT NEW.parent_object_id
            UNION ALL
            SELECT o.parent_object_id
            FROM world_object o JOIN ancestors a ON o.id = a.id
            WHERE o.parent_object_id IS NOT NULL
        )
        SELECT 1 FROM ancestors WHERE id = NEW.id
    ) THEN RAISE(ABORT, 'object containment cycle') END;
END;
