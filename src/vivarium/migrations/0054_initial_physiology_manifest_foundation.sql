-- Manifeste T0 inactif et scelle. Il enregistre une condition initiale de
-- modele pour un futur cutover; il ne materialise jamais H/phi/P, ne cree pas
-- d'evenement canonique et ne reconstruit aucune histoire anterieure.

CREATE TABLE initial_physiology_policy (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    policy_key TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version >= 1),
    policy_json TEXT NOT NULL CHECK (json_valid(policy_json) = 1),
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (policy_key, version)
);
CREATE TRIGGER initial_physiology_policy_no_update
BEFORE UPDATE ON initial_physiology_policy
BEGIN SELECT RAISE(ABORT, 'initial physiology policy is immutable'); END;
CREATE TRIGGER initial_physiology_policy_no_delete
BEFORE DELETE ON initial_physiology_policy
BEGIN SELECT RAISE(ABORT, 'initial physiology policy is immutable'); END;

CREATE TABLE t0_phase_rule (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    rule_key TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version >= 1),
    rule_json TEXT NOT NULL CHECK (json_valid(rule_json) = 1),
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (rule_key, version)
);
CREATE TRIGGER t0_phase_rule_no_update
BEFORE UPDATE ON t0_phase_rule
BEGIN SELECT RAISE(ABORT, 'T0 phase rule is immutable'); END;
CREATE TRIGGER t0_phase_rule_no_delete
BEFORE DELETE ON t0_phase_rule
BEGIN SELECT RAISE(ABORT, 'T0 phase rule is immutable'); END;

CREATE TABLE initial_physiology_manifest (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    manifest_key TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version >= 1),
    model_key TEXT NOT NULL CHECK (model_key = 'ric.sleep.additive.v1'),
    model_version INTEGER NOT NULL CHECK (model_version = 1),
    policy_id INTEGER NOT NULL REFERENCES initial_physiology_policy(id) ON DELETE RESTRICT,
    phase_rule_id INTEGER NOT NULL REFERENCES t0_phase_rule(id) ON DELETE RESTRICT,
    anchor_at TEXT NOT NULL,
    provenance TEXT NOT NULL,
    justification TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (world_id, manifest_key, version)
);
CREATE TRIGGER initial_physiology_manifest_no_update
BEFORE UPDATE ON initial_physiology_manifest
BEGIN SELECT RAISE(ABORT, 'initial physiology manifest is immutable'); END;
CREATE TRIGGER initial_physiology_manifest_no_delete
BEFORE DELETE ON initial_physiology_manifest
BEGIN SELECT RAISE(ABORT, 'initial physiology manifest is immutable'); END;

CREATE TABLE initial_physiology_manifest_entry (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    manifest_id INTEGER NOT NULL REFERENCES initial_physiology_manifest(id) ON DELETE RESTRICT,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL,
    profile_id INTEGER NOT NULL REFERENCES sleep_biology_profile(id) ON DELETE RESTRICT,
    homeostatic_load_milli INTEGER NOT NULL CHECK (homeostatic_load_milli BETWEEN 0 AND 100000),
    circadian_phase_milli INTEGER NOT NULL CHECK (circadian_phase_milli BETWEEN 0 AND 999999),
    physical_capacity_milli INTEGER NOT NULL CHECK (physical_capacity_milli BETWEEN 0 AND 100000),
    previous_band TEXT NOT NULL CHECK (previous_band IN ('stable', 'fragile', 'critical')),
    homeostatic_load_residue REAL NOT NULL CHECK (homeostatic_load_residue = 0.0),
    circadian_phase_residue REAL NOT NULL CHECK (circadian_phase_residue = 0.0),
    physical_capacity_remainder INTEGER NOT NULL CHECK (physical_capacity_remainder = 0),
    phase_override INTEGER NOT NULL CHECK (phase_override IN (0, 1)),
    phase_override_provenance TEXT,
    phase_override_justification TEXT,
    provenance TEXT NOT NULL,
    justification TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (manifest_id, character_id),
    FOREIGN KEY (world_id, character_id) REFERENCES character(world_id, id),
    CHECK (
        (phase_override = 0 AND phase_override_provenance IS NULL AND phase_override_justification IS NULL)
        OR
        (phase_override = 1 AND phase_override_provenance IS NOT NULL AND phase_override_justification IS NOT NULL)
    )
);
CREATE TRIGGER initial_physiology_manifest_entry_matches_manifest
BEFORE INSERT ON initial_physiology_manifest_entry
WHEN NOT EXISTS (
    SELECT 1 FROM initial_physiology_manifest
    WHERE id = NEW.manifest_id AND world_id = NEW.world_id
)
BEGIN SELECT RAISE(ABORT, 'initial physiology manifest entry world mismatch'); END;
CREATE TRIGGER initial_physiology_manifest_entry_matches_profile_assignment
BEFORE INSERT ON initial_physiology_manifest_entry
WHEN NOT EXISTS (
    SELECT 1 FROM character_sleep_biology_assignment
    WHERE world_id = NEW.world_id AND character_id = NEW.character_id AND profile_id = NEW.profile_id
)
BEGIN SELECT RAISE(ABORT, 'initial physiology manifest profile mismatch'); END;
CREATE TRIGGER initial_physiology_manifest_entry_not_after_seal
BEFORE INSERT ON initial_physiology_manifest_entry
WHEN EXISTS (
    SELECT 1 FROM initial_physiology_manifest_completion WHERE manifest_id = NEW.manifest_id
)
BEGIN SELECT RAISE(ABORT, 'initial physiology manifest is sealed'); END;
CREATE TRIGGER initial_physiology_manifest_entry_no_update
BEFORE UPDATE ON initial_physiology_manifest_entry
BEGIN SELECT RAISE(ABORT, 'initial physiology manifest entry is immutable'); END;
CREATE TRIGGER initial_physiology_manifest_entry_no_delete
BEFORE DELETE ON initial_physiology_manifest_entry
BEGIN SELECT RAISE(ABORT, 'initial physiology manifest entry is immutable'); END;

CREATE TABLE initial_physiology_manifest_completion (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    manifest_id INTEGER NOT NULL UNIQUE REFERENCES initial_physiology_manifest(id) ON DELETE RESTRICT,
    entry_count INTEGER NOT NULL CHECK (entry_count >= 1),
    sealed_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TRIGGER initial_physiology_manifest_completion_is_complete
BEFORE INSERT ON initial_physiology_manifest_completion
WHEN NEW.entry_count != (
    SELECT COUNT(*) FROM initial_physiology_manifest_entry WHERE manifest_id = NEW.manifest_id
)
OR NEW.entry_count != (
    SELECT COUNT(*)
    FROM character c
    JOIN initial_physiology_manifest m ON m.world_id = c.world_id
    WHERE m.id = NEW.manifest_id
)
BEGIN SELECT RAISE(ABORT, 'initial physiology manifest coverage incomplete'); END;
CREATE TRIGGER initial_physiology_manifest_completion_no_update
BEFORE UPDATE ON initial_physiology_manifest_completion
BEGIN SELECT RAISE(ABORT, 'initial physiology manifest completion is immutable'); END;
CREATE TRIGGER initial_physiology_manifest_completion_no_delete
BEFORE DELETE ON initial_physiology_manifest_completion
BEGIN SELECT RAISE(ABORT, 'initial physiology manifest completion is immutable'); END;
