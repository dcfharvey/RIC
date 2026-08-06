-- Migration 0013 : effets déclaratifs attachés aux bandes de ressource.
CREATE TABLE resource_state_effect (
    id INTEGER PRIMARY KEY,
    resource_state_band_id INTEGER NOT NULL REFERENCES resource_state_band(id),
    effect_type TEXT NOT NULL CHECK (effect_type IN ('capability_availability', 'context_signal')),
    effect_key TEXT NOT NULL,
    availability TEXT CHECK (availability IN ('available', 'limited', 'unavailable')),
    value_milli INTEGER CHECK (value_milli BETWEEN -100000 AND 100000),
    CHECK (
        (effect_type = 'capability_availability' AND availability IS NOT NULL AND value_milli IS NULL)
        OR
        (effect_type = 'context_signal' AND availability IS NULL AND value_milli IS NOT NULL)
    ),
    UNIQUE (resource_state_band_id, effect_type, effect_key)
);

CREATE TRIGGER resource_state_effect_immutable
BEFORE UPDATE ON resource_state_effect
BEGIN
    SELECT RAISE(ABORT, 'resource state effects are immutable');
END;
