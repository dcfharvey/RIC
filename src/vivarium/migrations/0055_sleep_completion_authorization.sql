-- Autorisation privee et consommable pour la completion d'un sommeil de checkpoint.
-- Cette preuve ne constitue ni un evenement canonique ni un second owner du sommeil :
-- SleepTermination valide la decision, ActivityEngine reste seul owner de la mutation.

CREATE TABLE sleep_completion_authorization (
    id INTEGER PRIMARY KEY,
    public_id TEXT NOT NULL UNIQUE,
    world_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    activity_id INTEGER NOT NULL REFERENCES activity(id) ON DELETE RESTRICT,
    checkpoint_id INTEGER NOT NULL REFERENCES activity_sleep_checkpoint(id) ON DELETE RESTRICT,
    policy_id INTEGER NOT NULL REFERENCES sleep_termination_policy(id) ON DELETE RESTRICT,
    boundary_at TEXT NOT NULL,
    evaluation_json TEXT NOT NULL CHECK (json_type(evaluation_json) = 'object'),
    authorized_at TEXT NOT NULL,
    consumed_event_id INTEGER REFERENCES canonical_event(id) ON DELETE RESTRICT,
    consumed_at TEXT,
    UNIQUE (checkpoint_id, boundary_at),
    FOREIGN KEY(world_id, character_id) REFERENCES character(world_id, id),
    CHECK ((consumed_event_id IS NULL) = (consumed_at IS NULL))
);

-- L'autorisation doit viser exactement l'episode, le checkpoint et la politique
-- actuellement attaches au meme owner, a une frontiere admissible du checkpoint.
CREATE TRIGGER sleep_completion_authorization_matches_checkpoint
BEFORE INSERT ON sleep_completion_authorization
WHEN NOT EXISTS (
    SELECT 1
    FROM activity_sleep_checkpoint cp
    JOIN activity a ON a.id = cp.activity_id
    WHERE cp.id = NEW.checkpoint_id
      AND cp.world_id = NEW.world_id
      AND cp.character_id = NEW.character_id
      AND cp.activity_id = NEW.activity_id
      AND cp.policy_id = NEW.policy_id
      AND a.world_id = NEW.world_id
      AND a.character_id = NEW.character_id
      AND a.type = 'sleep'
      AND a.status = 'active'
      AND NEW.boundary_at >= cp.next_reassessment_at
      AND NEW.boundary_at <= cp.hard_cap_at
)
BEGIN SELECT RAISE(ABORT, 'sleep completion authorization checkpoint mismatch'); END;

CREATE TRIGGER sleep_completion_authorization_no_delete
BEFORE DELETE ON sleep_completion_authorization
BEGIN SELECT RAISE(ABORT, 'sleep completion authorization is append-only'); END;

-- Seule la consommation atomique par l'evenement canonique peut modifier la preuve.
CREATE TRIGGER sleep_completion_authorization_identity_immutable
BEFORE UPDATE ON sleep_completion_authorization
WHEN NEW.public_id <> OLD.public_id
  OR NEW.world_id <> OLD.world_id
  OR NEW.character_id <> OLD.character_id
  OR NEW.activity_id <> OLD.activity_id
  OR NEW.checkpoint_id <> OLD.checkpoint_id
  OR NEW.policy_id <> OLD.policy_id
  OR NEW.boundary_at <> OLD.boundary_at
  OR NEW.evaluation_json <> OLD.evaluation_json
  OR NEW.authorized_at <> OLD.authorized_at
  OR OLD.consumed_event_id IS NOT NULL
  OR NEW.consumed_event_id IS NULL
  OR NEW.consumed_at IS NULL
BEGIN SELECT RAISE(ABORT, 'sleep completion authorization is immutable'); END;

-- Une completion issue de complete_sleep_from_checkpoint doit posseder une preuve
-- non consommee pour le meme personnage, le meme episode et exactement la meme
-- frontiere. Si cette insertion echoue, la transaction ActivityEngine est rollbackee
-- avec son UPDATE d'activite : aucune mutation canonique partielle n'est possible.
CREATE TRIGGER canonical_sleep_checkpoint_completion_requires_authorization
BEFORE INSERT ON canonical_event
WHEN NEW.event_type = 'activity_completed'
 AND json_extract(NEW.payload, '$.activity') = 'sleep'
 AND json_extract(NEW.payload, '$.reason_code') = 'sleep_checkpoint'
 AND NOT EXISTS (
    SELECT 1
    FROM sleep_completion_authorization auth
    JOIN character ch
      ON ch.world_id = auth.world_id AND ch.id = auth.character_id
    JOIN activity a
      ON a.id = auth.activity_id
    WHERE auth.world_id = NEW.world_id
      AND ch.key = json_extract(NEW.payload, '$.character')
      AND a.world_id = auth.world_id
      AND a.character_id = auth.character_id
      AND a.type = 'sleep'
      AND a.status = 'completed'
      AND auth.boundary_at = NEW.occurred_at
      AND auth.consumed_event_id IS NULL
 )
BEGIN SELECT RAISE(ABORT, 'sleep checkpoint completion requires authorization'); END;

-- La preuve est consommee dans la meme transaction que l'evenement append-only.
CREATE TRIGGER canonical_sleep_checkpoint_completion_consumes_authorization
AFTER INSERT ON canonical_event
WHEN NEW.event_type = 'activity_completed'
 AND json_extract(NEW.payload, '$.activity') = 'sleep'
 AND json_extract(NEW.payload, '$.reason_code') = 'sleep_checkpoint'
BEGIN
    UPDATE sleep_completion_authorization
    SET consumed_event_id = NEW.id,
        consumed_at = NEW.recorded_at
    WHERE id = (
        SELECT auth.id
        FROM sleep_completion_authorization auth
        JOIN character ch
          ON ch.world_id = auth.world_id AND ch.id = auth.character_id
        JOIN activity a
          ON a.id = auth.activity_id
        WHERE auth.world_id = NEW.world_id
          AND ch.key = json_extract(NEW.payload, '$.character')
          AND a.world_id = auth.world_id
          AND a.character_id = auth.character_id
          AND a.type = 'sleep'
          AND a.status = 'completed'
          AND auth.boundary_at = NEW.occurred_at
          AND auth.consumed_event_id IS NULL
        ORDER BY auth.id DESC
        LIMIT 1
    );
END;
