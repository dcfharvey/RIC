-- Migration 0010 : modèles réutilisables de personnages (Phase 4.2B).
CREATE TABLE character_template (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    key TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE character_template_version (
    id INTEGER PRIMARY KEY,
    template_id INTEGER NOT NULL REFERENCES character_template(id),
    version INTEGER NOT NULL CHECK (version > 0),
    status TEXT NOT NULL CHECK (status IN ('draft', 'published')),
    definition_json TEXT NOT NULL CHECK (json_type(definition_json) = 'object'),
    component_bindings_json TEXT NOT NULL CHECK (json_type(component_bindings_json) = 'array'),
    created_at TEXT NOT NULL,
    published_at TEXT,
    CHECK ((status = 'draft' AND published_at IS NULL) OR (status = 'published' AND published_at IS NOT NULL)),
    UNIQUE (template_id, version)
);

CREATE UNIQUE INDEX character_template_one_draft
    ON character_template_version(template_id) WHERE status = 'draft';

CREATE TRIGGER character_template_published_immutable
BEFORE UPDATE ON character_template_version
WHEN OLD.status = 'published'
BEGIN
    SELECT RAISE(ABORT, 'published character template is immutable');
END;

CREATE TRIGGER character_template_published_no_delete
BEFORE DELETE ON character_template_version
WHEN OLD.status = 'published'
BEGIN
    SELECT RAISE(ABORT, 'published character template cannot be deleted');
END;
