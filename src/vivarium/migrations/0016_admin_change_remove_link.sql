-- Migration 0016 : troisième action de plan administratif (fermeture sûre).
-- Reconstruction nécessaire pour élargir le CHECK tout en préservant chaque
-- plan et audit existants, comme la migration 0015.

DROP TRIGGER admin_audit_event_immutable;
DROP TRIGGER admin_audit_event_no_delete;
DROP TRIGGER admin_change_plan_immutable_fields;
DROP TRIGGER admin_change_plan_transition;
DROP TRIGGER admin_change_plan_no_delete;

CREATE TABLE admin_change_plan_new (
    id                  INTEGER PRIMARY KEY,
    public_id           TEXT NOT NULL UNIQUE,
    world_id            INTEGER NOT NULL REFERENCES worlds(id),
    action_key          TEXT NOT NULL CHECK (action_key IN ('rename_world', 'add_link', 'remove_link')),
    status              TEXT NOT NULL CHECK (status IN ('prepared', 'applied')),
    payload_json        TEXT NOT NULL CHECK (json_valid(payload_json) AND json_type(payload_json) = 'object'),
    impact_json         TEXT NOT NULL CHECK (json_valid(impact_json) AND json_type(impact_json) = 'object'),
    world_event_seq     INTEGER NOT NULL CHECK (world_event_seq >= 0),
    plan_hash           TEXT NOT NULL CHECK (length(plan_hash) = 64),
    expires_at          TEXT NOT NULL,
    prepared_at         TEXT NOT NULL,
    applied_at          TEXT,
    applied_result_json TEXT CHECK (applied_result_json IS NULL OR (json_valid(applied_result_json) AND json_type(applied_result_json) = 'object')),
    CHECK (
        (status = 'prepared' AND applied_at IS NULL AND applied_result_json IS NULL)
        OR
        (status = 'applied' AND applied_at IS NOT NULL AND applied_result_json IS NOT NULL)
    )
);

CREATE TABLE admin_audit_event_new (
    id             INTEGER PRIMARY KEY,
    public_id      TEXT NOT NULL UNIQUE,
    change_plan_id INTEGER NOT NULL REFERENCES admin_change_plan_new(id),
    seq            INTEGER NOT NULL,
    event_type     TEXT NOT NULL CHECK (event_type IN ('change_prepared', 'change_applied')),
    occurred_at    TEXT NOT NULL,
    recorded_at    TEXT NOT NULL,
    payload_json   TEXT NOT NULL CHECK (json_valid(payload_json) AND json_type(payload_json) = 'object'),
    UNIQUE (change_plan_id, seq)
);

INSERT INTO admin_change_plan_new SELECT * FROM admin_change_plan;
INSERT INTO admin_audit_event_new SELECT * FROM admin_audit_event;

DROP TABLE admin_audit_event;
DROP TABLE admin_change_plan;

ALTER TABLE admin_change_plan_new RENAME TO admin_change_plan;
ALTER TABLE admin_audit_event_new RENAME TO admin_audit_event;

CREATE TRIGGER admin_change_plan_immutable_fields
BEFORE UPDATE OF public_id, world_id, action_key, payload_json, impact_json,
                 world_event_seq, plan_hash, expires_at, prepared_at
ON admin_change_plan
BEGIN
    SELECT RAISE(ABORT, 'admin change plan is immutable');
END;

CREATE TRIGGER admin_change_plan_transition
BEFORE UPDATE ON admin_change_plan
WHEN NOT (
    OLD.status = 'prepared'
    AND NEW.status = 'applied'
    AND NEW.applied_at IS NOT NULL
    AND NEW.applied_result_json IS NOT NULL
)
BEGIN
    SELECT RAISE(ABORT, 'admin change plan transition is invalid');
END;

CREATE TRIGGER admin_change_plan_no_delete
BEFORE DELETE ON admin_change_plan
BEGIN
    SELECT RAISE(ABORT, 'admin change plan is append-only: DELETE forbidden');
END;

CREATE TRIGGER admin_audit_event_immutable
BEFORE UPDATE ON admin_audit_event
BEGIN
    SELECT RAISE(ABORT, 'admin audit event is append-only: UPDATE forbidden');
END;

CREATE TRIGGER admin_audit_event_no_delete
BEFORE DELETE ON admin_audit_event
BEGIN
    SELECT RAISE(ABORT, 'admin audit event is append-only: DELETE forbidden');
END;
