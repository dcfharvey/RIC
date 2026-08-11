-- Fondation inactive de la physiologie veille-sommeil. Elle ne branche aucun
-- runtime et ne transforme pas l'initialisation technique en événement vécu.

CREATE TABLE world_physiology_system (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL UNIQUE REFERENCES worlds(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('inactive', 'prepared')),
    prepared_model_key TEXT,
    prepared_model_version INTEGER,
    prepared_at TEXT,
    prepared_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (
        (status = 'inactive' AND prepared_model_key IS NULL AND prepared_model_version IS NULL
         AND prepared_at IS NULL AND prepared_by IS NULL)
        OR
        (status = 'prepared' AND prepared_model_key IS NOT NULL AND prepared_model_version >= 1
         AND prepared_at IS NOT NULL AND prepared_by IS NOT NULL)
    )
);

CREATE TABLE sleep_biology_profile (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    profile_key TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version >= 1),
    evidence_class TEXT NOT NULL CHECK (evidence_class IN (
        'human_reference', 'generic_feline', 'fictional_canon'
    )),
    parameters_json TEXT NOT NULL CHECK (json_valid(parameters_json) = 1),
    created_at TEXT NOT NULL,
    UNIQUE (profile_key, version)
);
CREATE TRIGGER sleep_biology_profile_no_update
BEFORE UPDATE ON sleep_biology_profile
BEGIN SELECT RAISE(ABORT, 'sleep biology profile is immutable'); END;
CREATE TRIGGER sleep_biology_profile_no_delete
BEFORE DELETE ON sleep_biology_profile
BEGIN SELECT RAISE(ABORT, 'sleep biology profile is immutable'); END;

CREATE TABLE character_sleep_biology_assignment (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    profile_id INTEGER NOT NULL REFERENCES sleep_biology_profile(id) ON DELETE RESTRICT,
    assigned_at TEXT NOT NULL,
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (world_id, character_id) REFERENCES character(world_id, id) ON DELETE CASCADE,
    UNIQUE (world_id, character_id)
);
CREATE TRIGGER character_sleep_biology_assignment_no_update
BEFORE UPDATE ON character_sleep_biology_assignment
BEGIN SELECT RAISE(ABORT, 'sleep biology assignment is immutable'); END;
CREATE TRIGGER character_sleep_biology_assignment_no_delete
BEFORE DELETE ON character_sleep_biology_assignment
BEGIN SELECT RAISE(ABORT, 'sleep biology assignment is immutable'); END;

CREATE TABLE sleep_regulation_state (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    model_key TEXT NOT NULL,
    model_version INTEGER NOT NULL CHECK (model_version >= 1),
    homeostatic_load_milli INTEGER NOT NULL CHECK (homeostatic_load_milli BETWEEN 0 AND 100000),
    circadian_phase_milli INTEGER NOT NULL CHECK (circadian_phase_milli BETWEEN 0 AND 999999),
    anchor_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (world_id, character_id) REFERENCES character(world_id, id) ON DELETE CASCADE,
    UNIQUE (world_id, character_id)
);

CREATE TABLE physical_capacity_state (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    capacity_milli INTEGER NOT NULL CHECK (capacity_milli BETWEEN 0 AND 100000),
    rate_remainder INTEGER NOT NULL DEFAULT 0 CHECK (rate_remainder >= 0),
    anchor_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (world_id, character_id) REFERENCES character(world_id, id) ON DELETE CASCADE,
    UNIQUE (world_id, character_id)
);

-- Journal technique opérateur. Ce n'est volontairement pas canonical_event :
-- son contenu n'est ni un fait vécu ni une source cognitive.
CREATE TABLE sleep_physiology_audit (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL,
    operation TEXT NOT NULL CHECK (operation = 'post_migration_initialization'),
    details_json TEXT NOT NULL CHECK (json_valid(details_json) = 1),
    recorded_at TEXT NOT NULL,
    FOREIGN KEY (world_id, character_id) REFERENCES character(world_id, id) ON DELETE CASCADE
);
CREATE INDEX idx_sleep_physiology_audit_character
ON sleep_physiology_audit(world_id, character_id, id);
CREATE TRIGGER sleep_physiology_audit_no_update
BEFORE UPDATE ON sleep_physiology_audit
BEGIN SELECT RAISE(ABORT, 'sleep physiology audit is append-only'); END;
CREATE TRIGGER sleep_physiology_audit_no_delete
BEFORE DELETE ON sleep_physiology_audit
BEGIN SELECT RAISE(ABORT, 'sleep physiology audit is append-only'); END;
