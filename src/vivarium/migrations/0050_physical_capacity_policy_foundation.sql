-- Catalogue et assignation inactifs de la future politique de capacité P.
-- Aucune ligne n'est créée automatiquement, aucun état P n'est écrit et ce
-- lot ne branche aucun consommateur runtime ou canonique.

CREATE TABLE physical_capacity_policy (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    policy_key TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version >= 1),
    policy_json TEXT NOT NULL CHECK (json_valid(policy_json) = 1),
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (policy_key, version)
);
CREATE TRIGGER physical_capacity_policy_no_update
BEFORE UPDATE ON physical_capacity_policy
BEGIN SELECT RAISE(ABORT, 'physical capacity policy is immutable'); END;
CREATE TRIGGER physical_capacity_policy_no_delete
BEFORE DELETE ON physical_capacity_policy
BEGIN SELECT RAISE(ABORT, 'physical capacity policy is immutable'); END;

CREATE TABLE world_physical_capacity_policy_assignment (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL UNIQUE REFERENCES worlds(id) ON DELETE CASCADE,
    policy_id INTEGER NOT NULL REFERENCES physical_capacity_policy(id) ON DELETE RESTRICT,
    assigned_at TEXT NOT NULL,
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TRIGGER world_physical_capacity_policy_assignment_no_update
BEFORE UPDATE ON world_physical_capacity_policy_assignment
BEGIN SELECT RAISE(ABORT, 'physical capacity policy assignment is append-only'); END;
CREATE TRIGGER world_physical_capacity_policy_assignment_no_delete
BEFORE DELETE ON world_physical_capacity_policy_assignment
BEGIN SELECT RAISE(ABORT, 'physical capacity policy assignment is append-only'); END;
