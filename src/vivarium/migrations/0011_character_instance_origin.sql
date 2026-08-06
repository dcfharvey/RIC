-- Migration 0011 : provenance immuable des personnages instanciés (Phase 4.2D).
CREATE TABLE character_instance_origin (
    character_id INTEGER PRIMARY KEY REFERENCES character(id),
    world_id INTEGER NOT NULL,
    template_id INTEGER NOT NULL,
    template_version INTEGER NOT NULL CHECK (template_version > 0),
    resolved_initial_definition_json TEXT NOT NULL
        CHECK (json_type(resolved_initial_definition_json) = 'object'),
    instantiated_at TEXT NOT NULL,
    FOREIGN KEY (world_id, character_id) REFERENCES character(world_id, id),
    FOREIGN KEY (template_id, template_version)
        REFERENCES character_template_version(template_id, version)
);

CREATE TRIGGER character_instance_origin_immutable
BEFORE UPDATE ON character_instance_origin
BEGIN
    SELECT RAISE(ABORT, 'character instance origin is immutable');
END;
