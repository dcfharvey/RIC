-- Migration 0026 : disposition canonique initiale de personnalité.
-- Les traits sont une donnée subjective propre au personnage, jamais une
-- commande d'action. La définition source reste figée dans son gabarit.

CREATE TABLE character_personality_disposition (
    world_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    traits_json TEXT NOT NULL CHECK (json_type(traits_json) = 'object'),
    attachment_json TEXT NOT NULL CHECK (json_type(attachment_json) = 'object'),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (world_id, character_id),
    FOREIGN KEY (world_id, character_id) REFERENCES character(world_id, id)
);

CREATE TRIGGER character_personality_disposition_immutable
BEFORE UPDATE ON character_personality_disposition
BEGIN
    SELECT RAISE(ABORT, 'personality disposition is immutable; create a reviewed revision');
END;

CREATE TRIGGER character_personality_disposition_no_delete
BEFORE DELETE ON character_personality_disposition
BEGIN
    SELECT RAISE(ABORT, 'personality disposition cannot be deleted');
END;
