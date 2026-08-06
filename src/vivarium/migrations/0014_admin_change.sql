-- Migration 0014 : plans administratifs préparés et audit séparé (Phase 4.2I).
-- Un plan n'est pas un fait du monde : il est conservé dans l'audit administratif.
-- Son application, elle, reste une mutation canonique atomique avec son événement.

CREATE TABLE admin_change_plan (
    id                  INTEGER PRIMARY KEY,
    public_id           TEXT NOT NULL UNIQUE,
    world_id            INTEGER NOT NULL REFERENCES worlds(id),
    action_key          TEXT NOT NULL CHECK (action_key IN ('rename_world')),
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

-- Les données d'un plan sont figées. Seule la transition prepared -> applied,
-- avec son résultat, est autorisée exactement une fois.
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

CREATE TABLE admin_audit_event (
    id             INTEGER PRIMARY KEY,
    public_id      TEXT NOT NULL UNIQUE,
    change_plan_id INTEGER NOT NULL REFERENCES admin_change_plan(id),
    seq            INTEGER NOT NULL,
    event_type     TEXT NOT NULL CHECK (event_type IN ('change_prepared', 'change_applied')),
    occurred_at    TEXT NOT NULL,
    recorded_at    TEXT NOT NULL,
    payload_json   TEXT NOT NULL CHECK (json_valid(payload_json) AND json_type(payload_json) = 'object'),
    UNIQUE (change_plan_id, seq)
);

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
