-- Fondations inactives de terminaison de sommeil. Elles ne remplacent pas la
-- planification legacy, n'initialisent aucun checkpoint et n'ecrivent aucun
-- evenement canonique pendant cette migration.

CREATE TABLE sleep_termination_policy (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    policy_key TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version >= 1),
    policy_json TEXT NOT NULL CHECK (json_valid(policy_json) = 1),
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (policy_key, version)
);
CREATE TRIGGER sleep_termination_policy_no_update
BEFORE UPDATE ON sleep_termination_policy
BEGIN SELECT RAISE(ABORT, 'sleep termination policy is immutable'); END;
CREATE TRIGGER sleep_termination_policy_no_delete
BEFORE DELETE ON sleep_termination_policy
BEGIN SELECT RAISE(ABORT, 'sleep termination policy is immutable'); END;

CREATE TABLE world_sleep_termination_policy_assignment (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL UNIQUE REFERENCES worlds(id) ON DELETE CASCADE,
    policy_id INTEGER NOT NULL REFERENCES sleep_termination_policy(id) ON DELETE RESTRICT,
    assigned_at TEXT NOT NULL,
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TRIGGER world_sleep_termination_policy_assignment_no_update
BEFORE UPDATE ON world_sleep_termination_policy_assignment
BEGIN SELECT RAISE(ABORT, 'sleep termination policy assignment is append-only'); END;
CREATE TRIGGER world_sleep_termination_policy_assignment_no_delete
BEFORE DELETE ON world_sleep_termination_policy_assignment
BEGIN SELECT RAISE(ABORT, 'sleep termination policy assignment is append-only'); END;

-- Cet etat est un plan de l'activite `sleep`, donc il appartient au futur
-- chemin ActivityEngine. `previous_band` est une hystereses de fin de sommeil,
-- distincte de `sleep_wake_hysteresis_state` qui demeure physiologique.
CREATE TABLE activity_sleep_checkpoint (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    activity_id INTEGER NOT NULL UNIQUE REFERENCES activity(id) ON DELETE RESTRICT,
    policy_id INTEGER NOT NULL REFERENCES sleep_termination_policy(id) ON DELETE RESTRICT,
    next_reassessment_at TEXT NOT NULL,
    previous_band TEXT NOT NULL CHECK (previous_band IN ('continue_sleep', 'wake_admissible')),
    hard_cap_at TEXT NOT NULL,
    hard_cap_reported_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(world_id, character_id) REFERENCES character(world_id, id)
);
CREATE TRIGGER activity_sleep_checkpoint_matches_sleep_activity
BEFORE INSERT ON activity_sleep_checkpoint
WHEN NOT EXISTS (
    SELECT 1 FROM activity
    WHERE id = NEW.activity_id AND world_id = NEW.world_id
      AND character_id = NEW.character_id AND type = 'sleep'
)
BEGIN SELECT RAISE(ABORT, 'sleep checkpoint activity mismatch'); END;
CREATE TRIGGER activity_sleep_checkpoint_policy_assigned_to_world
BEFORE INSERT ON activity_sleep_checkpoint
WHEN NOT EXISTS (
    SELECT 1 FROM world_sleep_termination_policy_assignment
    WHERE world_id = NEW.world_id AND policy_id = NEW.policy_id
)
BEGIN SELECT RAISE(ABORT, 'sleep checkpoint policy is not assigned to world'); END;
CREATE TRIGGER activity_sleep_checkpoint_no_delete
BEFORE DELETE ON activity_sleep_checkpoint
BEGIN SELECT RAISE(ABORT, 'activity sleep checkpoint cannot be deleted'); END;

-- Signal technique prive de garde. Il n'est pas un evenement vecu et Guardian
-- ne le lit pas encore : un futur raccord pourra seulement l'observer.
CREATE TABLE sleep_termination_audit (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL,
    activity_id INTEGER NOT NULL REFERENCES activity(id) ON DELETE RESTRICT,
    checkpoint_id INTEGER NOT NULL REFERENCES activity_sleep_checkpoint(id) ON DELETE RESTRICT,
    operation TEXT NOT NULL CHECK (operation IN ('hard_cap_protective')),
    details_json TEXT NOT NULL CHECK (json_valid(details_json) = 1),
    recorded_at TEXT NOT NULL,
    FOREIGN KEY(world_id, character_id) REFERENCES character(world_id, id),
    UNIQUE (checkpoint_id, operation)
);
CREATE TRIGGER sleep_termination_audit_no_update
BEFORE UPDATE ON sleep_termination_audit
BEGIN SELECT RAISE(ABORT, 'sleep termination audit is append-only'); END;
CREATE TRIGGER sleep_termination_audit_no_delete
BEFORE DELETE ON sleep_termination_audit
BEGIN SELECT RAISE(ABORT, 'sleep termination audit is append-only'); END;
