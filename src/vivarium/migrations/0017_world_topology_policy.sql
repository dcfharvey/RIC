-- Politique topologique déclarée par monde.
-- Aucun nom de lieu (notamment « salon ») ne devient une loi du moteur.

CREATE TABLE world_topology_policy (
    world_id           INTEGER PRIMARY KEY REFERENCES worlds(id),
    policy_key         TEXT NOT NULL CHECK (policy_key IN ('none', 'strong_anchor')),
    anchor_location_id INTEGER,
    configured_at      TEXT NOT NULL,
    FOREIGN KEY (world_id, anchor_location_id) REFERENCES location(world_id, id),
    CHECK (
        (policy_key = 'none' AND anchor_location_id IS NULL)
        OR
        (policy_key = 'strong_anchor' AND anchor_location_id IS NOT NULL)
    )
);
