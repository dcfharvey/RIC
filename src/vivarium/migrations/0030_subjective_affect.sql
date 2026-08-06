-- Etats affectifs privés. Ils ne sont pas des faits canoniques du monde.

CREATE TABLE mood_state (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    valence_milli INTEGER NOT NULL CHECK(valence_milli BETWEEN -1000 AND 1000),
    activation_milli INTEGER NOT NULL CHECK(activation_milli BETWEEN -1000 AND 1000),
    last_event_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(world_id, character_id)
);

CREATE TABLE mood_event (
    id INTEGER PRIMARY KEY,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    mood_id INTEGER NOT NULL REFERENCES mood_state(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK(event_type IN ('mood_initialized','mood_changed')),
    payload_json TEXT NOT NULL CHECK(json_type(payload_json)='object'),
    recorded_at TEXT NOT NULL
);

CREATE TRIGGER mood_state_character_same_world_insert
BEFORE INSERT ON mood_state
WHEN NOT EXISTS (SELECT 1 FROM character ch WHERE ch.id=NEW.character_id AND ch.world_id=NEW.world_id)
BEGIN SELECT RAISE(ABORT,'mood character must be in same world'); END;

CREATE TRIGGER mood_state_eventful_update
BEFORE UPDATE ON mood_state
WHEN NOT (
    NEW.public_id IS OLD.public_id AND NEW.world_id IS OLD.world_id AND NEW.character_id IS OLD.character_id
    AND NEW.created_at IS OLD.created_at AND NEW.last_event_id IS NOT NULL
    AND EXISTS (SELECT 1 FROM mood_event event WHERE event.id=NEW.last_event_id AND event.mood_id=OLD.id
                AND event.world_id=OLD.world_id AND event.character_id=OLD.character_id AND event.id>COALESCE(OLD.last_event_id,0))
)
BEGIN SELECT RAISE(ABORT,'mood update requires newer audit event'); END;

CREATE TRIGGER mood_state_no_delete BEFORE DELETE ON mood_state
BEGIN SELECT RAISE(ABORT,'mood state cannot be deleted'); END;
CREATE TRIGGER mood_event_same_owner BEFORE INSERT ON mood_event
WHEN NOT EXISTS (SELECT 1 FROM mood_state mood WHERE mood.id=NEW.mood_id AND mood.world_id=NEW.world_id AND mood.character_id=NEW.character_id)
BEGIN SELECT RAISE(ABORT,'mood event must belong to holder'); END;
CREATE TRIGGER mood_event_no_update BEFORE UPDATE ON mood_event
BEGIN SELECT RAISE(ABORT,'mood event is append-only'); END;
CREATE TRIGGER mood_event_no_delete BEFORE DELETE ON mood_event
BEGIN SELECT RAISE(ABORT,'mood event is append-only'); END;

CREATE TABLE emotion_episode (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    episode_key TEXT NOT NULL,
    family TEXT NOT NULL CHECK(family IN ('joy','relief','sadness','anger','fear','shame','guilt','affection')),
    target_character_id INTEGER REFERENCES character(id) ON DELETE SET NULL,
    appraisal_json TEXT NOT NULL CHECK(json_type(appraisal_json)='object'),
    cause_trace_id INTEGER NOT NULL REFERENCES subjective_trace(id) ON DELETE RESTRICT,
    intensity_milli INTEGER NOT NULL CHECK(intensity_milli BETWEEN 0 AND 1000),
    action_tendency TEXT NOT NULL,
    expression_milli INTEGER NOT NULL CHECK(expression_milli BETWEEN 0 AND 1000),
    status TEXT NOT NULL CHECK(status IN ('active','resolved','transformed')),
    last_event_id INTEGER,
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    UNIQUE(world_id, character_id, episode_key)
);

CREATE TABLE emotion_event (
    id INTEGER PRIMARY KEY,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    episode_id INTEGER NOT NULL REFERENCES emotion_episode(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK(event_type IN ('emotion_started','emotion_resolved')),
    payload_json TEXT NOT NULL CHECK(json_type(payload_json)='object'),
    recorded_at TEXT NOT NULL
);

CREATE TRIGGER emotion_episode_characters_same_world_insert
BEFORE INSERT ON emotion_episode
WHEN NOT EXISTS (SELECT 1 FROM character ch WHERE ch.id=NEW.character_id AND ch.world_id=NEW.world_id)
 OR (NEW.target_character_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM character target WHERE target.id=NEW.target_character_id AND target.world_id=NEW.world_id))
BEGIN SELECT RAISE(ABORT,'emotion characters must be in same world'); END;
CREATE TRIGGER emotion_episode_trace_same_owner_insert
BEFORE INSERT ON emotion_episode
WHEN NOT EXISTS (SELECT 1 FROM subjective_trace trace WHERE trace.id=NEW.cause_trace_id AND trace.world_id=NEW.world_id AND trace.character_id=NEW.character_id)
BEGIN SELECT RAISE(ABORT,'emotion cause must be an accessible private trace'); END;
CREATE TRIGGER emotion_episode_eventful_update
BEFORE UPDATE ON emotion_episode
WHEN NOT (
    NEW.public_id IS OLD.public_id AND NEW.world_id IS OLD.world_id AND NEW.character_id IS OLD.character_id
    AND NEW.episode_key IS OLD.episode_key AND NEW.family IS OLD.family AND NEW.target_character_id IS OLD.target_character_id
    AND NEW.appraisal_json IS OLD.appraisal_json AND NEW.cause_trace_id IS OLD.cause_trace_id
    AND NEW.intensity_milli IS OLD.intensity_milli AND NEW.action_tendency IS OLD.action_tendency
    AND NEW.expression_milli IS OLD.expression_milli AND NEW.created_at IS OLD.created_at
    AND NEW.last_event_id IS NOT NULL
    AND EXISTS (SELECT 1 FROM emotion_event event WHERE event.id=NEW.last_event_id AND event.episode_id=OLD.id
                AND event.world_id=OLD.world_id AND event.character_id=OLD.character_id AND event.id>COALESCE(OLD.last_event_id,0))
)
BEGIN SELECT RAISE(ABORT,'emotion update requires newer audit event'); END;
CREATE TRIGGER emotion_episode_no_delete BEFORE DELETE ON emotion_episode
BEGIN SELECT RAISE(ABORT,'emotion episode cannot be deleted'); END;
CREATE TRIGGER emotion_event_same_owner BEFORE INSERT ON emotion_event
WHEN NOT EXISTS (SELECT 1 FROM emotion_episode episode WHERE episode.id=NEW.episode_id AND episode.world_id=NEW.world_id AND episode.character_id=NEW.character_id)
BEGIN SELECT RAISE(ABORT,'emotion event must belong to holder'); END;
CREATE TRIGGER emotion_event_no_update BEFORE UPDATE ON emotion_event
BEGIN SELECT RAISE(ABORT,'emotion event is append-only'); END;
CREATE TRIGGER emotion_event_no_delete BEFORE DELETE ON emotion_event
BEGIN SELECT RAISE(ABORT,'emotion event is append-only'); END;
