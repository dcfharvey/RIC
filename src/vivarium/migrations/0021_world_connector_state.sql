-- Instances de connecteurs dans les mondes. Une arête brute historique peut
-- rester sans connecteur; les blueprints récents, eux, lient chaque arête à
-- une instance identifiée et mutable.

CREATE TABLE world_connector (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id),
    key TEXT NOT NULL,
    archetype_id INTEGER NOT NULL REFERENCES environment_archetype(id),
    archetype_version INTEGER NOT NULL CHECK (archetype_version > 0),
    from_location_id INTEGER NOT NULL,
    to_location_id INTEGER NOT NULL,
    directions TEXT NOT NULL CHECK (directions IN ('one_way', 'bidirectional')),
    state TEXT NOT NULL CHECK (state IN ('available', 'closed', 'blocked')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (world_id, from_location_id) REFERENCES location(world_id, id),
    FOREIGN KEY (world_id, to_location_id) REFERENCES location(world_id, id),
    FOREIGN KEY (archetype_id, archetype_version)
        REFERENCES environment_archetype_version(archetype_id, version),
    CHECK (from_location_id <> to_location_id),
    UNIQUE (world_id, key)
);

ALTER TABLE location_link ADD COLUMN connector_id INTEGER REFERENCES world_connector(id);

CREATE INDEX idx_location_link_connector ON location_link(world_id, connector_id);

CREATE TRIGGER location_link_connector_matches_insert
BEFORE INSERT ON location_link
WHEN NEW.connector_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM world_connector c
    WHERE c.id = NEW.connector_id
      AND c.world_id = NEW.world_id
      AND (
          (c.from_location_id = NEW.from_location_id AND c.to_location_id = NEW.to_location_id)
          OR (
              c.directions = 'bidirectional'
              AND c.from_location_id = NEW.to_location_id
              AND c.to_location_id = NEW.from_location_id
          )
      )
)
BEGIN
    SELECT RAISE(ABORT, 'location link must match connector');
END;

CREATE TRIGGER location_link_connector_matches_update
BEFORE UPDATE OF world_id, from_location_id, to_location_id, connector_id ON location_link
WHEN NEW.connector_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM world_connector c
    WHERE c.id = NEW.connector_id
      AND c.world_id = NEW.world_id
      AND (
          (c.from_location_id = NEW.from_location_id AND c.to_location_id = NEW.to_location_id)
          OR (
              c.directions = 'bidirectional'
              AND c.from_location_id = NEW.to_location_id
              AND c.to_location_id = NEW.from_location_id
          )
      )
)
BEGIN
    SELECT RAISE(ABORT, 'location link must match connector');
END;
