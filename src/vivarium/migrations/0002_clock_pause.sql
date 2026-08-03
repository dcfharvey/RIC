-- Migration 0002 : domaine du statut du monde (active | paused).
-- Contrainte appliquée par déclencheurs (sans reconstruire la table parente
-- `worlds`, référencée par des clés étrangères).

CREATE TRIGGER worlds_status_guard_insert
BEFORE INSERT ON worlds
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.status NOT IN ('active', 'paused')
        THEN RAISE(ABORT, 'statut de monde invalide')
    END;
END;

CREATE TRIGGER worlds_status_guard_update
BEFORE UPDATE OF status ON worlds
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.status NOT IN ('active', 'paused')
        THEN RAISE(ABORT, 'statut de monde invalide')
    END;
END;
