-- SCC-1A : une preuve secondaire peut appartenir à toute famille de trace privée.

DROP TRIGGER social_interpretation_support_same_owner;

CREATE TRIGGER social_interpretation_support_same_owner
BEFORE INSERT ON social_interpretation_support
WHEN NOT EXISTS (
    SELECT 1
    FROM social_interpretation interpretation
    JOIN subjective_trace trace ON trace.id = NEW.trace_id
    WHERE interpretation.id = NEW.interpretation_id
      AND interpretation.world_id = trace.world_id
      AND interpretation.character_id = trace.character_id
      AND trace.id <> interpretation.source_trace_id
)
BEGIN
    SELECT RAISE(ABORT, 'interpretation support must be an additional owned trace');
END;
