"""Tests de la Phase 4.1D — tableau de bord local simple.

Couvre : routes statiques fermées (/, CSS, JS), injection du jeton local,
en-têtes et protections, absence de connexion SQLite pour le statique, et
sécurité du front-end (pas d'innerHTML dynamique, pas d'éval, pas de polling).
"""

import http.client
import json
import threading

import pytest

from vivarium.db import connect_database
from vivarium.migrations import ensure_schema
from vivarium.web import STATIC_DIR, create_server, serve, shutdown
from vivarium.world import WorldEngine


def _make_db(tmp_path):
    db = tmp_path / "world.db"
    conn = connect_database(db)
    ensure_schema(conn)
    WorldEngine(conn).init_world(name="Admin")
    conn.close()
    return db


@pytest.fixture
def server(tmp_path):
    db = _make_db(tmp_path)
    srv = create_server(db, host="127.0.0.1", port=0)
    port = srv.server_address[1]
    thread = threading.Thread(target=serve, args=(srv,), daemon=True)
    thread.start()
    yield srv, port
    shutdown(srv)
    thread.join(timeout=5)
    assert not thread.is_alive()


def _request(port, method, path, *, host=None, origin=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    c.putrequest(method, path, skip_host=(host is not None))
    hdrs = {}
    if host is not None:
        hdrs["Host"] = host
    if origin is not None:
        hdrs["Origin"] = origin
    for k, v in hdrs.items():
        c.putheader(k, v)
    c.endheaders()
    r = c.getresponse()
    raw = r.read()
    status = r.status
    headers = dict(r.getheaders())
    c.close()
    return status, raw, headers


# --- Routes statiques ---------------------------------------------------------

def test_get_index(server):
    srv, port = server
    status, raw, headers = _request(port, "GET", "/")
    assert status == 200
    assert headers["Content-Type"].startswith("text/html")
    assert int(headers["Content-Length"]) == len(raw)
    assert headers["Cache-Control"] == "no-store"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["Referrer-Policy"] == "no-referrer"
    body = raw.decode("utf-8")
    assert "__VIVARIUM_TOKEN__" not in body  # placeholder remplacé
    assert srv.token in body  # valeur réelle injectée


def test_index_html_sur_disque_ne_contient_pas_le_jeton(server):
    srv, port = server
    disk = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    assert "__VIVARIUM_TOKEN__" in disk
    assert srv.token not in disk


def test_get_css(server):
    srv, port = server
    status, raw, headers = _request(port, "GET", "/static/style.css")
    assert status == 200
    assert headers["Content-Type"].startswith("text/css")
    assert int(headers["Content-Length"]) == len(raw)
    assert srv.token not in raw.decode("utf-8")


def test_get_js(server):
    srv, port = server
    status, raw, headers = _request(port, "GET", "/static/app.js")
    assert status == 200
    assert headers["Content-Type"].startswith("application/javascript")
    assert int(headers["Content-Length"]) == len(raw)
    assert srv.token not in raw.decode("utf-8")


@pytest.mark.parametrize("path", ["/", "/static/style.css", "/static/app.js"])
def test_head_statique(server, path):
    srv, port = server
    status, raw, headers = _request(port, "HEAD", path)
    assert status == 200
    assert raw == b""  # aucun corps
    assert int(headers["Content-Length"]) > 0


def test_route_inconnue_404(server):
    srv, port = server
    for path in [
        "/static/other.css",
        "/static/",
        "/nope",
        "/api/",
        "/static/../etc/passwd",
        "/static/%2e%2e/style.css",
        "/static/%252e%252e/style.css",
        "/static/..%2fstyle.css",
    ]:
        status, _, _ = _request(port, "GET", path)
        assert status in (400, 404), path


def test_host_invalide_static(server):
    srv, port = server
    status, _, _ = _request(port, "GET", "/", host="evil.com:1")
    assert status == 403


def test_origin_invalide_static(server):
    srv, port = server
    status, _, _ = _request(port, "GET", "/", origin="http://evil.com")
    assert status == 403


def test_static_aucune_connexion_sqlite(server, monkeypatch):
    import vivarium.web as web

    srv, port = server
    opens = {"n": 0}
    orig = web.connect_database

    def counting(path):
        opens["n"] += 1
        return orig(path)

    monkeypatch.setattr(web, "connect_database", counting)
    _request(port, "GET", "/")
    assert opens["n"] == 0
    _request(port, "GET", "/static/app.js")
    assert opens["n"] == 0
    _request(port, "GET", "/static/style.css")
    assert opens["n"] == 0
    # une route API, elle, ouvre une connexion
    _request(port, "GET", "/api/worlds")
    assert opens["n"] == 1


def test_aucun_listing_ni_acces_arbitraire(server):
    srv, port = server
    status, _, _ = _request(port, "GET", "/static/")
    assert status in (400, 404)


# --- Jeton -------------------------------------------------------------------

def test_jeton_absent_des_logs(server, caplog):
    import logging

    srv, port = server
    with caplog.at_level(logging.INFO):
        _request(port, "GET", "/")
        _request(port, "GET", "/static/app.js")
    assert srv.token not in caplog.text


# --- Sécurité du front-end ----------------------------------------------------

def test_app_js_securite():
    js = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    for bad in [
        "eval(",
        "new Function",
        "document.write",
        "innerHTML",
        "insertAdjacentHTML",
        "localStorage",
        "sessionStorage",
        "document.cookie",
        "http://",
        "https://",
        "setInterval",  # pas de polling
    ]:
        assert bad not in js, bad
    assert "textContent" in js
    assert "createElement" in js
    assert "encodeURIComponent" in js
    assert "X-Vivarium-Token" in js
    assert "vivarium-token" in js
    assert ".remove()" in js  # la meta est retirée du DOM


def test_index_html_structure():
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    assert 'name="vivarium-token"' in html
    assert "__VIVARIUM_TOKEN__" in html
    assert "/static/style.css" in html
    assert "/static/app.js" in html


# --- Énergie (D-1) -----------------------------------------------------------

def _fmt_energy(v):
    # réplique de formatEnergy (unité interne : millièmes de pourcentage).
    # Arrondi demi-supérieur, identique à Math.round côté JS.
    percent = int((v / 1000) * 100 + 0.5) / 100
    s = ("%.2f" % percent).rstrip("0").rstrip(".").replace(".", ",")
    return s + " %"


def test_energie_unite_milli_pourcent():
    # 1000 unités = 100 % ; l'unité interne est value_milli (millièmes)
    assert _fmt_energy(0) == "0 %"
    assert _fmt_energy(7000) == "7 %"
    assert _fmt_energy(100000) == "100 %"
    assert _fmt_energy(69379) == "69,38 %"
    assert _fmt_energy(6985) == "6,99 %"  # pas 69,85 % (unité réelle)


def test_app_js_convertit_energie_en_milli_pourcent():
    js = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert "/ 1000" in js
    assert "formatEnergy" in js
    assert "toFixed(2)" in js


def test_energie_js_reelle_via_node():
    import re
    import shutil
    import subprocess

    if shutil.which("node") is None:
        pytest.skip("node non disponible")
    js = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    m = re.search(r"function formatEnergy\(value\) \{.*?\n  \}", js, re.S)
    assert m is not None
    script = m.group(0) + "\n" + (
        "console.log(JSON.stringify([formatEnergy(0),formatEnergy(7000),"
        "formatEnergy(69379),formatEnergy(100000),formatEnergy(6985)]));"
    )
    out = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, timeout=10
    )
    assert out.returncode == 0, out.stderr
    values = json.loads(out.stdout.strip())
    assert values == ["0 %", "7 %", "69,38 %", "100 %", "6,99 %"]


# --- Dates (D-2) -------------------------------------------------------------

def test_app_js_format_dates():
    js = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert "formatTopDate" in js
    assert "formatJournalTime" in js
    assert "toLocaleDateString" in js
    assert "toLocaleTimeString" in js
    assert "isNaN" in js  # date invalide gérée
    # pas de millisecondes visibles dans les formats
    assert "toLocaleTimeString(\"fr-FR\", { hour: \"2-digit\", minute: \"2-digit\" })" in js


# --- Journal (D-3) -----------------------------------------------------------

def test_app_js_journal_reduit_et_ordre():
    js = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert "MAX_JOURNAL_SHOWN = 20" in js
    assert ".slice(-MAX_JOURNAL_SHOWN).reverse()" in js  # plus récents en premier
    assert "limit=200" in js


def test_css_journal_scroll_interne():
    css = (STATIC_DIR / "style.css").read_text(encoding="utf-8")
    assert "max-height" in css
    assert "overflow-y: auto" in css


# --- Grille (D-4) ------------------------------------------------------------

def test_css_grille_equilibree():
    css = (STATIC_DIR / "style.css").read_text(encoding="utf-8")
    assert "grid-template-areas" in css
    assert "\"worlds chars detail\"" in css
    assert "\"journal journal commands\"" in css
    assert "@media (max-width: 900px)" in css


# --- Messages (D-5) ----------------------------------------------------------

def test_app_js_message_succes_temporaire():
    js = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert "setTimeout" in js
    assert "clearTimeout" in js
    assert "successTimer" in js
    assert "alert(" not in js
