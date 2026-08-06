"""Serveur HTTP local minimal (Phase 4.1C).

Fine couche de transport locale donnant accès aux services administratifs déjà
validés (`AdminReadService`, `AdminCommandService`). Le serveur :

- n'écrit jamais directement dans SQLite ;
- ne connaît aucune table, ne contient aucun SQL ;
- n'appelle aucun moteur directement ni `_append_event` ;
- ouvre une connexion par requête et la ferme systématiquement ;
- n'expose aucune logique métier.

Bibliothèque standard uniquement (`http.server`, `secrets`, `json`,
`urllib.parse`, `logging`). Serveur mono-thread écoutant uniquement sur
`127.0.0.1`, avec protection locale par validation Host/Origin et jeton local
pour les mutations (POST) ainsi que les lectures de plans administratifs.
"""

from __future__ import annotations

import html
import http.server
import json
import logging
import secrets
import sqlite3
import uuid
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from .admin import AdminCommandService, AdminReadError, AdminReadService
from .admin_changes import AdminChangeError, AdminChangeService
from .db import connect_database
from .migrations import load_migrations

logger = logging.getLogger("vivarium.web")

# Limite de taille du corps des requêtes (D-5).
MAX_BODY_BYTES = 65536

# Borne maximale d'un identifiant SQLite signé 64 bits (C-5).
SQLITE_MAX_INT = 9223372036854775807

# Répertoire des fichiers statiques du tableau de bord (Phase 4.1D).
STATIC_DIR = Path(__file__).resolve().parent / "static"

# Placeholder du jeton local dans le modèle HTML (remplacé à la diffusion).
TOKEN_PLACEHOLDER = "__VIVARIUM_TOKEN__"

# Tables attendues pour une base compatible (le numéro de migration est calculé
# depuis le registre de migrations livré, jamais codé en dur).
REQUIRED_TABLES = frozenset(
    {
        "worlds",
        "canonical_clock",
        "canonical_event",
        "location",
        "location_link",
        "character",
        "character_profile",
        "need_definition",
        "need_state",
        "activity",
        "activity_definition",
        "activity_allowed_location",
        "injury",
        "world_object",
        "admin_change_plan",
        "admin_audit_event",
        "migrations",
    }
)

# Commandes autorisées (fermeture au niveau HTTP, redoublée par le dispatcher
# fermé d'AdminCommandService).
ALLOWED_COMMANDS = frozenset({"pause", "resume", "rename", "move"})

# Paramètres métier autorisés par commande (refus des paramètres supplémentaires).
COMMAND_PARAMS = {
    "pause": frozenset({"world_id"}),
    "resume": frozenset({"world_id"}),
    "rename": frozenset({"world_id", "name"}),
    "move": frozenset({"world_id", "character_key", "destination"}),
}


class WebServerError(RuntimeError):
    """Erreur de démarrage du serveur (base absente, invalide ou incompatible).

    Levée hors HTTP, avec un diagnostic local utile mais sans secret.
    """


class HttpError(Exception):
    """Erreur HTTP contrôlée (statut + code + message générique)."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def _validate_db(db_path: Path) -> None:
    """Validation strictement en lecture de la base, sans aucune modification.

    Vérifie que le fichier existe, est une base SQLite lisible, contient les
    tables requises et est à la version de schéma attendue.
    N'applique aucune migration et ne crée jamais une base absente.
    """
    path = Path(db_path)
    if not path.exists() or not path.is_file():
        raise WebServerError(f"base introuvable : {path}")
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.Error as e:
        raise WebServerError(f"base illisible : {e}") from None
    try:
        try:
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        except sqlite3.Error as e:
            raise WebServerError(f"base invalide : {e}") from None
        missing = REQUIRED_TABLES - tables
        if missing:
            raise WebServerError(
                f"tables manquantes : {', '.join(sorted(missing))}"
            )
        row = conn.execute(
            "SELECT MAX(version) AS v FROM migrations"
        ).fetchone()
        version = row[0] if row and row[0] is not None else 0
        expected = max(m.version for m in load_migrations())
        if version != expected:
            raise WebServerError(
                f"version de schéma incompatible : {version} (attendu {expected})"
            )
    finally:
        conn.close()


class VivariumRequestHandler(http.server.BaseHTTPRequestHandler):
    """Transport HTTP pur. Aucune logique métier, aucun SQL."""

    server_version = "Vivarium"
    sys_version = ""

    # --- journalisation technique (jamais le jeton, jamais le corps) ---------

    def log_message(self, fmt: str, *args) -> None:
        logger.info("%s %s", self.address_string(), fmt % args)

    # --- points d'entrée ------------------------------------------------------

    def do_GET(self) -> None:
        self._handle()

    def do_POST(self) -> None:
        self._handle()

    # Méthodes non permises : jamais le comportement HTML 501 hérité (C-2).
    # Chacune route vers `_handle`, qui retourne 405 JSON sur route connue et
    # 404 JSON sur route inconnue, sans ouvrir de connexion SQLite.
    def do_PUT(self) -> None:
        self._handle()

    def do_PATCH(self) -> None:
        self._handle()

    def do_DELETE(self) -> None:
        self._handle()

    def do_OPTIONS(self) -> None:
        self._handle()

    def do_HEAD(self) -> None:
        self._handle()

    # --- flux principal -------------------------------------------------------

    def _handle(self) -> None:
        try:
            self._check_host()
            self._check_origin()
            kind, args = self._resolve_route()
            if kind in ("index", "style", "app"):
                if self.command in ("GET", "HEAD"):
                    self._serve_static(kind, send_body=(self.command == "GET"))
                else:
                    raise HttpError(405, "method_not_allowed", "Méthode non autorisée.")
            elif self.command in ("GET", "HEAD"):
                if kind in (
                    "command", "change_prepare", "change_prepare_passage", "change_confirm"
                ):
                    raise HttpError(405, "method_not_allowed", "Méthode non autorisée.")
                if kind in ("change_validate", "change_impact"):
                    self._serve_change_read(kind, args[0], send_body=(self.command == "GET"))
                else:
                    self._serve_get(kind, args, send_body=(self.command == "GET"))
            elif self.command == "POST":
                if kind == "command":
                    self._serve_command(args[0])
                elif kind in ("change_prepare", "change_prepare_passage", "change_confirm"):
                    self._serve_change_command(kind, args)
                else:
                    raise HttpError(405, "method_not_allowed", "Méthode non autorisée.")
            else:
                raise HttpError(405, "method_not_allowed", "Méthode non autorisée.")
        except HttpError as e:
            self._send_error(e.status, e.code, e.message, send_body=(self.command != "HEAD"))
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception:
            logger.exception("erreur interne du serveur HTTP")
            self._send_error(500, "internal", "Erreur interne.", send_body=(self.command != "HEAD"))

    # --- protection locale ----------------------------------------------------

    def _check_host(self) -> None:
        if not self._host_valid():
            raise HttpError(403, "forbidden", "Accès refusé.")

    def _host_valid(self) -> bool:
        host = self.headers.get("Host")
        if not host:
            return False
        real_port = self.server.server_address[1]
        if ":" in host:
            h, _, port = host.rpartition(":")
            if h not in ("127.0.0.1", "localhost"):
                return False
            return port == str(real_port)
        return host in ("127.0.0.1", "localhost")

    def _check_origin(self) -> None:
        origin = self.headers.get("Origin")
        if origin is None:
            return
        real_port = self.server.server_address[1]
        allowed = {
            f"http://127.0.0.1:{real_port}",
            f"http://localhost:{real_port}",
        }
        if origin not in allowed:
            raise HttpError(403, "forbidden", "Accès refusé.")

    def _check_token(self) -> bool:
        token = self.headers.get("X-Vivarium-Token")
        if not token:
            return False
        # Comparaison en octets : évite une TypeError sur un jeton non-ASCII
        # (compare_digest exige de l'ASCII pour les str) et traite tout jeton
        # différent comme incorrect (403 générique).
        return secrets.compare_digest(
            token.encode("utf-8"), self.server.token.encode("utf-8")
        )

    # --- routage --------------------------------------------------------------

    def _resolve_route(self) -> tuple[str, list[str]]:
        raw = urlsplit(self.path).path
        if not raw.startswith("/"):
            raise HttpError(404, "not_found", "Route inconnue.")
        if raw == "/":
            return ("index", [])
        if "//" in raw or raw.endswith("/"):
            raise HttpError(400, "invalid_path", "Chemin invalide.")
        parts = raw.split("/")[1:]
        # Routes statiques explicites et fermées (aucun chemin construit depuis
        # l'entrée client ; aucun listing ni accès arbitraire).
        if parts == ["static", "style.css"]:
            return ("style", [])
        if parts == ["static", "app.js"]:
            return ("app", [])
        if not parts or parts[0] != "api":
            raise HttpError(404, "not_found", "Route inconnue.")
        if parts == ["api", "worlds"]:
            return ("list_worlds", [])
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "worlds":
            return ("dashboard", [parts[2]])
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "worlds":
            if parts[3] == "characters":
                return ("characters", [parts[2]])
            if parts[3] == "events":
                return ("events", [parts[2]])
            raise HttpError(404, "not_found", "Route inconnue.")
        if (
            len(parts) == 5
            and parts[0] == "api"
            and parts[1] == "worlds"
            and parts[3] == "characters"
        ):
            return ("character", [parts[2], parts[4]])
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "commands":
            return ("command", [parts[2]])
        if parts == ["api", "admin-changes", "rename-world", "prepare"]:
            return ("change_prepare", [])
        if parts == ["api", "admin-changes", "add-passage", "prepare"]:
            return ("change_prepare_passage", [])
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "admin-changes":
            plan_id = self._parse_plan_id(parts[2])
            if parts[3] == "validate":
                return ("change_validate", [plan_id])
            if parts[3] == "impact":
                return ("change_impact", [plan_id])
            if parts[3] == "confirm":
                return ("change_confirm", [plan_id])
        raise HttpError(404, "not_found", "Route inconnue.")

    # --- fichiers statiques (Phase 4.1D) --------------------------------------

    def _serve_static(self, kind: str, send_body: bool = True) -> None:
        """Sert un fichier statique fermé, sans ouvrir de connexion SQLite."""
        if kind == "index":
            body = self._index_html().encode("utf-8")
            ctype = "text/html; charset=utf-8"
        elif kind == "style":
            body = (STATIC_DIR / "style.css").read_bytes()
            ctype = "text/css; charset=utf-8"
        elif kind == "app":
            body = (STATIC_DIR / "app.js").read_bytes()
            ctype = "application/javascript; charset=utf-8"
        else:  # pragma: no cover - routeur garantit la fermeture
            raise HttpError(404, "not_found", "Route inconnue.")
        self._send_bytes(200, body, ctype, send_body=send_body)

    def _index_html(self) -> str:
        """Lit le modèle HTML et y injecte le jeton local (une seule occurrence)."""
        template = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        count = template.count(TOKEN_PLACEHOLDER)
        if count != 1:
            raise RuntimeError(
                f"placeholder de jeton attendu une seule fois, trouvé {count}"
            )
        token = html.escape(self.server.token, quote=True)
        return template.replace(TOKEN_PLACEHOLDER, token)

    # --- lectures (GET) -------------------------------------------------------

    def _serve_get(self, kind: str, args: list[str], send_body: bool = True) -> None:
        conn = connect_database(self.server.db_path)
        try:
            svc = AdminReadService(conn)
            if kind == "list_worlds":
                data = svc.list_worlds()
            elif kind == "dashboard":
                data = svc.dashboard(self._parse_world_id(args[0]))
            elif kind == "characters":
                data = svc.list_character_views(self._parse_world_id(args[0]))
            elif kind == "character":
                wid = self._parse_world_id(args[0])
                ckey = self._parse_character_key(args[1])
                data = svc.character_view(wid, ckey)
            elif kind == "events":
                wid = self._parse_world_id(args[0])
                query = self._parse_events_query()
                data = svc.journal_view(wid, **query)
            else:  # pragma: no cover - routeur garantit la fermeture
                raise HttpError(404, "not_found", "Route inconnue.")
            self._send_json(200, {"ok": True, "data": data, "error": None}, send_body=send_body)
        except AdminReadError as e:
            self._send_error(404, "not_found", str(e), send_body=send_body)
        except ValueError as e:
            self._send_error(400, "invalid_parameters", str(e), send_body=send_body)
        finally:
            conn.close()

    # --- commandes (POST) -----------------------------------------------------

    def _serve_command(self, command: str) -> None:
        if command not in ALLOWED_COMMANDS:
            raise HttpError(400, "unknown_command", "Commande inconnue.")
        if not self._check_token():
            raise HttpError(403, "forbidden", "Accès refusé.")
        payload = self._read_json_object(COMMAND_PARAMS[command])

        conn = connect_database(self.server.db_path)
        try:
            result = AdminCommandService(conn).execute(command, payload)
        finally:
            conn.close()
        self._send_json(self._command_status(result), result)

    # --- plans de changement administratifs (HTTP local) -------------------

    def _serve_change_read(
        self, kind: str, plan_id: str, send_body: bool = True
    ) -> None:
        """Expose les lectures d'un plan seulement au client local authentifié."""
        if urlsplit(self.path).query:
            raise HttpError(400, "invalid_parameters", "Paramètre inconnu.")
        if not self._check_token():
            raise HttpError(403, "forbidden", "Accès refusé.")
        conn = connect_database(self.server.db_path)
        try:
            service = AdminChangeService(conn)
            if kind == "change_validate":
                data = service.validate(plan_id)
            elif kind == "change_impact":
                data = service.impact(plan_id)
            else:  # pragma: no cover - routeur fermé
                raise HttpError(404, "not_found", "Route inconnue.")
        except AdminChangeError as exc:
            self._send_change_error(exc, send_body=send_body)
            return
        finally:
            conn.close()
        self._send_json(200, {"ok": True, "data": data, "error": None}, send_body=send_body)

    def _serve_change_command(self, kind: str, args: list[str]) -> None:
        """Prépare ou confirme un plan; aucun SQL ni logique métier HTTP."""
        if not self._check_token():
            raise HttpError(403, "forbidden", "Accès refusé.")
        if kind == "change_prepare":
            payload = self._read_json_object(frozenset({"world_id", "name", "ttl_seconds"}))
        elif kind == "change_prepare_passage":
            payload = self._read_json_object(
                frozenset({"world_id", "from_location", "to_location", "bidirectional", "kind", "ttl_seconds"})
            )
        elif kind == "change_confirm":
            payload = self._read_json_object(frozenset({"hash"}))
        else:  # pragma: no cover - routeur fermé
            raise HttpError(404, "not_found", "Route inconnue.")

        conn = connect_database(self.server.db_path)
        try:
            service = AdminChangeService(conn)
            if kind == "change_prepare":
                data = service.prepare_rename_world(
                    payload.get("world_id"),
                    payload.get("name"),
                    ttl_seconds=payload.get("ttl_seconds"),
                )
            elif kind == "change_prepare_passage":
                data = service.prepare_add_link(
                    payload.get("world_id"),
                    payload.get("from_location"),
                    payload.get("to_location"),
                    bidirectional=payload.get("bidirectional", True),
                    kind=payload.get("kind", "door"),
                    ttl_seconds=payload.get("ttl_seconds"),
                )
            else:
                data = service.confirm(args[0], payload.get("hash"))
        except AdminChangeError as exc:
            self._send_change_error(exc)
            return
        finally:
            conn.close()
        self._send_json(200, {"ok": True, "data": data, "error": None})

    def _send_change_error(self, exc: AdminChangeError, send_body: bool = True) -> None:
        mapping = {
            "invalid_parameters": 400,
            "invalid_name": 400,
            "invalid_link": 400,
            "location_not_found": 404,
            "world_not_found": 404,
            "plan_not_found": 404,
            "no_effect": 409,
            "hash_mismatch": 409,
            "plan_expired": 409,
            "world_changed": 409,
        }
        self._send_error(
            mapping.get(exc.code, 500),
            exc.code if exc.code in mapping else "internal",
            str(exc) if exc.code in mapping else "Erreur interne.",
            send_body=send_body,
        )

    def _read_json_object(self, allowed: frozenset[str]) -> dict:
        """Lit un corps JSON objet borné et refuse les champs inconnus."""
        ctype = self.headers.get("Content-Type", "")
        if ctype.split(";")[0].strip().lower() != "application/json":
            raise HttpError(415, "unsupported_media_type", "Content-Type invalide.")
        clen = self._read_content_length()
        body = self.rfile.read(clen)
        if not body or not body.strip():
            raise HttpError(400, "invalid_parameters", "Corps vide.")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            raise HttpError(400, "invalid_parameters", "JSON invalide.")
        if not isinstance(payload, dict):
            raise HttpError(400, "invalid_parameters", "Corps JSON non objet.")
        if set(payload) - allowed:
            raise HttpError(400, "invalid_parameters", "Paramètre inconnu.")
        return payload

    def _read_content_length(self) -> int:
        raw = self.headers.get("Content-Length")
        if raw is None:
            raise HttpError(411, "length_required", "Content-Length requis.")
        try:
            clen = int(raw)
        except ValueError:
            raise HttpError(400, "invalid_parameters", "Content-Length invalide.")
        if clen < 0:
            raise HttpError(400, "invalid_parameters", "Content-Length invalide.")
        if clen > MAX_BODY_BYTES:
            raise HttpError(413, "payload_too_large", "Corps trop volumineux.")
        return clen

    @staticmethod
    def _command_status(result: dict) -> int:
        if result.get("ok"):
            return 200
        code = result["error"]["code"]
        mapping = {
            "invalid_parameters": 400,
            "unknown_command": 400,
            "invalid_name": 400,
            "world_not_found": 404,
            "character_not_found": 404,
            "destination_not_found": 404,
            "already_paused": 409,
            "already_active": 409,
            "activity_active": 409,
            "injury_severe": 409,
            "insufficient_energy": 409,
            "world_paused": 409,
            "invalid_destination": 409,
            "internal": 500,
        }
        return mapping.get(code, 500)

    # --- validation des paramètres -------------------------------------------

    def _parse_world_id(self, segment: str) -> int:
        if not isinstance(segment, str) or not segment.isdigit():
            raise HttpError(400, "invalid_parameters", "world_id invalide.")
        value = int(segment)
        if value > SQLITE_MAX_INT:
            raise HttpError(400, "invalid_parameters", "world_id hors plage.")
        return value

    def _parse_character_key(self, segment: str) -> str:
        key = unquote(segment)
        if not key or "/" in key:
            raise HttpError(400, "invalid_parameters", "character_key invalide.")
        return key

    @staticmethod
    def _parse_plan_id(segment: str) -> str:
        """Accepte uniquement l'UUID canonique émis par le service métier."""
        value = unquote(segment)
        try:
            parsed = uuid.UUID(value)
        except (ValueError, AttributeError):
            raise HttpError(400, "invalid_parameters", "plan_id invalide.") from None
        if str(parsed) != value:
            raise HttpError(400, "invalid_parameters", "plan_id invalide.")
        return value

    def _parse_events_query(self) -> dict:
        query = urlsplit(self.path).query
        params = parse_qs(query, keep_blank_values=True)
        allowed = {"limit", "offset", "include_payload"}
        unknown = set(params) - allowed
        if unknown:
            raise HttpError(400, "invalid_parameters", "Paramètre inconnu.")
        for key, values in params.items():
            if len(values) != 1:
                raise HttpError(400, "invalid_parameters", f"Paramètre répété : {key}.")
        limit = 50
        if "limit" in params:
            limit = self._parse_int_param(params["limit"][0], "limit", 1, 200)
        offset = 0
        if "offset" in params:
            offset = self._parse_int_param(params["offset"][0], "offset", 0, None)
        include_payload = False
        if "include_payload" in params:
            value = params["include_payload"][0]
            if value == "true":
                include_payload = True
            elif value == "false":
                include_payload = False
            else:
                raise HttpError(400, "invalid_parameters", "include_payload invalide.")
        return {
            "limit": limit,
            "offset": offset,
            "include_payload": include_payload,
        }

    def _parse_int_param(self, value: str, name: str, lo: int, hi: int | None) -> int:
        if not isinstance(value, str) or not value.isdigit():
            raise HttpError(400, "invalid_parameters", f"{name} invalide.")
        parsed = int(value)
        if parsed < lo or (hi is not None and parsed > hi):
            raise HttpError(400, "invalid_parameters", f"{name} invalide.")
        return parsed

    # --- réponses -------------------------------------------------------------

    def _send_bytes(
        self, status: int, body: bytes, content_type: str, send_body: bool = True
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        if send_body:
            self.wfile.write(body)

    def _send_json(self, status: int, obj: dict, send_body: bool = True) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status, body, "application/json; charset=utf-8", send_body=send_body)

    def _send_error(self, status: int, code: str, message: str, send_body: bool = True) -> None:
        self._send_json(
            status,
            {"ok": False, "data": None, "error": {"code": code, "message": message}},
            send_body=send_body,
        )


class VivariumHTTPServer(http.server.HTTPServer):
    """Serveur HTTP local mono-thread portant la base et le jeton.

    Cycle de vie explicite (C-3) : `_serving` indique si `serve_forever` est
    actif. `shutdown()` ne bloque que si une boucle de service est réellement
    en cours ; sinon il retourne immédiatement (idempotent, borné).
    """

    def __init__(
        self, server_address: tuple[str, int], db_path: Path, token: str
    ) -> None:
        self.db_path = Path(db_path)
        self.token = token
        self._serving = False
        super().__init__(server_address, VivariumRequestHandler)

    def serve_forever(self, poll_interval: float = 0.5) -> None:
        self._serving = True
        try:
            super().serve_forever(poll_interval)
        finally:
            self._serving = False

    def shutdown(self) -> None:
        # Ne bloque jamais si aucune boucle serve_forever n'est active.
        if self._serving:
            super().shutdown()

    def server_close(self) -> None:
        self._serving = False
        super().server_close()


def create_server(
    db_path: Path, host: str = "127.0.0.1", port: int = 0
) -> VivariumHTTPServer:
    """Crée un serveur local validé, sans démarrer l'écoute.

    Refuse toute adresse de liaison autre que `127.0.0.1`. Valide le port
    (entier, non booléen, 0-65535). Valide la base en lecture (sans migration
    ni création). Génère le jeton local au démarrage.
    """
    if host != "127.0.0.1":
        raise WebServerError(
            f"adresse de liaison non autorisée : {host!r} (seul 127.0.0.1)"
        )
    if isinstance(port, bool) or not isinstance(port, int):
        raise WebServerError(f"port invalide : {port!r}")
    if port < 0 or port > 65535:
        raise WebServerError(f"port hors plage : {port}")
    _validate_db(db_path)
    token = secrets.token_urlsafe(32)
    return VivariumHTTPServer((host, port), db_path, token)


def serve(server: VivariumHTTPServer) -> None:
    """Lance la boucle d'écoute (bloquante).

    Marque le serveur comme en service avant `serve_forever` afin qu'un
    `shutdown` concurrent ne bloque pas (C-3).
    """
    server._serving = True
    try:
        server.serve_forever()
    finally:
        server._serving = False


def shutdown(server: VivariumHTTPServer) -> None:
    """Arrête proprement le serveur et libère le socket (idempotent, borné)."""
    server.shutdown()
    server.server_close()
