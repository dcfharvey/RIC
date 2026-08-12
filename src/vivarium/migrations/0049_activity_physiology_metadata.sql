-- Métadonnées inactives de compatibilité pour le futur cutover circadien.
-- Elles ne sont lues par aucun chemin runtime dans ce lot et ne créent aucun
-- événement canonique. Les activités inconnues restent explicitement non
-- classées afin qu'un futur préflight de monde actif puisse les refuser.

ALTER TABLE activity_definition
ADD COLUMN requires_sustained_wakefulness INTEGER
CHECK (requires_sustained_wakefulness IN (0, 1));

ALTER TABLE activity_definition
ADD COLUMN physical_load_class TEXT
CHECK (physical_load_class IN ('none', 'light', 'moderate', 'vigorous'));

-- Classification V1 approuvée. `physical_load_class` reste NULL : ses
-- classes et coûts relèvent encore de la calibration/politique versionnée.
UPDATE activity_definition
SET requires_sustained_wakefulness = CASE activity_type
    WHEN 'sleep' THEN 0
    WHEN 'rest' THEN 0
    WHEN 'idle' THEN 0
    WHEN 'eat' THEN 1
    WHEN 'clean' THEN 1
    WHEN 'gaming' THEN 1
    WHEN 'photography' THEN 1
    WHEN 'sport' THEN 1
    WHEN 'girly_care' THEN 1
    WHEN 'socialize' THEN 1
    WHEN 'watch_tv' THEN 1
END
WHERE activity_type IN (
    'sleep', 'rest', 'idle', 'eat', 'clean', 'gaming', 'photography',
    'sport', 'girly_care', 'socialize', 'watch_tv'
);
