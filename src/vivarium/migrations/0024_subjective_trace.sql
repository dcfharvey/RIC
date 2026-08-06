-- Première trace subjective : séparée des faits et événements canoniques.

CREATE TABLE subjective_trace (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    request_key TEXT NOT NULL,
    source_kind TEXT NOT NULL CHECK (source_kind IN ('state', 'event')),
    source_event_seq INTEGER,
    fact_type TEXT NOT NULL,
    fact_occurred_at TEXT NOT NULL,
    access_kind TEXT NOT NULL,
    fidelity TEXT NOT NULL CHECK (fidelity IN ('complete', 'partial', 'ambiguous', 'signal_only')),
    payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
    encoded_at TEXT NOT NULL,
    UNIQUE (world_id, character_id, request_key),
    CHECK ((source_kind = 'event' AND source_event_seq IS NOT NULL)
        OR (source_kind = 'state' AND source_event_seq IS NULL))
);

CREATE INDEX idx_subjective_trace_character_time
    ON subjective_trace(world_id, character_id, encoded_at DESC, id DESC);

CREATE UNIQUE INDEX idx_subjective_trace_direct_event_once
    ON subjective_trace(world_id, character_id, source_event_seq)
    WHERE source_event_seq IS NOT NULL;

CREATE TRIGGER subjective_trace_character_same_world_insert
BEFORE INSERT ON subjective_trace
WHEN NOT EXISTS (
    SELECT 1 FROM character ch
    WHERE ch.id = NEW.character_id AND ch.world_id = NEW.world_id
)
BEGIN
    SELECT RAISE(ABORT, 'subjective trace character must be in same world');
END;

CREATE TRIGGER subjective_trace_no_update
BEFORE UPDATE ON subjective_trace
BEGIN
    SELECT RAISE(ABORT, 'subjective trace is immutable: UPDATE forbidden');
END;

CREATE TRIGGER subjective_trace_no_delete
BEFORE DELETE ON subjective_trace
BEGIN
    SELECT RAISE(ABORT, 'subjective trace is append-only: DELETE forbidden');
END;

CREATE TABLE subjective_trace_event (
    id INTEGER PRIMARY KEY,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    trace_id INTEGER NOT NULL REFERENCES subjective_trace(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type = 'trace_encoded'),
    payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
    recorded_at TEXT NOT NULL
);

CREATE INDEX idx_subjective_trace_event_trace
    ON subjective_trace_event(world_id, character_id, trace_id, id);

CREATE TRIGGER subjective_trace_event_no_update
BEFORE UPDATE ON subjective_trace_event
BEGIN
    SELECT RAISE(ABORT, 'subjective trace event is append-only: UPDATE forbidden');
END;

CREATE TRIGGER subjective_trace_event_no_delete
BEFORE DELETE ON subjective_trace_event
BEGIN
    SELECT RAISE(ABORT, 'subjective trace event is append-only: DELETE forbidden');
END;
