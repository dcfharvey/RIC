-- Fondations inactives de l'arbitrage d'actions circadien futur.
-- Ce catalogue et son audit technique ne sont lus par aucun cycle runtime dans
-- ce lot. Ils ne produisent ni evenement canonique ni proposition executable.

CREATE TABLE action_arbitration_policy (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    policy_key TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version >= 1),
    policy_json TEXT NOT NULL CHECK (json_valid(policy_json) = 1),
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (policy_key, version)
);
CREATE TRIGGER action_arbitration_policy_no_update
BEFORE UPDATE ON action_arbitration_policy
BEGIN SELECT RAISE(ABORT, 'action arbitration policy is immutable'); END;
CREATE TRIGGER action_arbitration_policy_no_delete
BEFORE DELETE ON action_arbitration_policy
BEGIN SELECT RAISE(ABORT, 'action arbitration policy is immutable'); END;

CREATE TABLE world_action_arbitration_policy_assignment (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL UNIQUE REFERENCES worlds(id) ON DELETE CASCADE,
    policy_id INTEGER NOT NULL REFERENCES action_arbitration_policy(id) ON DELETE RESTRICT,
    assigned_at TEXT NOT NULL,
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TRIGGER world_action_arbitration_policy_assignment_no_update
BEFORE UPDATE ON world_action_arbitration_policy_assignment
BEGIN SELECT RAISE(ABORT, 'action arbitration policy assignment is append-only'); END;
CREATE TRIGGER world_action_arbitration_policy_assignment_no_delete
BEFORE DELETE ON world_action_arbitration_policy_assignment
BEGIN SELECT RAISE(ABORT, 'action arbitration policy assignment is append-only'); END;

-- Les plans/resume_context d'intentions demeurent opaques : le lien explicite
-- valide seulement le vocabulaire ferme du contrat d'action. La force reste
-- subjective et locale; elle n'est pas une echelle d'arbitrage commune.
CREATE TABLE subjective_intention_action_link (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    intention_id INTEGER NOT NULL REFERENCES subjective_intention(id) ON DELETE RESTRICT,
    action_kind TEXT NOT NULL CHECK (action_kind IN ('traverse', 'start_activity')),
    action_params_json TEXT NOT NULL CHECK (json_type(action_params_json) = 'object'),
    action_key TEXT NOT NULL,
    subjective_strength_milli INTEGER NOT NULL CHECK (subjective_strength_milli BETWEEN 0 AND 1000),
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (world_id, character_id, intention_id, action_key),
    FOREIGN KEY(world_id, character_id) REFERENCES character(world_id, id)
);
CREATE TRIGGER subjective_intention_action_link_same_owner
BEFORE INSERT ON subjective_intention_action_link
WHEN NOT EXISTS (
    SELECT 1 FROM subjective_intention
    WHERE id = NEW.intention_id AND world_id = NEW.world_id AND character_id = NEW.character_id
)
BEGIN SELECT RAISE(ABORT, 'intention action link owner mismatch'); END;
CREATE TRIGGER subjective_intention_action_link_no_update
BEFORE UPDATE ON subjective_intention_action_link
BEGIN SELECT RAISE(ABORT, 'subjective intention action link is append-only'); END;
CREATE TRIGGER subjective_intention_action_link_no_delete
BEFORE DELETE ON subjective_intention_action_link
BEGIN SELECT RAISE(ABORT, 'subjective intention action link is append-only'); END;

-- Audit operateur prive. Il ne fait pas partie du canon ni des surfaces
-- Hugin/Munin; canonical_at est fourni par l'appelant, jamais derive ici.
CREATE TABLE action_arbitration_audit (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    policy_id INTEGER NOT NULL REFERENCES action_arbitration_policy(id) ON DELETE RESTRICT,
    frame_digest TEXT NOT NULL,
    options_json TEXT NOT NULL CHECK (json_type(options_json) = 'array'),
    sources_json TEXT NOT NULL CHECK (json_type(sources_json) = 'array'),
    result_json TEXT NOT NULL CHECK (json_type(result_json) = 'object'),
    canonical_at TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);
CREATE TRIGGER action_arbitration_audit_policy_assigned_to_world
BEFORE INSERT ON action_arbitration_audit
WHEN NOT EXISTS (
    SELECT 1 FROM world_action_arbitration_policy_assignment
    WHERE world_id = NEW.world_id AND policy_id = NEW.policy_id
)
BEGIN SELECT RAISE(ABORT, 'action arbitration audit policy is not assigned to world'); END;
CREATE TRIGGER action_arbitration_audit_no_update
BEFORE UPDATE ON action_arbitration_audit
BEGIN SELECT RAISE(ABORT, 'action arbitration audit is append-only'); END;
CREATE TRIGGER action_arbitration_audit_no_delete
BEFORE DELETE ON action_arbitration_audit
BEGIN SELECT RAISE(ABORT, 'action arbitration audit is append-only'); END;
