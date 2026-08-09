-- SCC-1B1 : provenance technique sur le propriétaire SCC-1A existant.
ALTER TABLE social_interpretation ADD COLUMN origin_kind TEXT NOT NULL DEFAULT 'direct_controlled'
    CHECK (origin_kind IN ('llm', 'direct_controlled'));
ALTER TABLE social_interpretation ADD COLUMN model_id TEXT;
ALTER TABLE social_interpretation ADD COLUMN provider_version TEXT;
ALTER TABLE social_interpretation ADD COLUMN snapshot_fingerprint TEXT;
ALTER TABLE social_interpretation ADD COLUMN provider_turn_id TEXT;
CREATE INDEX idx_social_interpretation_snapshot_fingerprint
    ON social_interpretation(world_id, character_id, snapshot_fingerprint);
