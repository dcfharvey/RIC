"""Tests de la Phase 4.1C — serveur HTTP local minimal (web.py).

Couvre : liaison/cycle de vie, protection Host/Origin/jeton, validation des
requêtes, routes GET et POST, enveloppes JSON, statuts HTTP, fermeture des
connexions et absence de fuite du jeton.
"""

import http.client
import json
import socket
import threading

import pytest

from vivarium.db import connect_database
from vivarium.migrations import ensure_schema, load_migrations
from vivarium.web import WebServerError, create_server, serve, shutdown
from vivarium.world import WorldEngine


def _make_db(tmp_path, name="world.db", *, world_name="Admin"):
    db = tmp_path / name
    conn = connect_database(db)
    ensure_schema(conn)
    wid = WorldEngine(conn).init_world(name=world_name)["id"]
    conn.close()
    return db, wid


@pytest.fixture
def server(tmp_path):
    db, wid = _make_db(tmp_path)
    srv = create_server(db, host="127.0.0.1", port=0)
    port = srv.server_address[1]
    thread = threading.Thread(target=serve, args=(srv,), daemon=True)
    thread.start()
    yield srv, port, wid
    shutdown(srv)
    thread.join(timeout=5)
    assert not thread.is_alive()


def _request(
    port,
    method,
    path,
    *,
    headers=None,
    body=None,
    token=None,
    host=None,
    content_length=None,
):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.putrequest(method, path, skip_host=(host is not None))
    hdrs = dict(headers or {})
    if token is not None:
        hdrs["X-Vivarium-Token"] = token
    if host is not None:
        hdrs["Host"] = host
    if body is not None:
        hdrs.setdefault("Content-Type", "application/json")
    for k, v in hdrs.items():
        conn.putheader(k, v)
    if body is not None:
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode("utf-8")
        if content_length is None:
            conn.putheader("Content-Length", str(len(body)))
        else:
            conn.putheader("Content-Length", str(content_length))
        conn.endheaders(message_body=body)
    else:
        conn.endheaders()
    resp = conn.getresponse()
    raw = resp.read()
    status = resp.status
    headers_out = dict(resp.getheaders())
    conn.close()
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except Exception:
        parsed = None
    return status, parsed, headers_out


# --- Démarrage et validation de la base --------------------------------------

@pytest.mark.parametrize(
    "host",
    ["0.0.0.0", "::", "::1", "localhost", "", "192.168.1.5"],
)
def test_create_server_refuse_liaison_non_loopback(tmp_path, host):
    db, _ = _make_db(tmp_path)
    with pytest.raises(WebServerError):
        create_server(db, host=host)


def test_create_server_refuse_base_inexistante(tmp_path):
    with pytest.raises(WebServerError):
        create_server(tmp_path / "absent.db")


def test_create_server_refuse_base_invalide(tmp_path):
    bad = tmp_path / "bad.db"
    bad.write_text("pas une base sqlite", encoding="utf-8")
    with pytest.raises(WebServerError):
        create_server(bad)


def test_create_server_refuse_schema_incompatible(tmp_path):
    db, _ = _make_db(tmp_path)
    conn = connect_database(db)
    conn.execute("DELETE FROM migrations WHERE version = ?", (max(m.version for m in load_migrations()),))
    conn.commit()
    conn.close()
    with pytest.raises(WebServerError):
        create_server(db)


def test_create_server_port_zero_et_adresse(tmp_path):
    db, _ = _make_db(tmp_path)
    srv = create_server(db, host="127.0.0.1", port=0)
    try:
        assert srv.server_address[0] == "127.0.0.1"
        assert srv.server_address[1] > 0
        assert srv.db_path == db
        assert srv.token
    finally:
        srv.server_close()


def test_serveur_demarrage_arret_propre(tmp_path):
    db, _ = _make_db(tmp_path)
    srv = create_server(db, host="127.0.0.1", port=0)
    thread = threading.Thread(target=serve, args=(srv,), daemon=True)
    thread.start()
    shutdown(srv)
    thread.join(timeout=5)
    assert not thread.is_alive()


# --- Host ---------------------------------------------------------------------

def test_host_127_valide(server):
    srv, port, _ = server
    status, data, _ = _request(port, "GET", "/api/worlds", host=f"127.0.0.1:{port}")
    assert status == 200 and data["ok"] is True


def test_host_localhost_valide(server):
    srv, port, _ = server
    status, data, _ = _request(port, "GET", "/api/worlds", host=f"localhost:{port}")
    assert status == 200 and data["ok"] is True


def test_host_port_incorrect_refuse(server):
    srv, port, _ = server
    status, data, _ = _request(port, "GET", "/api/worlds", host=f"127.0.0.1:{port + 1}")
    assert status == 403 and data["error"]["code"] == "forbidden"


def test_host_externe_refuse(server):
    srv, port, _ = server
    status, data, _ = _request(port, "GET", "/api/worlds", host=f"evil.com:{port}")
    assert status == 403


def test_host_absent_refuse(server):
    srv, port, _ = server
    status, data, _ = _request(port, "GET", "/api/worlds", host="")
    assert status == 403


def test_host_malforme_refuse(server):
    srv, port, _ = server
    status, data, _ = _request(port, "GET", "/api/worlds", host="127.0.0.1:notaport")
    assert status == 403


# --- Origin -------------------------------------------------------------------

def test_origin_absente_acceptee(server):
    srv, port, _ = server
    status, data, _ = _request(port, "GET", "/api/worlds")
    assert status == 200


def test_origin_127_acceptee(server):
    srv, port, _ = server
    status, data, _ = _request(
        port, "GET", "/api/worlds", headers={"Origin": f"http://127.0.0.1:{port}"}
    )
    assert status == 200


def test_origin_localhost_acceptee(server):
    srv, port, _ = server
    status, data, _ = _request(
        port, "GET", "/api/worlds", headers={"Origin": f"http://localhost:{port}"}
    )
    assert status == 200


def test_origin_externe_refusee(server):
    srv, port, _ = server
    status, data, _ = _request(
        port, "GET", "/api/worlds", headers={"Origin": "http://evil.com"}
    )
    assert status == 403


def test_origin_port_different_refuse(server):
    srv, port, _ = server
    status, data, _ = _request(
        port, "GET", "/api/worlds", headers={"Origin": f"http://127.0.0.1:{port + 1}"}
    )
    assert status == 403


def test_origin_schema_different_refuse(server):
    srv, port, _ = server
    status, data, _ = _request(
        port, "GET", "/api/worlds", headers={"Origin": f"https://127.0.0.1:{port}"}
    )
    assert status == 403


def test_origin_null_refusee(server):
    srv, port, _ = server
    status, data, _ = _request(
        port, "GET", "/api/worlds", headers={"Origin": "null"}
    )
    assert status == 403


def test_origin_externe_refusee_sur_post(server):
    srv, port, _ = server
    status, data, _ = _request(
        port,
        "POST",
        "/api/commands/pause",
        headers={"Origin": "http://evil.com"},
        body={"world_id": 1},
        token=srv.token,
    )
    assert status == 403


def test_aucun_cors_permissif(server):
    srv, port, _ = server
    status, data, headers = _request(port, "GET", "/api/worlds")
    assert "Access-Control-Allow-Origin" not in headers


# --- Jeton --------------------------------------------------------------------

def test_post_bon_jeton(server):
    srv, port, wid = server
    status, data, _ = _request(
        port, "POST", "/api/commands/pause", body={"world_id": wid}, token=srv.token
    )
    assert status == 200 and data["ok"] is True


def test_post_jeton_absent(server):
    srv, port, wid = server
    status, data, _ = _request(port, "POST", "/api/commands/pause", body={"world_id": wid})
    assert status == 403 and data["error"]["code"] == "forbidden"


def test_post_jeton_vide(server):
    srv, port, wid = server
    status, data, _ = _request(
        port, "POST", "/api/commands/pause", body={"world_id": wid}, token=""
    )
    assert status == 403


def test_post_jeton_incorrect(server):
    srv, port, wid = server
    status, data, _ = _request(
        port, "POST", "/api/commands/pause", body={"world_id": wid}, token="wrong"
    )
    assert status == 403


def _raw_request(port, method, path, headers, body=b""):
    """Envoie une requête HTTP brute (en-têtes encodés latin-1).

    Utilisé pour les cas que http.client encode mal (jeton non-ASCII).
    """
    s = socket.create_connection(("127.0.0.1", port), timeout=5)
    lines = [f"{method} {path} HTTP/1.1"]
    for k, v in headers.items():
        lines.append(f"{k}: {v}")
    head = "\r\n".join(lines) + "\r\n\r\n"
    s.sendall(head.encode("latin-1") + body)
    s.shutdown(socket.SHUT_WR)
    data = b""
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        data += chunk
    s.close()
    head_part, _, body_part = data.partition(b"\r\n\r\n")
    status = int(head_part.split(b" ")[1])
    return status, body_part.decode("utf-8")


def test_post_jeton_unicode_incorrect(server):
    srv, port, wid = server
    body = json.dumps({"world_id": wid}).encode("utf-8")
    status, _ = _raw_request(
        port,
        "POST",
        "/api/commands/pause",
        {
            "Host": f"127.0.0.1:{port}",
            "X-Vivarium-Token": "t\xf6ken",  # latin-1 : ö
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
        body,
    )
    assert status == 403


def test_jeton_jamais_dans_reponse(server):
    srv, port, wid = server
    status, data, _ = _request(
        port, "POST", "/api/commands/pause", body={"world_id": wid}, token=srv.token
    )
    assert srv.token not in json.dumps(data)


def test_jeton_jamais_dans_logs(server, caplog):
    srv, port, wid = server
    import logging

    with caplog.at_level(logging.INFO):
        _request(port, "POST", "/api/commands/pause", body={"world_id": wid}, token=srv.token)
        _request(port, "POST", "/api/commands/pause", body={"world_id": wid}, token="bad")
    assert srv.token not in caplog.text


# --- GET ----------------------------------------------------------------------

def test_get_list_worlds(server):
    srv, port, wid = server
    status, data, _ = _request(port, "GET", "/api/worlds")
    assert status == 200 and data["ok"] is True
    assert any(w["id"] == wid for w in data["data"])


def test_get_dashboard(server):
    srv, port, wid = server
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}")
    assert status == 200
    assert data["data"]["world"]["id"] == wid
    assert "observed_canonical_at" in data["data"]
    assert "last_seq" in data["data"]


def test_get_characters(server):
    srv, port, wid = server
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}/characters")
    assert status == 200
    assert len(data["data"]) == 4


def test_get_character(server):
    srv, port, wid = server
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}/characters/character_1")
    assert status == 200
    assert data["data"]["character"]["key"] == "character_1"


def test_get_events(server):
    srv, port, wid = server
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}/events")
    assert status == 200
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0
    assert "payload" not in data["data"][0]


def test_get_events_include_payload(server):
    srv, port, wid = server
    status, data, _ = _request(
        port, "GET", f"/api/worlds/{wid}/events?include_payload=true"
    )
    assert status == 200
    assert "payload" in data["data"][0]


def test_get_events_pagination(server):
    srv, port, wid = server
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}/events?limit=2&offset=0")
    assert status == 200 and len(data["data"]) == 2
    status2, page2, _ = _request(
        port, "GET", f"/api/worlds/{wid}/events?limit=2&offset=2"
    )
    assert status2 == 200
    assert data["data"][0]["seq"] < page2["data"][0]["seq"]


def test_get_events_page_vide(server):
    srv, port, wid = server
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}/events?offset=99999")
    assert status == 200 and data["data"] == []


def test_get_monde_inexistant(server):
    srv, port, _ = server
    status, data, _ = _request(port, "GET", "/api/worlds/9999")
    assert status == 404


def test_get_personnage_inexistant(server):
    srv, port, wid = server
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}/characters/ghost")
    assert status == 404


def test_get_world_id_invalide(server):
    srv, port, _ = server
    status, data, _ = _request(port, "GET", "/api/worlds/abc")
    assert status == 400


def test_get_character_unicode(server):
    srv, port, wid = server
    status, data, _ = _request(
        port, "GET", f"/api/worlds/{wid}/characters/character_%31"
    )
    assert status in (200, 404)


def test_get_slash_final_refuse(server):
    srv, port, wid = server
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}/")
    assert status == 400


def test_get_route_inconnue(server):
    srv, port, _ = server
    status, data, _ = _request(port, "GET", "/api/bogus")
    assert status == 404


def test_get_methode_invalide(server):
    srv, port, wid = server
    status, data, _ = _request(port, "POST", f"/api/worlds/{wid}", body={})
    assert status == 405


def test_get_parametres_inconnus(server):
    srv, port, wid = server
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}/events?bogus=1")
    assert status == 400


def test_get_parametres_repetes(server):
    srv, port, wid = server
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}/events?limit=1&limit=2")
    assert status == 400


def test_get_limit_invalide(server):
    srv, port, wid = server
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}/events?limit=0")
    assert status == 400
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}/events?limit=201")
    assert status == 400
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}/events?limit=abc")
    assert status == 400


def test_get_offset_invalide(server):
    srv, port, wid = server
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}/events?offset=-1")
    assert status == 400


def test_get_include_payload_invalide(server):
    srv, port, wid = server
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}/events?include_payload=yes")
    assert status == 400


# --- POST ---------------------------------------------------------------------

def test_post_pause_resume(server):
    srv, port, wid = server
    status, data, _ = _request(
        port, "POST", "/api/commands/pause", body={"world_id": wid}, token=srv.token
    )
    assert status == 200 and data["data"]["status"] == "paused"
    status, data, _ = _request(
        port, "POST", "/api/commands/resume", body={"world_id": wid}, token=srv.token
    )
    assert status == 200 and data["data"]["status"] == "active"


def test_post_rename(server):
    srv, port, wid = server
    status, data, _ = _request(
        port, "POST", "/api/commands/rename", body={"world_id": wid, "name": "  X  "}, token=srv.token
    )
    assert status == 200 and data["data"]["name"] == "X"


def test_post_move(server):
    srv, port, wid = server
    status, data, _ = _request(
        port,
        "POST",
        "/api/commands/move",
        body={"world_id": wid, "character_key": "character_1", "destination": "couloir"},
        token=srv.token,
    )
    assert status == 200 and data["data"]["to"] == "couloir"


def test_post_refus_metier_409(server):
    srv, port, wid = server
    _request(port, "POST", "/api/commands/pause", body={"world_id": wid}, token=srv.token)
    status, data, _ = _request(
        port, "POST", "/api/commands/pause", body={"world_id": wid}, token=srv.token
    )
    assert status == 409 and data["error"]["code"] == "already_paused"


def test_post_commande_inconnue(server):
    srv, port, wid = server
    status, data, _ = _request(
        port, "POST", "/api/commands/teleport", body={"world_id": wid}, token=srv.token
    )
    assert status == 400 and data["error"]["code"] == "unknown_command"


def test_post_parametres_supplementaires(server):
    srv, port, wid = server
    status, data, _ = _request(
        port, "POST", "/api/commands/pause", body={"world_id": wid, "extra": 1}, token=srv.token
    )
    assert status == 400 and data["error"]["code"] == "invalid_parameters"


def test_post_parametres_absents(server):
    srv, port, _ = server
    status, data, _ = _request(
        port, "POST", "/api/commands/pause", body={}, token=srv.token
    )
    assert status == 400 and data["error"]["code"] == "invalid_parameters"


def test_post_bool_pour_world_id(server):
    srv, port, _ = server
    status, data, _ = _request(
        port, "POST", "/api/commands/pause", body={"world_id": True}, token=srv.token
    )
    assert status == 400 and data["error"]["code"] == "invalid_parameters"


def test_post_json_invalide(server):
    srv, port, _ = server
    status, data, _ = _request(
        port, "POST", "/api/commands/pause", body=b"{not json", token=srv.token
    )
    assert status == 400


def test_post_json_non_objet(server):
    srv, port, _ = server
    status, data, _ = _request(
        port, "POST", "/api/commands/pause", body=[1, 2], token=srv.token
    )
    assert status == 400


def test_post_corps_vide(server):
    srv, port, _ = server
    status, data, _ = _request(
        port, "POST", "/api/commands/pause", body=b"", token=srv.token
    )
    assert status == 400


def test_post_content_length_absent(server):
    srv, port, _ = server
    status, data, _ = _request(
        port,
        "POST",
        "/api/commands/pause",
        headers={"Content-Type": "application/json"},
        token=srv.token,
    )
    assert status == 411


def test_post_content_length_invalide(server):
    srv, port, _ = server
    status, data, _ = _request(
        port,
        "POST",
        "/api/commands/pause",
        body=b"{}",
        content_length="abc",
        token=srv.token,
    )
    assert status == 400


def test_post_corps_trop_gros(server):
    srv, port, _ = server
    status, data, _ = _request(
        port,
        "POST",
        "/api/commands/pause",
        body=b"{}",
        content_length=65537,
        token=srv.token,
    )
    assert status == 413


def test_post_content_type_absent(server):
    srv, port, _ = server
    status, data, _ = _request(
        port, "POST", "/api/commands/pause", body=b"{}", token=srv.token,
        headers={"Content-Type": ""},
    )
    assert status == 415


def test_post_content_type_invalide(server):
    srv, port, _ = server
    status, data, _ = _request(
        port, "POST", "/api/commands/pause", body=b"{}", token=srv.token,
        headers={"Content-Type": "text/plain"},
    )
    assert status == 415


def test_post_charset_valide(server):
    srv, port, wid = server
    status, data, _ = _request(
        port, "POST", "/api/commands/pause", body={"world_id": wid}, token=srv.token,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    assert status == 200


# --- Pipeline de changements administratifs ----------------------------------

def _prepare_change(port, wid, token, *, name="Après", ttl_seconds=None):
    body = {"world_id": wid, "name": name}
    if ttl_seconds is not None:
        body["ttl_seconds"] = ttl_seconds
    status, data, _ = _request(
        port,
        "POST",
        "/api/admin-changes/rename-world/prepare",
        body=body,
        token=token,
    )
    assert status == 200 and data["ok"] is True
    return data["data"]


def test_change_pipeline_http_complet(server):
    srv, port, wid = server
    plan = _prepare_change(port, wid, srv.token)
    plan_id = plan["id"]
    status, data, _ = _request(
        port, "GET", f"/api/admin-changes/{plan_id}/validate", token=srv.token
    )
    assert status == 200 and data["data"]["valid"] is True
    status, data, _ = _request(
        port, "GET", f"/api/admin-changes/{plan_id}/impact", token=srv.token
    )
    assert status == 200 and data["data"]["impact"]["classification"] == "non_sensitive"
    status, data, _ = _request(
        port,
        "POST",
        f"/api/admin-changes/{plan_id}/confirm",
        body={"hash": plan["hash"]},
        token=srv.token,
    )
    assert status == 200 and data["data"]["status"] == "applied"
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}")
    assert status == 200 and data["data"]["world"]["name"] == "Après"


@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/api/admin-changes/rename-world/prepare"),
        ("GET", "/api/admin-changes/00000000-0000-0000-0000-000000000000/validate"),
        ("GET", "/api/admin-changes/00000000-0000-0000-0000-000000000000/impact"),
        ("POST", "/api/admin-changes/00000000-0000-0000-0000-000000000000/confirm"),
    ],
)
def test_change_pipeline_requiert_jeton(server, method, path):
    srv, port, wid = server
    body = {"world_id": wid, "name": "Après"} if path.endswith("prepare") else {"hash": "0" * 64}
    status, data, _ = _request(port, method, path, body=body if method == "POST" else None)
    assert status == 403 and data["error"]["code"] == "forbidden"


def test_change_pipeline_refuse_hash_incorrect_sans_mutation(server):
    srv, port, wid = server
    plan = _prepare_change(port, wid, srv.token)
    status, data, _ = _request(
        port,
        "POST",
        f"/api/admin-changes/{plan['id']}/confirm",
        body={"hash": "0" * 64},
        token=srv.token,
    )
    assert status == 409 and data["error"]["code"] == "hash_mismatch"
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}")
    assert data["data"]["world"]["name"] == "Admin"


def test_change_pipeline_refuse_parametre_inconnu_et_uuid_invalide(server):
    srv, port, wid = server
    status, data, _ = _request(
        port,
        "POST",
        "/api/admin-changes/rename-world/prepare",
        body={"world_id": wid, "name": "Après", "extra": 1},
        token=srv.token,
    )
    assert status == 400 and data["error"]["code"] == "invalid_parameters"
    status, data, _ = _request(
        port, "GET", "/api/admin-changes/not-a-uuid/validate", token=srv.token
    )
    assert status == 400 and data["error"]["code"] == "invalid_parameters"


def test_change_pipeline_confirme_retry_sans_double_action(server):
    srv, port, wid = server
    plan = _prepare_change(port, wid, srv.token)
    path = f"/api/admin-changes/{plan['id']}/confirm"
    for expected in ("applied", "already_applied"):
        status, data, _ = _request(
            port, "POST", path, body={"hash": plan["hash"]}, token=srv.token
        )
        assert status == 200 and data["data"]["status"] == expected


def test_change_pipeline_http_ajoute_un_passage(server):
    srv, port, wid = server
    status, data, _ = _request(
        port,
        "POST",
        "/api/admin-changes/add-passage/prepare",
        body={
            "world_id": wid,
            "from_location": "cour",
            "to_location": "cuisine",
            "kind": "arch",
        },
        token=srv.token,
    )
    assert status == 200 and data["data"]["action"] == "add_link"
    plan = data["data"]
    status, data, _ = _request(
        port,
        "POST",
        f"/api/admin-changes/{plan['id']}/confirm",
        body={"hash": plan["hash"]},
        token=srv.token,
    )
    assert status == 200 and data["data"]["result"]["kind"] == "arch"


def test_prepare_passage_http_refuse_lieu_inconnu(server):
    srv, port, wid = server
    status, data, _ = _request(
        port,
        "POST",
        "/api/admin-changes/add-passage/prepare",
        body={"world_id": wid, "from_location": "ghost", "to_location": "cour"},
        token=srv.token,
    )
    assert status == 404 and data["error"]["code"] == "location_not_found"


def test_change_pipeline_http_retire_un_passage_sans_isoler(server):
    srv, port, wid = server
    # La résidence seedée est un arbre : on crée une voie de remplacement.
    status, data, _ = _request(
        port,
        "POST",
        "/api/admin-changes/add-passage/prepare",
        body={"world_id": wid, "from_location": "cour", "to_location": "cuisine"},
        token=srv.token,
    )
    assert status == 200
    added = data["data"]
    status, data, _ = _request(
        port, "POST", f"/api/admin-changes/{added['id']}/confirm",
        body={"hash": added["hash"]}, token=srv.token,
    )
    assert status == 200
    status, data, _ = _request(
        port,
        "POST",
        "/api/admin-changes/remove-passage/prepare",
        body={"world_id": wid, "from_location": "salon", "to_location": "cuisine"},
        token=srv.token,
    )
    assert status == 200 and data["data"]["action"] == "remove_link"
    plan = data["data"]
    status, data, _ = _request(
        port, "POST", f"/api/admin-changes/{plan['id']}/confirm",
        body={"hash": plan["hash"]}, token=srv.token,
    )
    assert status == 200 and data["data"]["result"]["directed_links_removed"] == 2


def test_prepare_fermeture_isolante_http_est_refusee(server):
    srv, port, wid = server
    status, data, _ = _request(
        port,
        "POST",
        "/api/admin-changes/remove-passage/prepare",
        body={"world_id": wid, "from_location": "couloir", "to_location": "chambre_1"},
        token=srv.token,
    )
    assert status == 409 and data["error"]["code"] == "would_isolate_location"


# --- Erreurs internes et connexions -------------------------------------------

def test_exception_inattendue_masquee(server, monkeypatch):
    srv, port, wid = server
    from vivarium import admin as admin_mod

    def boom(self, world_id):
        raise RuntimeError("SECRET /path/secret.db")
    monkeypatch.setattr(admin_mod.WorldEngine, "get_world", boom)
    status, data, _ = _request(port, "GET", f"/api/worlds/{wid}")
    assert status == 500
    assert data["error"]["code"] == "internal"
    assert "SECRET" not in json.dumps(data)
    assert "secret.db" not in json.dumps(data)


def test_serveur_reutilisable_apres_erreur(server):
    srv, port, wid = server
    status, data, _ = _request(port, "GET", "/api/worlds/9999")
    assert status == 404
    status, data, _ = _request(port, "GET", "/api/worlds")
    assert status == 200


def test_serveur_reutilisable_apres_refus_host(server):
    srv, port, _ = server
    status, data, _ = _request(port, "GET", "/api/worlds", host="evil.com:1")
    assert status == 403
    status, data, _ = _request(port, "GET", "/api/worlds")
    assert status == 200


# --- En-têtes -----------------------------------------------------------------

def test_en_tetes_reponse(server):
    srv, port, _ = server
    status, data, headers = _request(port, "GET", "/api/worlds")
    assert headers["Content-Type"].startswith("application/json")
    assert headers["Cache-Control"] == "no-store"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["Referrer-Policy"] == "no-referrer"
    assert int(headers["Content-Length"]) > 0


# --- Méthodes non permises (C-2) ---------------------------------------------

@pytest.mark.parametrize("method", ["PUT", "PATCH", "DELETE", "OPTIONS"])
def test_methode_non_permise_route_connue(server, method):
    srv, port, wid = server
    status, data, headers = _request(port, method, f"/api/worlds/{wid}")
    assert status == 405
    assert data["ok"] is False and data["error"]["code"] == "method_not_allowed"
    assert "Access-Control-Allow-Origin" not in headers
    assert headers["Content-Type"].startswith("application/json")


@pytest.mark.parametrize("method", ["PUT", "PATCH", "DELETE", "OPTIONS"])
def test_methode_non_permise_route_inconnue(server, method):
    srv, port, _ = server
    status, data, _ = _request(port, method, "/api/bogus")
    assert status == 404
    assert data["error"]["code"] == "not_found"


def test_head_route_inconnue_sans_corps(server):
    srv, port, _ = server
    status, data, _ = _request(port, "HEAD", "/api/bogus")
    assert status == 404
    assert data is None  # HEAD ne renvoie aucun corps


@pytest.mark.parametrize("method", ["PUT", "PATCH", "DELETE", "OPTIONS"])
def test_methode_non_permise_aucun_html(server, method):
    srv, port, wid = server
    status, data, _ = _request(port, method, f"/api/worlds/{wid}")
    assert status == 405
    assert data is not None and "ok" in data  # JSON, jamais HTML


def test_head_route_connue_sans_corps(server):
    srv, port, wid = server
    status, data, headers = _request(port, "HEAD", f"/api/worlds/{wid}")
    assert status == 200
    assert data is None  # aucun corps
    assert int(headers["Content-Length"]) > 0
    assert headers["Content-Type"].startswith("application/json")


# --- Cycle de vie (C-3) ------------------------------------------------------

def test_shutdown_sans_serve_ne_bloque_pas(tmp_path):
    db, _ = _make_db(tmp_path)
    srv = create_server(db, host="127.0.0.1", port=0)
    shutdown(srv)
    shutdown(srv)  # idempotent


def test_double_shutdown_apres_serve(tmp_path):
    db, _ = _make_db(tmp_path)
    srv = create_server(db, host="127.0.0.1", port=0)
    thread = threading.Thread(target=serve, args=(srv,), daemon=True)
    thread.start()
    shutdown(srv)
    thread.join(timeout=5)
    assert not thread.is_alive()
    shutdown(srv)  # second shutdown ne bloque pas


def test_port_libree_apres_fermeture(tmp_path):
    db, _ = _make_db(tmp_path)
    srv = create_server(db, host="127.0.0.1", port=0)
    port = srv.server_address[1]
    shutdown(srv)
    srv2 = create_server(db, host="127.0.0.1", port=port)
    assert srv2.server_address[1] == port
    srv2.server_close()


# --- Validation du port (C-4) -------------------------------------------------

@pytest.mark.parametrize("port", [True, False, -1, 65536, 70000, 1.5, "80", None])
def test_create_server_refuse_port_invalide(tmp_path, port):
    db, _ = _make_db(tmp_path)
    with pytest.raises(WebServerError):
        create_server(db, host="127.0.0.1", port=port)


def test_create_server_port_zero_ephemere(tmp_path):
    db, _ = _make_db(tmp_path)
    srv = create_server(db, host="127.0.0.1", port=0)
    assert srv.server_address[1] > 0
    srv.server_close()


# --- world_id hors plage (C-5) ------------------------------------------------

def test_world_id_max_sqlite(server):
    srv, port, _ = server
    status, data, _ = _request(port, "GET", "/api/worlds/9223372036854775807")
    assert status == 404  # syntaxiquement valide mais inexistant


@pytest.mark.parametrize(
    "value", ["9223372036854775808", "999999999999999999999999999999"]
)
def test_world_id_hors_plage_400(server, value):
    srv, port, _ = server
    status, data, _ = _request(port, "GET", f"/api/worlds/{value}")
    assert status == 400
    assert data["error"]["code"] == "invalid_parameters"


# --- Validation de base non destructive (C-1) --------------------------------

def test_validation_base_non_destructive(tmp_path):
    import hashlib

    db, _ = _make_db(tmp_path)
    size_before = db.stat().st_size
    hash_before = hashlib.sha256(db.read_bytes()).hexdigest()
    srv = create_server(db, host="127.0.0.1", port=0)
    srv.server_close()
    assert db.stat().st_size == size_before
    assert hashlib.sha256(db.read_bytes()).hexdigest() == hash_before
