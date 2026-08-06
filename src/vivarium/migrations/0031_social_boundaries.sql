-- Vues relationnelles, limites personnelles et permissions situationnelles.

CREATE TABLE relationship_view (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    owner_character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    target_character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    dimensions_json TEXT NOT NULL CHECK(json_type(dimensions_json)='object'),
    last_event_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(world_id, owner_character_id, target_character_id),
    CHECK(owner_character_id <> target_character_id)
);

CREATE TABLE relationship_evidence (
    id INTEGER PRIMARY KEY,
    view_id INTEGER NOT NULL REFERENCES relationship_view(id) ON DELETE CASCADE,
    trace_id INTEGER NOT NULL REFERENCES subjective_trace(id) ON DELETE RESTRICT,
    impact_json TEXT NOT NULL CHECK(json_type(impact_json)='object'),
    context_json TEXT NOT NULL CHECK(json_type(context_json)='object'),
    created_at TEXT NOT NULL,
    UNIQUE(view_id, trace_id)
);

CREATE TABLE relationship_event (
    id INTEGER PRIMARY KEY,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    owner_character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    target_character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    view_id INTEGER NOT NULL REFERENCES relationship_view(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK(event_type IN ('relationship_initialized','relationship_changed')),
    payload_json TEXT NOT NULL CHECK(json_type(payload_json)='object'),
    recorded_at TEXT NOT NULL
);

CREATE TRIGGER relationship_view_same_world_insert
BEFORE INSERT ON relationship_view
WHEN NOT EXISTS (SELECT 1 FROM character ch WHERE ch.id=NEW.owner_character_id AND ch.world_id=NEW.world_id)
 OR NOT EXISTS (SELECT 1 FROM character ch WHERE ch.id=NEW.target_character_id AND ch.world_id=NEW.world_id)
BEGIN SELECT RAISE(ABORT,'relationship participants must be in same world'); END;
CREATE TRIGGER relationship_view_eventful_update
BEFORE UPDATE ON relationship_view
WHEN NOT (
    NEW.public_id IS OLD.public_id AND NEW.world_id IS OLD.world_id
    AND NEW.owner_character_id IS OLD.owner_character_id AND NEW.target_character_id IS OLD.target_character_id
    AND NEW.created_at IS OLD.created_at AND NEW.last_event_id IS NOT NULL
    AND EXISTS (SELECT 1 FROM relationship_event event WHERE event.id=NEW.last_event_id AND event.view_id=OLD.id
                AND event.world_id=OLD.world_id AND event.owner_character_id=OLD.owner_character_id
                AND event.target_character_id=OLD.target_character_id AND event.id>COALESCE(OLD.last_event_id,0))
)
BEGIN SELECT RAISE(ABORT,'relationship update requires newer audit event'); END;
CREATE TRIGGER relationship_view_no_delete BEFORE DELETE ON relationship_view
BEGIN SELECT RAISE(ABORT,'relationship view cannot be deleted'); END;
CREATE TRIGGER relationship_evidence_same_owner BEFORE INSERT ON relationship_evidence
WHEN NOT EXISTS (SELECT 1 FROM relationship_view view JOIN subjective_trace trace ON trace.id=NEW.trace_id
                 WHERE view.id=NEW.view_id AND view.world_id=trace.world_id AND view.owner_character_id=trace.character_id)
BEGIN SELECT RAISE(ABORT,'relationship evidence must belong to holder'); END;
CREATE TRIGGER relationship_evidence_no_update BEFORE UPDATE ON relationship_evidence
BEGIN SELECT RAISE(ABORT,'relationship evidence is append-only'); END;
CREATE TRIGGER relationship_evidence_no_delete BEFORE DELETE ON relationship_evidence
BEGIN SELECT RAISE(ABORT,'relationship evidence is append-only'); END;
CREATE TRIGGER relationship_event_same_owner BEFORE INSERT ON relationship_event
WHEN NOT EXISTS (SELECT 1 FROM relationship_view view WHERE view.id=NEW.view_id AND view.world_id=NEW.world_id
                 AND view.owner_character_id=NEW.owner_character_id AND view.target_character_id=NEW.target_character_id)
BEGIN SELECT RAISE(ABORT,'relationship event must belong to view'); END;
CREATE TRIGGER relationship_event_no_update BEFORE UPDATE ON relationship_event
BEGIN SELECT RAISE(ABORT,'relationship event is append-only'); END;
CREATE TRIGGER relationship_event_no_delete BEFORE DELETE ON relationship_event
BEGIN SELECT RAISE(ABORT,'relationship event is append-only'); END;

CREATE TABLE personal_boundary (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    boundary_key TEXT NOT NULL,
    domain TEXT NOT NULL CHECK(domain IN ('body','space','time','attention','information','property','relationship','decision')),
    scope_json TEXT NOT NULL CHECK(json_type(scope_json)='object'),
    origin TEXT NOT NULL CHECK(origin IN ('declared','implicit')),
    status TEXT NOT NULL CHECK(status IN ('active','revoked')),
    last_event_id INTEGER,
    created_at TEXT NOT NULL,
    revoked_at TEXT,
    UNIQUE(world_id, character_id, boundary_key)
);

CREATE TABLE personal_boundary_event (
    id INTEGER PRIMARY KEY,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    boundary_id INTEGER NOT NULL REFERENCES personal_boundary(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK(event_type IN ('boundary_declared','boundary_revoked')),
    payload_json TEXT NOT NULL CHECK(json_type(payload_json)='object'),
    recorded_at TEXT NOT NULL
);
CREATE TRIGGER boundary_same_world_insert BEFORE INSERT ON personal_boundary
WHEN NOT EXISTS (SELECT 1 FROM character ch WHERE ch.id=NEW.character_id AND ch.world_id=NEW.world_id)
BEGIN SELECT RAISE(ABORT,'boundary holder must be in same world'); END;
CREATE TRIGGER boundary_eventful_update BEFORE UPDATE ON personal_boundary
WHEN NOT (
    NEW.public_id IS OLD.public_id AND NEW.world_id IS OLD.world_id AND NEW.character_id IS OLD.character_id
    AND NEW.boundary_key IS OLD.boundary_key AND NEW.domain IS OLD.domain AND NEW.scope_json IS OLD.scope_json
    AND NEW.origin IS OLD.origin AND NEW.created_at IS OLD.created_at AND NEW.last_event_id IS NOT NULL
    AND EXISTS (SELECT 1 FROM personal_boundary_event event WHERE event.id=NEW.last_event_id AND event.boundary_id=OLD.id
                AND event.world_id=OLD.world_id AND event.character_id=OLD.character_id AND event.id>COALESCE(OLD.last_event_id,0))
)
BEGIN SELECT RAISE(ABORT,'boundary update requires newer audit event'); END;
CREATE TRIGGER boundary_no_delete BEFORE DELETE ON personal_boundary
BEGIN SELECT RAISE(ABORT,'boundary cannot be deleted'); END;
CREATE TRIGGER boundary_event_same_owner BEFORE INSERT ON personal_boundary_event
WHEN NOT EXISTS (SELECT 1 FROM personal_boundary boundary WHERE boundary.id=NEW.boundary_id AND boundary.world_id=NEW.world_id AND boundary.character_id=NEW.character_id)
BEGIN SELECT RAISE(ABORT,'boundary event must belong to holder'); END;
CREATE TRIGGER boundary_event_no_update BEFORE UPDATE ON personal_boundary_event
BEGIN SELECT RAISE(ABORT,'boundary event is append-only'); END;
CREATE TRIGGER boundary_event_no_delete BEFORE DELETE ON personal_boundary_event
BEGIN SELECT RAISE(ABORT,'boundary event is append-only'); END;

CREATE TABLE situational_permission (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    issuer_character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    recipient_character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    permission_key TEXT NOT NULL,
    action_key TEXT NOT NULL,
    scope_json TEXT NOT NULL CHECK(json_type(scope_json)='object'),
    status TEXT NOT NULL CHECK(status IN ('granted','revoked')),
    last_event_id INTEGER,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    revoked_at TEXT,
    UNIQUE(world_id, issuer_character_id, recipient_character_id, permission_key),
    CHECK(issuer_character_id <> recipient_character_id)
);
CREATE TABLE situational_permission_event (
    id INTEGER PRIMARY KEY,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    issuer_character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    recipient_character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES situational_permission(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK(event_type IN ('permission_granted','permission_revoked')),
    payload_json TEXT NOT NULL CHECK(json_type(payload_json)='object'),
    recorded_at TEXT NOT NULL
);
CREATE TRIGGER permission_same_world_insert BEFORE INSERT ON situational_permission
WHEN NOT EXISTS (SELECT 1 FROM character ch WHERE ch.id=NEW.issuer_character_id AND ch.world_id=NEW.world_id)
 OR NOT EXISTS (SELECT 1 FROM character ch WHERE ch.id=NEW.recipient_character_id AND ch.world_id=NEW.world_id)
BEGIN SELECT RAISE(ABORT,'permission participants must be in same world'); END;
CREATE TRIGGER permission_eventful_update BEFORE UPDATE ON situational_permission
WHEN NOT (
    NEW.public_id IS OLD.public_id AND NEW.world_id IS OLD.world_id
    AND NEW.issuer_character_id IS OLD.issuer_character_id AND NEW.recipient_character_id IS OLD.recipient_character_id
    AND NEW.permission_key IS OLD.permission_key AND NEW.action_key IS OLD.action_key AND NEW.scope_json IS OLD.scope_json
    AND NEW.created_at IS OLD.created_at AND NEW.expires_at IS OLD.expires_at AND NEW.last_event_id IS NOT NULL
    AND EXISTS (SELECT 1 FROM situational_permission_event event WHERE event.id=NEW.last_event_id AND event.permission_id=OLD.id
                AND event.world_id=OLD.world_id AND event.issuer_character_id=OLD.issuer_character_id
                AND event.recipient_character_id=OLD.recipient_character_id AND event.id>COALESCE(OLD.last_event_id,0))
)
BEGIN SELECT RAISE(ABORT,'permission update requires newer audit event'); END;
CREATE TRIGGER permission_no_delete BEFORE DELETE ON situational_permission
BEGIN SELECT RAISE(ABORT,'permission cannot be deleted'); END;
CREATE TRIGGER permission_event_same_owner BEFORE INSERT ON situational_permission_event
WHEN NOT EXISTS (SELECT 1 FROM situational_permission permission WHERE permission.id=NEW.permission_id AND permission.world_id=NEW.world_id
                 AND permission.issuer_character_id=NEW.issuer_character_id AND permission.recipient_character_id=NEW.recipient_character_id)
BEGIN SELECT RAISE(ABORT,'permission event must belong to permission'); END;
CREATE TRIGGER permission_event_no_update BEFORE UPDATE ON situational_permission_event
BEGIN SELECT RAISE(ABORT,'permission event is append-only'); END;
CREATE TRIGGER permission_event_no_delete BEFORE DELETE ON situational_permission_event
BEGIN SELECT RAISE(ABORT,'permission event is append-only'); END;
