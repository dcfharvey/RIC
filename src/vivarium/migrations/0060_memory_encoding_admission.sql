-- P0 : décisions explicites d'admission d'encodage et d'amorçage d'épisode.

CREATE TABLE subjective_memory_encoding_admission (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    request_key TEXT NOT NULL,
    candidate_kind TEXT NOT NULL CHECK (candidate_kind IN ('attention', 'direct_event', 'social_speech')),
    candidate_fingerprint TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('not_encoded', 'encoded')),
    reason_code TEXT NOT NULL,
    trace_id INTEGER REFERENCES subjective_trace(id) ON DELETE RESTRICT,
    decided_at TEXT NOT NULL,
    UNIQUE (world_id, character_id, request_key),
    CHECK ((outcome = 'encoded' AND trace_id IS NOT NULL)
        OR (outcome = 'not_encoded' AND trace_id IS NULL))
);

CREATE INDEX idx_memory_encoding_admission_owner_time
    ON subjective_memory_encoding_admission(world_id, character_id, id DESC);

CREATE TRIGGER subjective_memory_encoding_admission_same_owner
BEFORE INSERT ON subjective_memory_encoding_admission
WHEN NOT EXISTS (
    SELECT 1
    FROM subjective_trace trace
    WHERE trace.id = NEW.trace_id
      AND trace.world_id = NEW.world_id
      AND trace.character_id = NEW.character_id
)
AND NEW.trace_id IS NOT NULL
BEGIN
    SELECT RAISE(ABORT, 'memory encoding admission trace must belong to its owner');
END;

CREATE TRIGGER subjective_memory_encoding_admission_character_same_world
BEFORE INSERT ON subjective_memory_encoding_admission
WHEN NOT EXISTS (
    SELECT 1 FROM character ch
    WHERE ch.id = NEW.character_id AND ch.world_id = NEW.world_id
)
BEGIN
    SELECT RAISE(ABORT, 'memory encoding admission character must be in same world');
END;

CREATE TRIGGER subjective_memory_encoding_admission_no_update
BEFORE UPDATE ON subjective_memory_encoding_admission
BEGIN
    SELECT RAISE(ABORT, 'memory encoding admission is append-only');
END;

CREATE TRIGGER subjective_memory_encoding_admission_no_delete
BEFORE DELETE ON subjective_memory_encoding_admission
BEGIN
    SELECT RAISE(ABORT, 'memory encoding admission is append-only');
END;

CREATE TABLE autobiographical_episode_seed_decision (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    trace_id INTEGER NOT NULL REFERENCES subjective_trace(id) ON DELETE RESTRICT,
    outcome TEXT NOT NULL CHECK (outcome IN ('trace_only', 'episode_seeded')),
    reason_code TEXT NOT NULL,
    episode_id INTEGER REFERENCES autobiographical_episode(id) ON DELETE RESTRICT,
    decided_at TEXT NOT NULL,
    UNIQUE (world_id, character_id, trace_id),
    CHECK ((outcome = 'episode_seeded' AND episode_id IS NOT NULL)
        OR (outcome = 'trace_only' AND episode_id IS NULL))
);

CREATE INDEX idx_episode_seed_decision_owner_time
    ON autobiographical_episode_seed_decision(world_id, character_id, id DESC);

CREATE TRIGGER autobiographical_episode_seed_decision_same_owner
BEFORE INSERT ON autobiographical_episode_seed_decision
WHEN NOT EXISTS (
    SELECT 1
    FROM subjective_trace trace
    WHERE trace.id = NEW.trace_id
      AND trace.world_id = NEW.world_id
      AND trace.character_id = NEW.character_id
)
BEGIN
    SELECT RAISE(ABORT, 'episode seed decision trace must belong to its owner');
END;

CREATE TRIGGER autobiographical_episode_seed_decision_episode_same_owner
BEFORE INSERT ON autobiographical_episode_seed_decision
WHEN NEW.episode_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1
    FROM autobiographical_episode episode
    WHERE episode.id = NEW.episode_id
      AND episode.world_id = NEW.world_id
      AND episode.character_id = NEW.character_id
)
BEGIN
    SELECT RAISE(ABORT, 'episode seed decision episode must belong to its owner');
END;

CREATE TRIGGER autobiographical_episode_seed_decision_character_same_world
BEFORE INSERT ON autobiographical_episode_seed_decision
WHEN NOT EXISTS (
    SELECT 1 FROM character ch
    WHERE ch.id = NEW.character_id AND ch.world_id = NEW.world_id
)
BEGIN
    SELECT RAISE(ABORT, 'episode seed decision character must be in same world');
END;

CREATE TRIGGER autobiographical_episode_seed_decision_no_update
BEFORE UPDATE ON autobiographical_episode_seed_decision
BEGIN
    SELECT RAISE(ABORT, 'episode seed decision is append-only');
END;

CREATE TRIGGER autobiographical_episode_seed_decision_no_delete
BEFORE DELETE ON autobiographical_episode_seed_decision
BEGIN
    SELECT RAISE(ABORT, 'episode seed decision is append-only');
END;
