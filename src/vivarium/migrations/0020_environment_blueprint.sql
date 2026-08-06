-- Blueprints environnementaux globaux et provenance des mondes instancies.

CREATE TABLE environment_blueprint (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    key TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE environment_blueprint_version (
    id INTEGER PRIMARY KEY,
    blueprint_id INTEGER NOT NULL REFERENCES environment_blueprint(id),
    version INTEGER NOT NULL CHECK (version > 0),
    status TEXT NOT NULL CHECK (status IN ('draft', 'published')),
    definition_json TEXT NOT NULL CHECK (json_type(definition_json) = 'object'),
    created_at TEXT NOT NULL,
    published_at TEXT,
    CHECK ((status = 'draft' AND published_at IS NULL) OR (status = 'published' AND published_at IS NOT NULL)),
    UNIQUE (blueprint_id, version)
);

CREATE UNIQUE INDEX environment_blueprint_one_draft
    ON environment_blueprint_version(blueprint_id) WHERE status = 'draft';

CREATE TRIGGER environment_blueprint_published_immutable
BEFORE UPDATE ON environment_blueprint_version
WHEN OLD.status = 'published'
BEGIN
    SELECT RAISE(ABORT, 'published environment blueprint is immutable');
END;

CREATE TRIGGER environment_blueprint_published_no_delete
BEFORE DELETE ON environment_blueprint_version
WHEN OLD.status = 'published'
BEGIN
    SELECT RAISE(ABORT, 'published environment blueprint cannot be deleted');
END;

CREATE TABLE world_environment_origin (
    world_id INTEGER PRIMARY KEY REFERENCES worlds(id),
    blueprint_id INTEGER NOT NULL REFERENCES environment_blueprint(id),
    blueprint_version INTEGER NOT NULL CHECK (blueprint_version > 0),
    resolved_definition_json TEXT NOT NULL CHECK (json_type(resolved_definition_json) = 'object'),
    instantiated_at TEXT NOT NULL,
    FOREIGN KEY (blueprint_id, blueprint_version)
        REFERENCES environment_blueprint_version(blueprint_id, version)
);

CREATE TRIGGER world_environment_origin_immutable
BEFORE UPDATE ON world_environment_origin
BEGIN
    SELECT RAISE(ABORT, 'world environment origin is immutable');
END;

CREATE TABLE world_location_origin (
    location_id INTEGER PRIMARY KEY REFERENCES location(id),
    world_id INTEGER NOT NULL,
    archetype_id INTEGER NOT NULL REFERENCES environment_archetype(id),
    archetype_version INTEGER NOT NULL CHECK (archetype_version > 0),
    resolved_contract_json TEXT NOT NULL CHECK (json_type(resolved_contract_json) = 'object'),
    instantiated_at TEXT NOT NULL,
    FOREIGN KEY (world_id, location_id) REFERENCES location(world_id, id),
    FOREIGN KEY (archetype_id, archetype_version)
        REFERENCES environment_archetype_version(archetype_id, version)
);

CREATE TRIGGER world_location_origin_immutable
BEFORE UPDATE ON world_location_origin
BEGIN
    SELECT RAISE(ABORT, 'world location origin is immutable');
END;
