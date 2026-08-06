-- Migration 0009 : registre global de contrats (Phase 4.2A).
-- Les contrats publiés sont immuables. Ils ne constituent pas encore des faits
-- d'un monde : aucun événement canonique n'est produit à ce stade.

CREATE TABLE registry_definition (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL CHECK (kind IN ('component', 'capability', 'unit')),
    key TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE registry_definition_version (
    id INTEGER PRIMARY KEY,
    definition_id INTEGER NOT NULL REFERENCES registry_definition(id),
    version INTEGER NOT NULL CHECK (version > 0),
    status TEXT NOT NULL CHECK (status IN ('draft', 'published')),
    contract_json TEXT NOT NULL CHECK (json_type(contract_json) = 'object'),
    dependencies_json TEXT NOT NULL CHECK (json_type(dependencies_json) = 'array'),
    incompatibilities_json TEXT NOT NULL CHECK (json_type(incompatibilities_json) = 'array'),
    created_at TEXT NOT NULL,
    published_at TEXT,
    CHECK (
        (status = 'draft' AND published_at IS NULL)
        OR (status = 'published' AND published_at IS NOT NULL)
    ),
    UNIQUE (definition_id, version)
);

CREATE UNIQUE INDEX registry_one_draft_per_definition
    ON registry_definition_version(definition_id) WHERE status = 'draft';

CREATE TRIGGER registry_published_version_immutable
BEFORE UPDATE ON registry_definition_version
WHEN OLD.status = 'published'
BEGIN
    SELECT RAISE(ABORT, 'published registry definition is immutable');
END;

CREATE TRIGGER registry_published_version_no_delete
BEFORE DELETE ON registry_definition_version
WHEN OLD.status = 'published'
BEGIN
    SELECT RAISE(ABORT, 'published registry definition cannot be deleted');
END;
