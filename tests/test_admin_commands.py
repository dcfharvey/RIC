"""Tests de la Phase 4.1B — commandes administratives sûres (AdminCommandService).

Vérifie : pause/resume/rename/move (succès et refus), dispatcher fermé, format
stable, validation des paramètres, traduction des erreurs, absence de mutation
et d'événement lors des refus.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest

from vivarium.activities import ActivityEngine
from vivarium.admin import AdminCommandService
from vivarium.character import CharacterEngine
from vivarium.db import connect_database
from vivarium.injury import InjuryEngine
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest, max_seq
from vivarium.util import to_iso
from vivarium.world import WorldEngine

T0 = datetime(2026, 8, 1, 8, 0, 0, tzinfo=timezone.utc)


class FakeClock:
    def __init__(self, start=T0):
        self._now = start

    def now(self):
        return self._now

    def now_iso(self):
        return to_iso(self.now())

    def advance(self, **kw):
        self._now = self._now + timedelta(**kw)


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    wid = WorldEngine(conn, clock=clock).init_world(name="Admin")["id"]
    return conn, clock, wid


def _svc(conn, clock):
    return AdminCommandService(conn, clock=clock)


def _events(conn, wid, etype):
    return conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type = ?",
        (wid, etype),
    ).fetchone()[0]


def _move_to(conn, clock, wid, char, target):
    from vivarium.spatial import GraphEngine
    ce = CharacterEngine(conn, clock=clock)
    cur = ce.character_sheet(wid, char)["location_key"]
    if cur == target:
        return
    for step in GraphEngine(conn).find_path(wid, cur, target)[1:]:
        ce.move_character(wid, char, step)


# --- Pause / reprise ---------------------------------------------------------

def test_pause_valide(setup):
    conn, clock, wid = setup
    r = _svc(conn, clock).pause(wid)
    assert r["ok"] is True and r["command"] == "pause" and r["error"] is None
    assert r["data"]["status"] == "paused"
    assert _events(conn, wid, "world_paused") == 1


def test_pause_repetee(setup):
    conn, clock, wid = setup
    _svc(conn, clock).pause(wid)
    before = _events(conn, wid, "world_paused")
    r = _svc(conn, clock).pause(wid)
    assert r["ok"] is False and r["error"]["code"] == "already_paused"
    assert _events(conn, wid, "world_paused") == before


def test_resume_valide(setup):
    conn, clock, wid = setup
    _svc(conn, clock).pause(wid)
    r = _svc(conn, clock).resume(wid)
    assert r["ok"] is True and r["data"]["status"] == "active"
    assert _events(conn, wid, "world_resumed") == 1


def test_resume_repetee(setup):
    conn, clock, wid = setup
    r = _svc(conn, clock).resume(wid)
    assert r["ok"] is False and r["error"]["code"] == "already_active"


# --- Renommage ---------------------------------------------------------------

def test_rename_valide_normalise(setup):
    conn, clock, wid = setup
    r = _svc(conn, clock).rename(wid, "  Nouveau  ")
    assert r["ok"] is True
    assert r["data"]["name"] == "Nouveau"


def test_rename_invalide(setup):
    conn, clock, wid = setup
    before = max_seq(conn, wid)
    r = _svc(conn, clock).rename(wid, "   ")
    assert r["ok"] is False and r["error"]["code"] == "invalid_name"
    assert max_seq(conn, wid) == before


# --- Déplacement -------------------------------------------------------------

def test_move_valide(setup):
    conn, clock, wid = setup
    r = _svc(conn, clock).move(wid, "character_1", "couloir")
    assert r["ok"] is True
    assert r["data"]["character"] == "character_1"
    assert r["data"]["from"] == "chambre_1"
    assert r["data"]["to"] == "couloir"
    assert r["data"]["energy_cost"] == 0


def test_move_personnage_inexistant(setup):
    conn, clock, wid = setup
    r = _svc(conn, clock).move(wid, "ghost", "couloir")
    assert r["ok"] is False and r["error"]["code"] == "character_not_found"


def test_move_monde_inexistant(setup):
    conn, clock, wid = setup
    r = _svc(conn, clock).move(9999, "character_1", "couloir")
    assert r["ok"] is False and r["error"]["code"] == "world_not_found"


def test_move_destination_inexistante(setup):
    conn, clock, wid = setup
    r = _svc(conn, clock).move(wid, "character_1", "ghost_location")
    assert r["ok"] is False and r["error"]["code"] == "destination_not_found"


def test_move_destination_inaccessible(setup):
    conn, clock, wid = setup
    # chambre_1 → cuisine n'est pas une arête directe
    r = _svc(conn, clock).move(wid, "character_1", "cuisine")
    assert r["ok"] is False and r["error"]["code"] == "invalid_destination"


def test_move_energie_insuffisante(setup):
    conn, clock, wid = setup
    ce = CharacterEngine(conn, clock=clock)
    ie = InjuryEngine(conn, clock=clock)
    _move_to(conn, clock, wid, "character_1", "salon")
    ie.inflict_injury(wid, "character_1", 40000)  # moderate
    conn.execute(
        "UPDATE need_state SET value_milli = 499, rate_remainder = 0, anchor_at = ? "
        "WHERE world_id = ? AND need_key = 'energie' AND character_id = "
        "(SELECT id FROM character WHERE world_id = ? AND key = 'character_1')",
        (to_iso(T0), wid, wid),
    )
    r = _svc(conn, clock).move(wid, "character_1", "cuisine")
    assert r["ok"] is False and r["error"]["code"] == "insufficient_energy"


def test_move_activite_active(setup):
    conn, clock, wid = setup
    ce = CharacterEngine(conn, clock=clock)
    ae = ActivityEngine(conn, clock=clock)
    _move_to(conn, clock, wid, "character_1", "cuisine")
    ae.start_activity(wid, "character_1", "eat", "cuisine", sim_now=to_iso(T0))
    r = _svc(conn, clock).move(wid, "character_1", "salon")
    assert r["ok"] is False and r["error"]["code"] == "activity_active"


def test_move_blessure_severe(setup):
    conn, clock, wid = setup
    ce = CharacterEngine(conn, clock=clock)
    ie = InjuryEngine(conn, clock=clock)
    _move_to(conn, clock, wid, "character_1", "salon")
    ie.inflict_injury(wid, "character_1", 70000)  # severe
    r = _svc(conn, clock).move(wid, "character_1", "cuisine")
    assert r["ok"] is False and r["error"]["code"] == "injury_severe"


def test_move_monde_paused(setup):
    conn, clock, wid = setup
    WorldEngine(conn, clock=clock).pause_world(wid)
    r = _svc(conn, clock).move(wid, "character_1", "couloir")
    assert r["ok"] is False and r["error"]["code"] == "world_paused"


# --- Paramètres --------------------------------------------------------------

def test_parametres_absents(setup):
    conn, clock, wid = setup
    r = _svc(conn, clock).execute("pause", {})
    assert r["ok"] is False and r["error"]["code"] == "invalid_parameters"


def test_world_id_bool_refuse(setup):
    conn, clock, wid = setup
    r = _svc(conn, clock).execute("pause", {"world_id": True})
    assert r["ok"] is False and r["error"]["code"] == "invalid_parameters"


def test_world_id_chaine_refuse(setup):
    conn, clock, wid = setup
    r = _svc(conn, clock).execute("pause", {"world_id": "1"})
    assert r["ok"] is False and r["error"]["code"] == "invalid_parameters"


def test_commande_inconnue(setup):
    conn, clock, wid = setup
    r = _svc(conn, clock).execute("teleport", {"world_id": wid})
    assert r["ok"] is False and r["error"]["code"] == "unknown_command"


def test_reponses_json_serialisables(setup):
    conn, clock, wid = setup
    for r in (
        _svc(conn, clock).pause(wid),
        _svc(conn, clock).rename(wid, "X"),
        _svc(conn, clock).move(wid, "character_1", "couloir"),
        _svc(conn, clock).execute("bogus", {}),
    ):
        json.dumps(r)  # ne doit pas lever


# --- Absence de mutation / événement lors des refus --------------------------

def _snapshot(conn, wid):
    """Capture l'état canonique pertinent pour vérifier l'absence de mutation."""
    world = conn.execute(
        "SELECT name, status FROM worlds WHERE id = ?", (wid,)
    ).fetchone()
    clock = conn.execute(
        "SELECT simulated_now, real_updated_at FROM canonical_clock WHERE world_id = ?",
        (wid,),
    ).fetchone()
    chars = {
        r["key"]: r["loc"]
        for r in conn.execute(
            "SELECT ch.key, l.key AS loc FROM character ch "
            "JOIN location l ON l.id = ch.current_location_id WHERE ch.world_id = ?",
            (wid,),
        ).fetchall()
    }
    energy = {
        r["key"]: r["value_milli"]
        for r in conn.execute(
            "SELECT ch.key, ns.value_milli FROM need_state ns "
            "JOIN character ch ON ch.id = ns.character_id "
            "WHERE ns.world_id = ? AND ns.need_key = 'energie'",
            (wid,),
        ).fetchall()
    }
    return {
        "world": dict(world),
        "clock": dict(clock),
        "chars": chars,
        "energy": energy,
        "activities": conn.execute(
            "SELECT COUNT(*) FROM activity WHERE world_id = ?", (wid,)
        ).fetchone()[0],
        "injuries": conn.execute(
            "SELECT COUNT(*) FROM injury WHERE world_id = ?", (wid,)
        ).fetchone()[0],
        "events": conn.execute(
            "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
        ).fetchone()[0],
        "max_seq": max_seq(conn, wid),
        "digest": canonical_state_digest(conn, wid),
    }


def _scenario_already_paused(conn, clock, wid, svc, mp):
    svc.pause(wid)
    return lambda: svc.pause(wid)


def _scenario_already_active(conn, clock, wid, svc, mp):
    svc.pause(wid)
    svc.resume(wid)
    return lambda: svc.resume(wid)


def _scenario_invalid_name(conn, clock, wid, svc, mp):
    return lambda: svc.rename(wid, "   ")


def _scenario_world_not_found(conn, clock, wid, svc, mp):
    return lambda: svc.pause(9999)


def _scenario_character_not_found(conn, clock, wid, svc, mp):
    return lambda: svc.move(wid, "ghost", "couloir")


def _scenario_destination_not_found(conn, clock, wid, svc, mp):
    return lambda: svc.move(wid, "character_1", "ghost_location")


def _scenario_invalid_destination(conn, clock, wid, svc, mp):
    return lambda: svc.move(wid, "character_1", "cuisine")


def _scenario_activity_active(conn, clock, wid, svc, mp):
    ae = ActivityEngine(conn, clock=clock)
    _move_to(conn, clock, wid, "character_1", "cuisine")
    ae.start_activity(wid, "character_1", "eat", "cuisine", sim_now=to_iso(T0))
    return lambda: svc.move(wid, "character_1", "salon")


def _scenario_injury_severe(conn, clock, wid, svc, mp):
    ie = InjuryEngine(conn, clock=clock)
    _move_to(conn, clock, wid, "character_1", "salon")
    ie.inflict_injury(wid, "character_1", 70000)
    return lambda: svc.move(wid, "character_1", "cuisine")


def _scenario_insufficient_energy(conn, clock, wid, svc, mp):
    ie = InjuryEngine(conn, clock=clock)
    _move_to(conn, clock, wid, "character_1", "salon")
    ie.inflict_injury(wid, "character_1", 40000)
    conn.execute(
        "UPDATE need_state SET value_milli = 499, rate_remainder = 0, anchor_at = ? "
        "WHERE world_id = ? AND need_key = 'energie' AND character_id = "
        "(SELECT id FROM character WHERE world_id = ? AND key = 'character_1')",
        (to_iso(T0), wid, wid),
    )
    return lambda: svc.move(wid, "character_1", "cuisine")


def _scenario_world_paused(conn, clock, wid, svc, mp):
    WorldEngine(conn, clock=clock).pause_world(wid)
    return lambda: svc.move(wid, "character_1", "couloir")


def _scenario_invalid_parameters(conn, clock, wid, svc, mp):
    return lambda: svc.execute("pause", {"world_id": "x"})


def _scenario_unknown_command(conn, clock, wid, svc, mp):
    return lambda: svc.execute("teleport", {"world_id": wid})


def _scenario_internal(conn, clock, wid, svc, mp):
    from vivarium.needs import NeedsEngine

    def boom(self, world_id, character_key, target_at, reason, *, _conn=None):
        raise RuntimeError(
            "SECRET /path/to/secret.db line 42 sql=SELECT * FROM secret_table"
        )
    mp.setattr(NeedsEngine, "materialize_character_needs", boom)
    return lambda: svc.pause(wid)


REFUSAL_SCENARIOS = [
    pytest.param(_scenario_already_paused, id="already_paused"),
    pytest.param(_scenario_already_active, id="already_active"),
    pytest.param(_scenario_invalid_name, id="invalid_name"),
    pytest.param(_scenario_world_not_found, id="world_not_found"),
    pytest.param(_scenario_character_not_found, id="character_not_found"),
    pytest.param(_scenario_destination_not_found, id="destination_not_found"),
    pytest.param(_scenario_invalid_destination, id="invalid_destination"),
    pytest.param(_scenario_activity_active, id="activity_active"),
    pytest.param(_scenario_injury_severe, id="injury_severe"),
    pytest.param(_scenario_insufficient_energy, id="insufficient_energy"),
    pytest.param(_scenario_world_paused, id="world_paused"),
    pytest.param(_scenario_invalid_parameters, id="invalid_parameters"),
    pytest.param(_scenario_unknown_command, id="unknown_command"),
    pytest.param(_scenario_internal, id="internal"),
]


@pytest.mark.parametrize("scenario", REFUSAL_SCENARIOS)
def test_refus_aucune_mutation_ni_evenement(scenario, setup, monkeypatch):
    """Chaque refus métier ne produit aucune mutation ni aucun événement."""
    conn, clock, wid = setup
    svc = _svc(conn, clock)
    command = scenario(conn, clock, wid, svc, monkeypatch)
    before = _snapshot(conn, wid)
    r = command()
    assert r["ok"] is False
    assert r["data"] is None
    assert _snapshot(conn, wid) == before


def test_exception_inattendue_masquee_internal(setup, monkeypatch):
    """Une exception inattendue dans une commande est masquée en `internal`.

    L'exception est levée à l'intérieur de la transaction de pause (pendant la
    matérialisation des besoins) : on vérifie le masquage, l'absence de fuite,
    le rollback complet et la réutilisabilité de la connexion.
    """
    from vivarium.needs import NeedsEngine

    conn, clock, wid = setup
    svc = _svc(conn, clock)
    before = _snapshot(conn, wid)

    def boom(self, world_id, character_key, target_at, reason, *, _conn=None):
        raise RuntimeError(
            "SECRET /path/to/secret.db line 42 sql=SELECT * FROM secret_table"
        )
    monkeypatch.setattr(NeedsEngine, "materialize_character_needs", boom)

    r = svc.pause(wid)
    # structure exacte
    assert set(r.keys()) == {"ok", "command", "data", "error"}
    assert r["ok"] is False
    assert r["command"] == "pause"
    assert r["data"] is None
    assert r["error"]["code"] == "internal"
    assert r["error"]["message"] == "Erreur interne."
    # aucune fuite de détail sensible
    raw = json.dumps(r)
    assert "SECRET" not in raw
    assert "secret.db" not in raw
    assert "secret_table" not in raw
    assert "Traceback" not in raw
    # aucune mutation / événement (rollback complet)
    assert _snapshot(conn, wid) == before
    # aucune transaction ouverte restante
    assert conn.in_transaction is False
    # connexion réutilisable après restauration
    monkeypatch.undo()
    r2 = svc.rename(wid, "OK")
    assert r2["ok"] is True and r2["data"]["name"] == "OK"
