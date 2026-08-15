-- Technical lifecycle of cognitive opportunities, separate from canon and
-- subjective memory. Rows are append-only audit evidence.
CREATE TABLE cognition_flow_event (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER REFERENCES character(id) ON DELETE SET NULL,
    opportunity_id TEXT NOT NULL,
    trigger TEXT NOT NULL,
    source_key TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN (
        'opportunity', 'admitted', 'queued', 'executing', 'completed',
        'duplicate', 'coalesced', 'stale', 'cancelled', 'invalidated',
        'provider_error', 'timeout', 'runaway_guard', 'backpressure', 'refused'
    )),
    reason_code TEXT,
    source_event_seq INTEGER,
    parent_event_seq INTEGER,
    canonical_at TEXT,
    recorded_at TEXT NOT NULL,
    wait_started_at TEXT,
    provider_started_at TEXT,
    provider_finished_at TEXT,
    details_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_cognition_flow_opportunity
    ON cognition_flow_event(world_id, opportunity_id, id);

CREATE INDEX idx_cognition_flow_character_time
    ON cognition_flow_event(world_id, character_id, recorded_at, id);

CREATE TRIGGER cognition_flow_event_no_update
BEFORE UPDATE ON cognition_flow_event
BEGIN
    SELECT RAISE(ABORT, 'cognition flow events are append-only: UPDATE forbidden');
END;

CREATE TRIGGER cognition_flow_event_no_delete
BEFORE DELETE ON cognition_flow_event
BEGIN
    SELECT RAISE(ABORT, 'cognition flow events are append-only: DELETE forbidden');
END;
