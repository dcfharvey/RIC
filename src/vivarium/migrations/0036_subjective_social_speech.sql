-- SCC-0 : une trace subjective peut référencer un acte de parole social accepté.

ALTER TABLE subjective_trace
ADD COLUMN source_social_speech_act_id INTEGER
REFERENCES social_speech_act(id) ON DELETE RESTRICT;

CREATE UNIQUE INDEX idx_subjective_trace_social_speech_once
ON subjective_trace(world_id, character_id, source_social_speech_act_id)
WHERE source_social_speech_act_id IS NOT NULL;

CREATE INDEX idx_subjective_trace_social_speech_source
ON subjective_trace(world_id, source_social_speech_act_id);

CREATE TRIGGER subjective_trace_social_speech_same_world_insert
BEFORE INSERT ON subjective_trace
WHEN NEW.source_social_speech_act_id IS NOT NULL
 AND NOT EXISTS (
     SELECT 1
     FROM social_speech_act act
     JOIN social_scene scene ON scene.id = act.scene_id
     WHERE act.id = NEW.source_social_speech_act_id
       AND scene.world_id = NEW.world_id
 )
BEGIN
    SELECT RAISE(ABORT, 'subjective social speech source must be in same world');
END;
