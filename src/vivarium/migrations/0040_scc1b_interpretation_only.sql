-- SCC-1B: le contrat actif est désormais interpretation-only.
-- Les anciennes sorties de motif restent conservées sous un nom explicitement
-- legacy pour préserver l'archive forensic, sans être lues par le runtime.
ALTER TABLE social_interpretation
RENAME COLUMN motive_hypotheses_json TO legacy_motive_hypotheses_json;
