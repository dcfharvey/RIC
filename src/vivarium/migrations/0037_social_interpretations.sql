-- SCC-1A : lectures sociales privées, hypothétiques et révisables.

CREATE TABLE social_interpretation (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    interpretation_key TEXT NOT NULL,
    source_trace_id INTEGER NOT NULL REFERENCES subjective_trace(id) ON DELETE RESTRICT,
    interaction_role TEXT NOT NULL CHECK (interaction_role IN ('speaker','addressee','side_participant')),
    understanding_status TEXT NOT NULL CHECK (understanding_status IN ('clear','ambiguous','unresolved')),
    meaning_hypotheses_json TEXT NOT NULL CHECK (json_type(meaning_hypotheses_json) = 'array'),
    motive_hypotheses_json TEXT NOT NULL CHECK (json_type(motive_hypotheses_json) = 'array'),
    revision_of_id INTEGER REFERENCES social_interpretation(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    UNIQUE(world_id, character_id, interpretation_key)
);

CREATE INDEX idx_social_interpretation_owner_time
ON social_interpretation(world_id, character_id, created_at DESC, id DESC);

CREATE INDEX idx_social_interpretation_source
ON social_interpretation(world_id, source_trace_id);

CREATE TABLE social_interpretation_support (
    id INTEGER PRIMARY KEY,
    interpretation_id INTEGER NOT NULL REFERENCES social_interpretation(id) ON DELETE CASCADE,
    trace_id INTEGER NOT NULL REFERENCES subjective_trace(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    UNIQUE(interpretation_id, trace_id)
);

CREATE INDEX idx_social_interpretation_support_trace
ON social_interpretation_support(trace_id, interpretation_id);

CREATE TABLE social_interpretation_event (
    id INTEGER PRIMARY KEY,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    interpretation_id INTEGER NOT NULL REFERENCES social_interpretation(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN ('interpretation_created','interpretation_revised')),
    payload_json TEXT NOT NULL CHECK (json_type(payload_json) = 'object'),
    recorded_at TEXT NOT NULL
);

CREATE TRIGGER social_interpretation_source_same_owner
BEFORE INSERT ON social_interpretation
WHEN NOT EXISTS (
    SELECT 1
    FROM subjective_trace trace
    WHERE trace.id = NEW.source_trace_id
      AND trace.world_id = NEW.world_id
      AND trace.character_id = NEW.character_id
      AND trace.fact_type = 'social_speech_act'
      AND trace.source_social_speech_act_id IS NOT NULL
)
BEGIN
    SELECT RAISE(ABORT, 'social interpretation source must be an owned social trace');
END;

CREATE TRIGGER social_interpretation_revision_same_owner
BEFORE INSERT ON social_interpretation
WHEN NEW.revision_of_id IS NOT NULL
 AND NOT EXISTS (
     SELECT 1
     FROM social_interpretation prior
     WHERE prior.id = NEW.revision_of_id
       AND prior.world_id = NEW.world_id
       AND prior.character_id = NEW.character_id
       AND prior.source_trace_id = NEW.source_trace_id
 )
BEGIN
    SELECT RAISE(ABORT, 'social interpretation revision must keep its source and owner');
END;

CREATE TRIGGER social_interpretation_no_update
BEFORE UPDATE ON social_interpretation
BEGIN
    SELECT RAISE(ABORT, 'social interpretation is immutable: UPDATE forbidden');
END;

CREATE TRIGGER social_interpretation_no_delete
BEFORE DELETE ON social_interpretation
BEGIN
    SELECT RAISE(ABORT, 'social interpretation is append-only: DELETE forbidden');
END;

CREATE TRIGGER social_interpretation_support_same_owner
BEFORE INSERT ON social_interpretation_support
WHEN NOT EXISTS (
    SELECT 1
    FROM social_interpretation interpretation
    JOIN subjective_trace trace ON trace.id = NEW.trace_id
    WHERE interpretation.id = NEW.interpretation_id
      AND interpretation.world_id = trace.world_id
      AND interpretation.character_id = trace.character_id
      AND trace.fact_type = 'social_speech_act'
      AND trace.source_social_speech_act_id IS NOT NULL
      AND trace.id <> interpretation.source_trace_id
)
BEGIN
    SELECT RAISE(ABORT, 'interpretation support must be an additional owned social trace');
END;

CREATE TRIGGER social_interpretation_support_no_update
BEFORE UPDATE ON social_interpretation_support
BEGIN
    SELECT RAISE(ABORT, 'interpretation support is append-only');
END;

CREATE TRIGGER social_interpretation_support_no_delete
BEFORE DELETE ON social_interpretation_support
BEGIN
    SELECT RAISE(ABORT, 'interpretation support is append-only');
END;

CREATE TRIGGER social_interpretation_event_same_owner
BEFORE INSERT ON social_interpretation_event
WHEN NOT EXISTS (
    SELECT 1 FROM social_interpretation interpretation
    WHERE interpretation.id = NEW.interpretation_id
      AND interpretation.world_id = NEW.world_id
      AND interpretation.character_id = NEW.character_id
)
BEGIN
    SELECT RAISE(ABORT, 'interpretation event must belong to holder');
END;

CREATE TRIGGER social_interpretation_event_no_update
BEFORE UPDATE ON social_interpretation_event
BEGIN
    SELECT RAISE(ABORT, 'interpretation event is append-only');
END;

CREATE TRIGGER social_interpretation_event_no_delete
BEFORE DELETE ON social_interpretation_event
BEGIN
    SELECT RAISE(ABORT, 'interpretation event is append-only');
END;
