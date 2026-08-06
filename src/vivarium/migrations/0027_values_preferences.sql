-- Migration 0027 : valeurs et préférences initiales, séparées.

CREATE TABLE character_value_profile (
    world_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    ranked_value_keys_json TEXT NOT NULL CHECK (json_type(ranked_value_keys_json) = 'array'),
    created_at TEXT NOT NULL,
    PRIMARY KEY (world_id, character_id),
    FOREIGN KEY (world_id, character_id) REFERENCES character(world_id, id)
);

CREATE TABLE character_preference_profile (
    world_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    items_json TEXT NOT NULL CHECK (json_type(items_json) = 'array'),
    created_at TEXT NOT NULL,
    PRIMARY KEY (world_id, character_id),
    FOREIGN KEY (world_id, character_id) REFERENCES character(world_id, id)
);

CREATE TRIGGER character_value_profile_immutable
BEFORE UPDATE ON character_value_profile
BEGIN
    SELECT RAISE(ABORT, 'value profile is immutable; create a reviewed revision');
END;

CREATE TRIGGER character_value_profile_no_delete
BEFORE DELETE ON character_value_profile
BEGIN
    SELECT RAISE(ABORT, 'value profile cannot be deleted');
END;

CREATE TRIGGER character_preference_profile_immutable
BEFORE UPDATE ON character_preference_profile
BEGIN
    SELECT RAISE(ABORT, 'preference profile is immutable; create a reviewed revision');
END;

CREATE TRIGGER character_preference_profile_no_delete
BEFORE DELETE ON character_preference_profile
BEGIN
    SELECT RAISE(ABORT, 'preference profile cannot be deleted');
END;
