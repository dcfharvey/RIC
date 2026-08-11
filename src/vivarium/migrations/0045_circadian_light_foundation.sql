-- Fondation inactive du cycle lumineux. Ces données décrivent la réalité
-- physique/configurée ; elles ne créent ni événement canonique narratif ni
-- exposition subjective. Aucun profil n'est installé automatiquement.

CREATE TABLE light_schedule_profile (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    profile_key TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version >= 1),
    cycle_seconds INTEGER NOT NULL CHECK (cycle_seconds = 86400),
    schedule_json TEXT NOT NULL CHECK (json_valid(schedule_json) = 1),
    created_at TEXT NOT NULL,
    UNIQUE (profile_key, version)
);

CREATE TRIGGER light_schedule_profile_no_update
BEFORE UPDATE ON light_schedule_profile
BEGIN SELECT RAISE(ABORT, 'light schedule profile is immutable'); END;
CREATE TRIGGER light_schedule_profile_no_delete
BEFORE DELETE ON light_schedule_profile
BEGIN SELECT RAISE(ABORT, 'light schedule profile is immutable'); END;

CREATE TABLE world_light_schedule_assignment (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    profile_id INTEGER NOT NULL REFERENCES light_schedule_profile(id) ON DELETE RESTRICT,
    effective_at TEXT NOT NULL,
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (world_id, effective_at)
);
CREATE INDEX idx_world_light_schedule_assignment_effective
ON world_light_schedule_assignment(world_id, effective_at DESC, id DESC);
CREATE TRIGGER world_light_schedule_assignment_no_update
BEFORE UPDATE ON world_light_schedule_assignment
BEGIN SELECT RAISE(ABORT, 'world light schedule assignment is append-only'); END;
CREATE TRIGGER world_light_schedule_assignment_no_delete
BEFORE DELETE ON world_light_schedule_assignment
BEGIN SELECT RAISE(ABORT, 'world light schedule assignment is append-only'); END;

-- Ce profil exprime seulement la propriété d'exposition du lieu. Il ne dit pas
-- que ce lieu est actuellement éclairé : un futur état physique (lampe,
-- rideau, environnement) aura son propre propriétaire et sa propre frontière
-- causale.
CREATE TABLE location_light_profile (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    profile_key TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version >= 1),
    exposure_milli INTEGER NOT NULL CHECK (exposure_milli BETWEEN 0 AND 100000),
    properties_json TEXT NOT NULL CHECK (json_valid(properties_json) = 1),
    created_at TEXT NOT NULL,
    UNIQUE (profile_key, version)
);
CREATE TRIGGER location_light_profile_no_update
BEFORE UPDATE ON location_light_profile
BEGIN SELECT RAISE(ABORT, 'location light profile is immutable'); END;
CREATE TRIGGER location_light_profile_no_delete
BEFORE DELETE ON location_light_profile
BEGIN SELECT RAISE(ABORT, 'location light profile is immutable'); END;

CREATE TABLE world_location_light_assignment (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    profile_id INTEGER NOT NULL REFERENCES location_light_profile(id) ON DELETE RESTRICT,
    effective_at TEXT NOT NULL,
    provenance TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (world_id, location_id) REFERENCES location(world_id, id) ON DELETE CASCADE,
    UNIQUE (world_id, location_id, effective_at)
);
CREATE INDEX idx_world_location_light_assignment_effective
ON world_location_light_assignment(world_id, location_id, effective_at DESC, id DESC);
CREATE TRIGGER world_location_light_assignment_no_update
BEFORE UPDATE ON world_location_light_assignment
BEGIN SELECT RAISE(ABORT, 'world location light assignment is append-only'); END;
CREATE TRIGGER world_location_light_assignment_no_delete
BEFORE DELETE ON world_location_light_assignment
BEGIN SELECT RAISE(ABORT, 'world location light assignment is append-only'); END;
