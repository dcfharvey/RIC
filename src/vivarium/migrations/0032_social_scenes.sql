-- Scènes sociales et actes de parole : journal local, hors vérité canonique.

CREATE TABLE social_scene (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    scene_key TEXT NOT NULL,
    location_id INTEGER NOT NULL REFERENCES location(id) ON DELETE RESTRICT,
    status TEXT NOT NULL CHECK(status IN ('active','closed','interrupted')),
    opened_at TEXT NOT NULL,
    closed_at TEXT,
    close_reason TEXT,
    UNIQUE(world_id, scene_key)
);
CREATE TABLE social_scene_participant (
    id INTEGER PRIMARY KEY,
    scene_id INTEGER NOT NULL REFERENCES social_scene(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    joined_at TEXT NOT NULL,
    UNIQUE(scene_id, character_id)
);
CREATE TABLE social_speech_act (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    scene_id INTEGER NOT NULL REFERENCES social_scene(id) ON DELETE CASCADE,
    speaker_character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    recipient_character_id INTEGER REFERENCES character(id) ON DELETE SET NULL,
    act_key TEXT NOT NULL,
    act_kind TEXT NOT NULL CHECK(act_kind IN ('greet','ask','answer','inform','offer','decline','apologize','acknowledge','leave')),
    content_text TEXT NOT NULL CHECK(length(content_text) BETWEEN 1 AND 1200),
    payload_json TEXT NOT NULL CHECK(json_type(payload_json)='object'),
    spoken_at TEXT NOT NULL,
    UNIQUE(scene_id, act_key)
);
CREATE TABLE social_scene_event (
    id INTEGER PRIMARY KEY,
    scene_id INTEGER NOT NULL REFERENCES social_scene(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK(event_type IN ('scene_opened','speech_recorded','scene_closed','scene_interrupted')),
    payload_json TEXT NOT NULL CHECK(json_type(payload_json)='object'),
    recorded_at TEXT NOT NULL
);
CREATE TRIGGER social_scene_no_delete BEFORE DELETE ON social_scene BEGIN SELECT RAISE(ABORT,'social scene cannot be deleted'); END;
CREATE TRIGGER social_scene_participant_no_update BEFORE UPDATE ON social_scene_participant BEGIN SELECT RAISE(ABORT,'scene participant is append-only'); END;
CREATE TRIGGER social_scene_participant_no_delete BEFORE DELETE ON social_scene_participant BEGIN SELECT RAISE(ABORT,'scene participant is append-only'); END;
CREATE TRIGGER social_speech_act_no_update BEFORE UPDATE ON social_speech_act BEGIN SELECT RAISE(ABORT,'speech act is append-only'); END;
CREATE TRIGGER social_speech_act_no_delete BEFORE DELETE ON social_speech_act BEGIN SELECT RAISE(ABORT,'speech act is append-only'); END;
CREATE TRIGGER social_scene_event_no_update BEFORE UPDATE ON social_scene_event BEGIN SELECT RAISE(ABORT,'scene event is append-only'); END;
CREATE TRIGGER social_scene_event_no_delete BEFORE DELETE ON social_scene_event BEGIN SELECT RAISE(ABORT,'scene event is append-only'); END;
