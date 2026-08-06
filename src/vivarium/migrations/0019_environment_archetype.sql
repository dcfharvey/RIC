-- Presets environnementaux versionnes. Ils sont globaux et ne sont pas des
-- faits d'un monde : aucune ecriture dans canonical_event ici.

CREATE TABLE environment_archetype (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    archetype_kind TEXT NOT NULL CHECK (archetype_kind IN ('place', 'connector')),
    key TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (archetype_kind, key)
);

CREATE TABLE environment_archetype_version (
    id INTEGER PRIMARY KEY,
    archetype_id INTEGER NOT NULL REFERENCES environment_archetype(id),
    version INTEGER NOT NULL CHECK (version > 0),
    status TEXT NOT NULL CHECK (status IN ('draft', 'published')),
    contract_json TEXT NOT NULL CHECK (json_type(contract_json) = 'object'),
    created_at TEXT NOT NULL,
    published_at TEXT,
    CHECK (
        (status = 'draft' AND published_at IS NULL)
        OR (status = 'published' AND published_at IS NOT NULL)
    ),
    UNIQUE (archetype_id, version)
);

CREATE UNIQUE INDEX environment_archetype_one_draft
    ON environment_archetype_version(archetype_id) WHERE status = 'draft';

CREATE TRIGGER environment_archetype_published_immutable
BEFORE UPDATE ON environment_archetype_version
WHEN OLD.status = 'published'
BEGIN
    SELECT RAISE(ABORT, 'published environment archetype is immutable');
END;

CREATE TRIGGER environment_archetype_published_no_delete
BEFORE DELETE ON environment_archetype_version
WHEN OLD.status = 'published'
BEGIN
    SELECT RAISE(ABORT, 'published environment archetype cannot be deleted');
END;
