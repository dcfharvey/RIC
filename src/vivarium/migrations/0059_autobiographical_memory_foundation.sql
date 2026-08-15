-- P0 : épisode autobiographique minimal, distinct de la trace subjective.

CREATE TABLE autobiographical_episode (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    episode_key TEXT NOT NULL,
    gist_json TEXT NOT NULL CHECK (json_type(gist_json) = 'object'),
    details_json TEXT NOT NULL CHECK (json_type(details_json) = 'object'),
    context_json TEXT NOT NULL CHECK (json_type(context_json) = 'object'),
    participants_json TEXT NOT NULL CHECK (json_type(participants_json) = 'array'),
    experience_started_at TEXT NOT NULL,
    experience_ended_at TEXT NOT NULL,
    source_attribution_json TEXT NOT NULL CHECK (json_type(source_attribution_json) = 'object'),
    recovery_cues_json TEXT NOT NULL CHECK (json_type(recovery_cues_json) = 'array'),
    importance_milli INTEGER NOT NULL CHECK (importance_milli BETWEEN 0 AND 1000),
    accessibility_milli INTEGER NOT NULL CHECK (accessibility_milli BETWEEN 0 AND 1000),
    formed_at TEXT NOT NULL,
    UNIQUE (world_id, character_id, episode_key),
    CHECK (experience_ended_at >= experience_started_at)
);

CREATE INDEX idx_autobiographical_episode_owner_time
    ON autobiographical_episode(world_id, character_id, experience_ended_at DESC, id DESC);

CREATE TABLE autobiographical_episode_support (
    id INTEGER PRIMARY KEY,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    episode_id INTEGER NOT NULL REFERENCES autobiographical_episode(id) ON DELETE CASCADE,
    trace_id INTEGER NOT NULL REFERENCES subjective_trace(id) ON DELETE RESTRICT,
    support_role TEXT NOT NULL CHECK (support_role IN ('primary', 'additional')),
    created_at TEXT NOT NULL,
    UNIQUE (episode_id, trace_id)
);

CREATE INDEX idx_autobiographical_episode_support_trace
    ON autobiographical_episode_support(world_id, character_id, trace_id, episode_id);

CREATE TABLE autobiographical_episode_event (
    id INTEGER PRIMARY KEY,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    episode_id INTEGER NOT NULL REFERENCES autobiographical_episode(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type = 'episode_formed'),
    payload_json TEXT NOT NULL CHECK (json_type(payload_json) = 'object'),
    recorded_at TEXT NOT NULL
);

CREATE TRIGGER autobiographical_episode_character_same_world
BEFORE INSERT ON autobiographical_episode
WHEN NOT EXISTS (
    SELECT 1 FROM character ch
    WHERE ch.id = NEW.character_id AND ch.world_id = NEW.world_id
)
BEGIN
    SELECT RAISE(ABORT, 'autobiographical episode character must be in same world');
END;

CREATE TRIGGER autobiographical_episode_no_update
BEFORE UPDATE ON autobiographical_episode
BEGIN
    SELECT RAISE(ABORT, 'autobiographical episode is immutable: UPDATE forbidden');
END;

CREATE TRIGGER autobiographical_episode_no_delete
BEFORE DELETE ON autobiographical_episode
BEGIN
    SELECT RAISE(ABORT, 'autobiographical episode is append-only: DELETE forbidden');
END;

CREATE TRIGGER autobiographical_episode_support_same_owner
BEFORE INSERT ON autobiographical_episode_support
WHEN NOT EXISTS (
    SELECT 1
    FROM autobiographical_episode episode
    JOIN subjective_trace trace ON trace.id = NEW.trace_id
    WHERE episode.id = NEW.episode_id
      AND episode.world_id = NEW.world_id
      AND episode.character_id = NEW.character_id
      AND trace.world_id = episode.world_id
      AND trace.character_id = episode.character_id
)
BEGIN
    SELECT RAISE(ABORT, 'autobiographical support must belong to its owner');
END;

CREATE TRIGGER autobiographical_episode_support_no_update
BEFORE UPDATE ON autobiographical_episode_support
BEGIN
    SELECT RAISE(ABORT, 'autobiographical episode support is append-only');
END;

CREATE TRIGGER autobiographical_episode_support_no_delete
BEFORE DELETE ON autobiographical_episode_support
BEGIN
    SELECT RAISE(ABORT, 'autobiographical episode support is append-only');
END;

CREATE TRIGGER autobiographical_episode_event_same_owner
BEFORE INSERT ON autobiographical_episode_event
WHEN NOT EXISTS (
    SELECT 1 FROM autobiographical_episode episode
    WHERE episode.id = NEW.episode_id
      AND episode.world_id = NEW.world_id
      AND episode.character_id = NEW.character_id
)
BEGIN
    SELECT RAISE(ABORT, 'autobiographical episode event must belong to holder');
END;

CREATE TRIGGER autobiographical_episode_event_no_update
BEFORE UPDATE ON autobiographical_episode_event
BEGIN
    SELECT RAISE(ABORT, 'autobiographical episode event is append-only');
END;

CREATE TRIGGER autobiographical_episode_event_no_delete
BEFORE DELETE ON autobiographical_episode_event
BEGIN
    SELECT RAISE(ABORT, 'autobiographical episode event is append-only');
END;
