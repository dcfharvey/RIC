-- Migration 0008 : blessures de mobilité (Sous-lot 3.3B1).
-- État corporel persistant, causalité canonique, récupération entière /36.
-- AUCUNE colonne REAL. Une seule blessure active par personnage ; les blessures
-- guéries restent dans l'historique et sont terminales (immuables).

CREATE TABLE injury (
    id                 INTEGER PRIMARY KEY,
    public_id          TEXT NOT NULL UNIQUE,
    world_id           INTEGER NOT NULL,
    character_id       INTEGER NOT NULL,
    kind               TEXT NOT NULL CHECK (kind IN ('mobility')),
    status             TEXT NOT NULL,
    severity_milli     INTEGER NOT NULL CHECK (severity_milli BETWEEN 0 AND 100000),
    rate_remainder     INTEGER NOT NULL DEFAULT 0 CHECK (rate_remainder BETWEEN 0 AND 35),
    recovery_anchor_at TEXT NOT NULL,          -- heure simulée du dernier ancrage
    started_at         TEXT NOT NULL,          -- heure simulée canonique d'apparition
    recovered_at       TEXT,                  -- heure simulée exacte de guérison (NULL si active)
    cause_event_seq    INTEGER NOT NULL,
    created_at         TEXT NOT NULL,
    updated_at         TEXT NOT NULL,
    CHECK (
        (status = 'active' AND severity_milli > 0 AND recovered_at IS NULL)
        OR
        (status = 'healed' AND severity_milli = 0 AND recovered_at IS NOT NULL AND rate_remainder = 0)
    ),
    -- une cause canonique ne peut produire qu'une seule blessure (refus réutilisation)
    UNIQUE (world_id, cause_event_seq),
    FOREIGN KEY (world_id, character_id) REFERENCES character(world_id, id),
    FOREIGN KEY (world_id, cause_event_seq) REFERENCES canonical_event(world_id, seq)
);
CREATE UNIQUE INDEX injury_one_active
    ON injury(world_id, character_id) WHERE status = 'active';

-- Une blessure guérie est terminale : champs corporels essentiels immuables.
CREATE TRIGGER injury_healed_terminal
BEFORE UPDATE ON injury
WHEN OLD.status = 'healed' AND (
    NEW.status != OLD.status
    OR NEW.severity_milli != OLD.severity_milli
    OR NEW.rate_remainder != OLD.rate_remainder
    OR NEW.recovered_at IS NOT OLD.recovered_at
)
BEGIN
    SELECT RAISE(ABORT, 'healed injury is terminal: corporeal fields immutable');
END;

-- L'historique des blessures est immuable (pas de suppression).
CREATE TRIGGER injury_no_delete
BEFORE DELETE ON injury
BEGIN
    SELECT RAISE(ABORT, 'injury is immutable: DELETE forbidden');
END;
