-- Durcissements d'integrite des fondations de terminaison de sommeil.
-- Cette migration ne cree aucun checkpoint, ne touche pas les activites et ne
-- produit aucun evenement canonique.

CREATE TRIGGER activity_sleep_checkpoint_identity_immutable
BEFORE UPDATE ON activity_sleep_checkpoint
WHEN NEW.public_id IS NOT OLD.public_id
  OR NEW.world_id IS NOT OLD.world_id
  OR NEW.character_id IS NOT OLD.character_id
  OR NEW.activity_id IS NOT OLD.activity_id
  OR NEW.policy_id IS NOT OLD.policy_id
  OR NEW.hard_cap_at IS NOT OLD.hard_cap_at
  OR NEW.created_at IS NOT OLD.created_at
BEGIN SELECT RAISE(ABORT, 'activity sleep checkpoint identity is immutable'); END;

CREATE TRIGGER sleep_termination_audit_matches_checkpoint
BEFORE INSERT ON sleep_termination_audit
WHEN NOT EXISTS (
    SELECT 1 FROM activity_sleep_checkpoint
    WHERE id = NEW.checkpoint_id
      AND world_id = NEW.world_id
      AND character_id = NEW.character_id
      AND activity_id = NEW.activity_id
)
BEGIN SELECT RAISE(ABORT, 'sleep termination audit checkpoint mismatch'); END;
