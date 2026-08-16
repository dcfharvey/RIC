-- P0 : chaîne append-only des représentations autobiographiques.

CREATE TABLE autobiographical_episode_revision (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    request_key TEXT NOT NULL,
    predecessor_episode_id INTEGER NOT NULL REFERENCES autobiographical_episode(id) ON DELETE CASCADE,
    successor_episode_id INTEGER NOT NULL REFERENCES autobiographical_episode(id) ON DELETE CASCADE,
    reason_code TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (world_id, character_id, request_key),
    UNIQUE (predecessor_episode_id),
    UNIQUE (successor_episode_id),
    CHECK (predecessor_episode_id <> successor_episode_id)
);

CREATE INDEX idx_autobiographical_episode_revision_owner_time
    ON autobiographical_episode_revision(world_id, character_id, id DESC);

CREATE TRIGGER autobiographical_episode_revision_same_owner
BEFORE INSERT ON autobiographical_episode_revision
WHEN NOT EXISTS (
    SELECT 1
    FROM autobiographical_episode predecessor
    JOIN autobiographical_episode successor
      ON successor.id = NEW.successor_episode_id
    WHERE predecessor.id = NEW.predecessor_episode_id
      AND predecessor.world_id = NEW.world_id
      AND predecessor.character_id = NEW.character_id
      AND successor.world_id = NEW.world_id
      AND successor.character_id = NEW.character_id
)
BEGIN
    SELECT RAISE(ABORT, 'autobiographical revision must stay owner-scoped');
END;

CREATE TRIGGER autobiographical_episode_revision_no_cycle
BEFORE INSERT ON autobiographical_episode_revision
WHEN EXISTS (
    WITH RECURSIVE successors(episode_id) AS (
        SELECT NEW.successor_episode_id
        UNION ALL
        SELECT revision.successor_episode_id
        FROM autobiographical_episode_revision revision
        JOIN successors
          ON revision.predecessor_episode_id = successors.episode_id
    )
    SELECT 1 FROM successors WHERE episode_id = NEW.predecessor_episode_id
)
BEGIN
    SELECT RAISE(ABORT, 'autobiographical revision cycle forbidden');
END;

CREATE TRIGGER autobiographical_episode_revision_no_update
BEFORE UPDATE ON autobiographical_episode_revision
BEGIN
    SELECT RAISE(ABORT, 'autobiographical revision is append-only: UPDATE forbidden');
END;

CREATE TRIGGER autobiographical_episode_revision_no_delete
BEFORE DELETE ON autobiographical_episode_revision
BEGIN
    SELECT RAISE(ABORT, 'autobiographical revision is append-only: DELETE forbidden');
END;

CREATE TABLE autobiographical_episode_revision_support (
    id INTEGER PRIMARY KEY,
    world_id INTEGER NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    character_id INTEGER NOT NULL REFERENCES character(id) ON DELETE CASCADE,
    revision_id INTEGER NOT NULL REFERENCES autobiographical_episode_revision(id) ON DELETE CASCADE,
    trace_id INTEGER NOT NULL REFERENCES subjective_trace(id) ON DELETE RESTRICT,
    support_origin TEXT NOT NULL CHECK (support_origin IN ('inherited', 'new')),
    created_at TEXT NOT NULL,
    UNIQUE (revision_id, trace_id)
);

CREATE INDEX idx_autobiographical_episode_revision_support_revision
    ON autobiographical_episode_revision_support(revision_id, id);

CREATE TRIGGER autobiographical_episode_revision_support_same_owner
BEFORE INSERT ON autobiographical_episode_revision_support
WHEN NOT EXISTS (
    SELECT 1
    FROM autobiographical_episode_revision revision
    JOIN subjective_trace trace ON trace.id = NEW.trace_id
    JOIN autobiographical_episode_support successor_support
      ON successor_support.episode_id = revision.successor_episode_id
     AND successor_support.trace_id = trace.id
    WHERE revision.id = NEW.revision_id
      AND revision.world_id = NEW.world_id
      AND revision.character_id = NEW.character_id
      AND trace.world_id = NEW.world_id
      AND trace.character_id = NEW.character_id
)
BEGIN
    SELECT RAISE(ABORT, 'autobiographical revision support must belong to its owner');
END;

CREATE TRIGGER autobiographical_episode_revision_support_no_update
BEFORE UPDATE ON autobiographical_episode_revision_support
BEGIN
    SELECT RAISE(ABORT, 'autobiographical revision support is append-only: UPDATE forbidden');
END;

CREATE TRIGGER autobiographical_episode_revision_support_no_delete
BEFORE DELETE ON autobiographical_episode_revision_support
BEGIN
    SELECT RAISE(ABORT, 'autobiographical revision support is append-only: DELETE forbidden');
END;
