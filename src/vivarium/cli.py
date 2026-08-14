"""Interface en ligne de commande du vivarium (Phase 1).

Commandes :
- `init`   : initialise un nouveau monde de développement ;
- `status` : inspecte l'état général du monde.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import threading
import time

from . import __version__
from .db import connect_database
from .migrations import ensure_schema
from .settings import Settings
from .world import WORLD_DEFAULT_NAME, WorldEngine, get_status
from .character import upgrade_development_world
from .needs import upgrade_dev_needs
from .activities import upgrade_dev_activities
from .simulation import upgrade_dev_profiles


def _resolve_db_path(args_db: str | None) -> Path:
    if args_db:
        return Path(args_db).resolve()
    return Settings().db_path


def _run_init(conn, args) -> int:
    engine = WorldEngine(conn)
    worlds = engine.list_worlds()
    if worlds:
        if not getattr(args, "force", False):
            print(
                "Un monde existe déjà. Utilisez --force pour réinitialiser le monde "
                "de développement (écrase la base locale de développement).",
                file=__import__("sys").stderr,
            )
            return 2
        db_path = _resolve_db_path(getattr(args, "db", None))
        conn.close()
        _delete_dev_db(db_path)
        conn = connect_database(db_path)
        ensure_schema(conn)
        engine = WorldEngine(conn)
    world = engine.init_world(name=args.name)
    print(f"Monde initialisé : id={world['id']} name={world['name']!r}")
    print(f"  statut       : {world['status']}")
    print("  lieux        : 9 (salon, cuisine, salle de bain, cour, couloir, 4 chambres)")
    print("  objets       : table, chaise, lit (seed de test, non définitif)")
    print("  personnages  : character_1..4 (provisoires, chambres 1..4)")
    return 0


def _delete_dev_db(db_path: Path) -> None:
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(db_path) + suffix)
        if p.exists():
            p.unlink()


def _run_upgrade_dev(conn) -> int:
    """Ajoute les quatre identités provisoires au monde local (non destructif).

    Ne déduit le caractère développement d'aucun nom : la commande cible
    explicitement le monde local configuré et n'insère que les personnages
    manquants. Idempotente : une seconde exécution n'écrit ni événement si les
    quatre existent déjà.
    """
    engine = WorldEngine(conn)
    worlds = engine.list_worlds()
    if not worlds:
        print("Aucun monde initialisé : rien à faire.", file=__import__("sys").stderr)
        return 1
    world = worlds[0]
    print(f"Monde cible : id={world['id']} ({world['name']!r})")
    print("Ajout des 4 identités provisoires de développement (character_1..4)")
    print("  - personnages manquants uniquement ; aucun existant modifié/remplacé")
    added = upgrade_development_world(conn, world["id"])
    if added:
        print(f"Personnages ajoutés : {', '.join(added)}")
    else:
        print("Personnages : aucun ajout (les quatre identités existent déjà).")
    needs = upgrade_dev_needs(conn, world["id"])
    if needs["definitions_added"] or needs["states_added"]:
        print(
            f"Besoins ajoutés : {needs['definitions_added']} définitions, "
            f"{needs['states_added']} états"
        )
    else:
        print("Besoins : aucun ajout (mise à niveau idempotente).")
    acts = upgrade_dev_activities(conn, world["id"])
    if acts["definitions_created"] or acts["rules_created"]:
        print(
            f"Activités ajoutées : {acts['definitions_created']} définitions, "
            f"{acts['rules_created']} règles de lieu"
        )
    else:
        print("Activités : aucun ajout (mise à niveau idempotente).")
    added_profiles = upgrade_dev_profiles(conn, world["id"])
    print(
        f"Profils (neutres) ajoutés : {added_profiles}"
        if added_profiles
        else "Profils : aucun ajout (mise à niveau idempotente)."
    )
    return 0


def _run_status(conn) -> int:
    status = get_status(conn)
    if not status["present"]:
        print(status["message"])
        return 1
    w = status["world"]
    print(f"Monde : id={w['id']} name={w['name']!r} statut={w['status']}")
    print(f"Version de schéma (registre migrations) : {status['schema_version']}")
    clock = status["clock"]
    print(f"Horloge canonique : {clock['simulated_now'] if clock else 'n/d'}")
    integrity = status["integrity_check"]
    print(
        "Integrity check : "
        + ("ok" if integrity == ["ok"] else f"anomalies {integrity}")
    )
    fk = status["foreign_key_check"]
    print(f"Foreign key check : {'aucune violation' if not fk else f'{len(fk)} violation(s)'}")
    counts = status["counts"]
    c = counts
    print(
        f"Compteurs : lieux={c['locations']} objets={c['objects']} "
        f"personnages={c['characters']} événements={c['events']}"
    )
    return 0


def _run_llm_status() -> int:
    """Teste la connexion locale sans ouvrir ni modifier une base de monde."""
    from .cognition import CognitionError, LMStudioProvider, LocalLLMSettings

    try:
        settings = LocalLLMSettings.from_environment(require_model=False)
        models = LMStudioProvider(settings).list_models()
    except CognitionError as exc:
        print(f"LLM local : {exc.code} — {exc}", file=__import__("sys").stderr)
        return 2
    print(f"LLM local : connecté à {settings.base_url}")
    print(f"Modèle configuré : {settings.model_id or 'aucun'}")
    print("Modèles chargés : " + (", ".join(models) if models else "aucun"))
    if not settings.model_id:
        print("Configure VIVARIUM_LLM_MODEL avec un identifiant ci-dessus.", file=__import__("sys").stderr)
        return 1
    if settings.model_id not in models:
        print("Attention : le modèle configuré n'est pas chargé dans LM Studio.", file=__import__("sys").stderr)
        return 1
    return 0


def _run_mvp_preflight(db_path: Path, world_id: int | None) -> int:
    """Contrôle une base existante en lecture seule, sans migration ni LLM."""
    from .mvp_preflight import MVPPreflightError, inspect_mvp_preflight

    if not db_path.is_file():
        print(f"Prévol MVP : base introuvable : {db_path}", file=__import__("sys").stderr)
        return 2
    try:
        uri = db_path.resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        try:
            report = inspect_mvp_preflight(conn, world_id=world_id)
        finally:
            conn.close()
    except (sqlite3.DatabaseError, MVPPreflightError) as exc:
        print(f"Prévol MVP : impossible : {exc}", file=__import__("sys").stderr)
        return 2
    print(f"Prévol MVP — monde : {report.world_name or 'non sélectionné'}")
    for check in report.checks:
        marker = "OK" if check.passed else "ECHEC"
        print(f"  [{marker:<5}] {check.key:<24} {check.detail}")
    print(f"Verdict : {'prêt structurellement' if report.healthy else 'non prêt — aucune correction appliquée'}")
    return 0 if report.healthy else 1


def _run_mvp_init(db_path: Path, name: str) -> int:
    """Crée une unique résidence alpha par les services réels, jamais par seed SQL."""
    from .integration_world import IntegrationWorldService
    from .mvp_preflight import inspect_mvp_preflight

    if db_path.exists():
        print(
            f"Initialisation MVP : la cible existe déjà : {db_path}",
            file=__import__("sys").stderr,
        )
        return 2
    conn = connect_database(db_path)
    try:
        ensure_schema(conn)
        world = IntegrationWorldService(conn).create_initial_world(name=name)
        report = inspect_mvp_preflight(conn, world_id=world["id"])
    except (sqlite3.Error, ValueError) as exc:
        print(f"Initialisation MVP : échec : {exc}", file=__import__("sys").stderr)
        return 2
    finally:
        conn.close()
    if not report.healthy:
        print("Initialisation MVP : prévol en échec; monde non présenté.", file=__import__("sys").stderr)
        return 1
    print(f"Monde MVP créé : id={world['id']} nom={world['name']!r}")
    print(f"Base : {db_path.resolve()}")
    print("Prévol : prêt structurellement")
    return 0


def _run_mvp_runtime(
    db_path: Path,
    world_id: int | None,
    *,
    enable_local_llm: bool,
    port: int,
    tick_seconds: float,
    max_ticks: int,
    guardian_interval: int,
    official_checkout_root: Path | None = None,
    official_runtime_head: str | None = None,
    official_product_head: str | None = None,
) -> int:
    """Lance le runtime alpha et le tableau local jusqu'à Ctrl+C ou la borne."""
    from .cognition import LMStudioProvider, LocalLLMSettings
    from .mvp_preflight import inspect_mvp_preflight
    from .mvp_runtime import MVPRuntime
    from .official_runtime import OfficialRuntimeError, validate_official_world
    from .runtime_provenance import RuntimeProvenanceError, verify_runtime_provenance
    from .runtime_session import RuntimeSessionService
    from .guardian import LocalGuardian
    from .scene_turn import LMStudioSceneTurnProvider
    from .simulation import SimulationLimitError
    from .telemetry import RuntimeOutcomeLog
    from .util import Clock
    from .world_rules import WorldRuleService
    from .web import WebServerError, create_server, serve, shutdown

    official = any(value is not None for value in (
        official_checkout_root, official_runtime_head, official_product_head,
    ))
    provenance = None
    if official:
        if official_checkout_root is None or official_runtime_head is None:
            print(
                "Rodage officiel : preuve de checkout/RUNTIME_HEAD incomplète.",
                file=__import__("sys").stderr,
            )
            return 2
        try:
            provenance = verify_runtime_provenance(
                expected_checkout_root=official_checkout_root,
                expected_runtime_head=official_runtime_head,
                expected_product_head=official_product_head,
            )
        except RuntimeProvenanceError as exc:
            print(f"Rodage officiel : lancement refusé ({exc.code}) : {exc}", file=__import__("sys").stderr)
            return 2

    if not db_path.is_file():
        print(f"Runtime MVP : base introuvable : {db_path}", file=__import__("sys").stderr)
        return 2
    if not isinstance(port, int) or isinstance(port, bool) or not 0 <= port <= 65535:
        print("Runtime MVP : port invalide", file=__import__("sys").stderr)
        return 2
    if not isinstance(tick_seconds, (float, int)) or not 0.25 <= tick_seconds <= 60:
        print("Runtime MVP : intervalle invalide", file=__import__("sys").stderr)
        return 2
    if not isinstance(max_ticks, int) or isinstance(max_ticks, bool) or not 0 <= max_ticks <= 100_000:
        print("Runtime MVP : borne de ticks invalide", file=__import__("sys").stderr)
        return 2
    if not isinstance(guardian_interval, int) or isinstance(guardian_interval, bool) \
            or not 60 <= guardian_interval <= 86400:
        print("Runtime MVP : intervalle du gardien invalide", file=__import__("sys").stderr)
        return 2
    conn = connect_database(db_path)
    server = None
    thread = None
    runtime = None
    session_service = None
    session_id = None
    validation = None
    protective_stop = False
    from .diagnostics import DiagnosticRecorder
    diagnostics = DiagnosticRecorder.from_environment()
    try:
        ensure_schema(conn)
        report = inspect_mvp_preflight(conn, world_id=world_id)
        if not report.healthy:
            print("Runtime MVP : prévol en échec; lancement refusé.", file=__import__("sys").stderr)
            for check in report.failures:
                print(f"  {check.key} : {check.detail}", file=__import__("sys").stderr)
            return 1
        if official:
            try:
                validation = validate_official_world(
                    conn, report.world_id, database_path=db_path, provenance=provenance,
                )
            except OfficialRuntimeError as exc:
                print(f"Rodage officiel : lancement refusé ({exc.code}) : {exc}", file=__import__("sys").stderr)
                return 1
        # Le port est réservé avant de muter la session : deux runtimes locaux
        # ne peuvent pas se déclarer propriétaires du même monde par accident.
        server = create_server(db_path, host="127.0.0.1", port=port)
        session_service = RuntimeSessionService(conn)
        session_start = session_service.start(report.world_id)
        session_id = session_start.session_id
        if session_start.recovered_session_id is not None:
            print(
                "Session interrompue détectée : horloge récupérée à "
                f"{session_start.canonical_at} sans rattrapage hors ligne."
            )
        rules = WorldRuleService(conn).install_standard_residence_rules(report.world_id)
        if rules["changed"]:
            print(
                "Règles du monde mises à niveau : "
                f"+{rules['activities_added']} activités, "
                f"+{rules['activity_locations_added']} autorisations."
            )
        cognition_provider = scene_provider = interpretation_provider = appraisal_provider = affect_provider = None
        if enable_local_llm:
            settings = LocalLLMSettings.from_environment()
            cognition_provider = LMStudioProvider(settings)
            scene_provider = LMStudioSceneTurnProvider(settings, diagnostics=diagnostics)
            from .social_interpretation_provider import LMStudioSocialInterpretationProvider
            interpretation_provider = LMStudioSocialInterpretationProvider(settings)
            from .social_appraisal_provider import LMStudioSocialAppraisalProvider
            appraisal_provider = LMStudioSocialAppraisalProvider(settings)
            from .scc3a_affect_provider import LMStudioSCC3AAffectProvider
            affect_provider = LMStudioSCC3AAffectProvider(settings)
        runtime = MVPRuntime(
            conn, report.world_id, cognition_provider=cognition_provider, scene_provider=scene_provider,
            interpretation_provider=interpretation_provider,
            appraisal_provider=appraisal_provider,
            affect_provider=affect_provider,
            diagnostics=diagnostics,
            simulation_contract="active" if official else "legacy",
        )
        guardian = LocalGuardian(
            conn,
            report.world_id,
            log_path=db_path.parent.parent / "logs" / "guardian.jsonl",
            model_lister=cognition_provider,
            service_probe=lambda: thread is not None and thread.is_alive(),
            interval_seconds=guardian_interval,
            runtime_session_id=session_id,
        )
        outcome_log = RuntimeOutcomeLog(
            db_path.parent.parent / "logs" / "runtime_outcomes.jsonl"
        )
        thread = threading.Thread(target=serve, args=(server,), daemon=True)
        thread.start()
        actual_port = server.server_address[1]
        print(f"Runtime MVP actif — tableau de contrôle : http://127.0.0.1:{actual_port}/")
        if official and validation is not None:
            for key, value in {
                **validation.as_dict(),
                "RUNTIME_SESSION_ID": session_id,
            }.items():
                print(f"{key}={value}")
        print("Ctrl+C arrête proprement le runtime et interrompt les scènes ouvertes.")
        print(f"LLM local : {'activé' if enable_local_llm else 'désactivé (routines déterministes seulement)'}")
        ticks = 0
        last_session_heartbeat = time.monotonic()
        while max_ticks == 0 or ticks < max_ticks:
            tick = runtime.run_once()
            ticks += 1
            if time.monotonic() - last_session_heartbeat >= 10.0:
                session_service.heartbeat(session_id)
                last_session_heartbeat = time.monotonic()
            arrival = tick.arrival
            if arrival and arrival.character_key:
                if arrival.routed is None:
                    arrival_state = "sans appel"
                elif arrival.routed.provider_error_code:
                    arrival_state = "LLM indisponible"
                elif arrival.routed.turn is None:
                    arrival_state = arrival.routed.admission.verdict.reason_code
                else:
                    arrival_state = arrival.routed.turn.decision.action
                suffix = " (suite à venir)" if arrival.pending else ""
                print(f"[tick {ticks}] arrivée {arrival.character_key} : {arrival_state}{suffix}")
                routed = arrival.routed
                outcome_log.append(
                    checked_at=Clock().now_iso(), cycle="arrival",
                    character=arrival.character_key, outcome=arrival_state,
                    provider_error=None if routed is None else routed.provider_error_code,
                    validation_error=None if routed is None or routed.turn is None
                    or routed.turn.validation is None else routed.turn.validation.reason_code,
                )
            autonomy = tick.autonomy
            if autonomy and autonomy.character_key:
                if autonomy.routed is None:
                    autonomy_state = autonomy.detail_code or "sans appel"
                elif autonomy.routed.provider_error_code:
                    autonomy_state = autonomy.routed.provider_error_code
                elif autonomy.routed.turn is None:
                    autonomy_state = autonomy.routed.admission.verdict.reason_code
                else:
                    turn = autonomy.routed.turn
                    autonomy_state = turn.decision.action
                    if turn.validation is not None:
                        autonomy_state += f"/{turn.validation.status}"
                print(f"[tick {ticks}] autonomie {autonomy.character_key} : {autonomy_state}")
                routed = autonomy.routed
                outcome_log.append(
                    checked_at=Clock().now_iso(), cycle="autonomy",
                    character=autonomy.character_key, outcome=autonomy_state,
                    provider_error=None if routed is None else routed.provider_error_code,
                    validation_error=None if routed is None or routed.turn is None
                    or routed.turn.validation is None else routed.turn.validation.reason_code,
                )
            animal = tick.non_sapient
            if animal and animal.character_key:
                print(
                    f"[tick {ticks}] non-sapient {animal.character_key} : "
                    f"{animal.selected_action}/{animal.outcome} "
                    f"cible={animal.target_key or '-'} motif={animal.reason_code}"
                )
                outcome_log.append(
                    checked_at=Clock().now_iso(), cycle="non_sapient",
                    character=animal.character_key,
                    outcome=f"{animal.selected_action}/{animal.outcome}",
                    provider_error=None, validation_error=animal.reason_code,
                )
            social = tick.social
            if social and (social.opened_scene_keys or social.closed_scene_keys or social.interrupted_scene_keys or social.turn):
                action = social.turn.decision.action if social.turn and social.turn.decision else "-"
                print(f"[tick {ticks}] scènes +{len(social.opened_scene_keys)} -{len(social.closed_scene_keys)} !{len(social.interrupted_scene_keys)} tour={action}")
                if social.turn is not None:
                    outcome_log.append(
                        checked_at=Clock().now_iso(), cycle="social", character=None,
                        outcome=action,
                        provider_error=social.turn.provider_error_code,
                        validation_error=social.turn.validation_error_code,
                    )
            guardian_report = guardian.run_if_due()
            if guardian_report is not None:
                print(
                    f"[gardien] {guardian_report.status} - "
                    f"{guardian_report.checked_at} - logs/guardian.jsonl"
                )
                if guardian_report.status == "CRITIQUE":
                    print(
                        "Runtime MVP : arrêt protecteur demandé par le gardien local.",
                        file=__import__("sys").stderr,
                    )
                    protective_stop = True
                    return 3
            time.sleep(tick_seconds)
    except KeyboardInterrupt:
        print("Arrêt demandé.")
    except (ValueError, WebServerError, SimulationLimitError, sqlite3.Error) as exc:
        print(f"Runtime MVP : arrêt sur erreur explicite : {exc}", file=__import__("sys").stderr)
        return 2
    finally:
        try:
            if runtime is not None and not protective_stop:
                runtime.shutdown()
        finally:
            try:
                if session_service is not None and session_id is not None:
                    session_service.stop(session_id, protective=protective_stop)
            finally:
                if server is not None:
                    shutdown(server)
                if thread is not None:
                    thread.join(timeout=5)
                conn.close()
    print("Runtime MVP arrêté proprement.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vivarium", description="Vivarium social artificiel")
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="Initialise un nouveau monde de développement.")
    p_init.add_argument("--name", default=WORLD_DEFAULT_NAME)
    p_init.add_argument("--db", default=None, help="Chemin de la base (défaut : data/world.dev.sqlite).")
    p_init.add_argument("--force", action="store_true",
                        help="Réinitialise la base locale de développement.")

    p_status = sub.add_parser("status", help="Inspecte l'état général du monde.")
    p_status.add_argument("--db", default=None, help="Chemin de la base.")

    p_upgrade = sub.add_parser(
        "upgrade-dev",
        help="Ajoute les 4 identités provisoires de développement au monde local "
        "(mise à niveau non destructive, idempotente).",
    )
    p_upgrade.add_argument("--db", default=None, help="Chemin de la base.")

    sub.add_parser("llm-status", help="Vérifie LM Studio local et le modèle chargé (lecture seule).")
    p_preflight = sub.add_parser("mvp-preflight", help="Contrôle une base MVP existante en lecture seule, sans LLM.")
    p_preflight.add_argument("--db", required=True, help="Chemin de la base existante à contrôler.")
    p_preflight.add_argument("--world-id", type=int, default=None, help="Identifiant requis si la base contient plusieurs mondes.")
    p_mvp_init = sub.add_parser("mvp-init", help="Crée une nouvelle résidence MVP par les services canoniques.")
    p_mvp_init.add_argument("--db", required=True, help="Nouvelle base cible; elle doit être absente.")
    p_mvp_init.add_argument("--name", default="Résidence Vivarium", help="Nom initial du monde MVP.")
    p_mvp_run = sub.add_parser("mvp-run", help="Lance le runtime MVP et le tableau de contrôle local.")
    p_mvp_run.add_argument("--db", required=True, help="Base MVP existante et validée.")
    p_mvp_run.add_argument("--world-id", type=int, default=None, help="Cible explicite si la base contient plusieurs mondes.")
    p_mvp_run.add_argument("--enable-local-llm", action="store_true", help="Autorise les appels Gemma locaux bornés.")
    p_mvp_run.add_argument("--port", type=int, default=8765, help="Port local du tableau de contrôle (défaut : 8765).")
    p_mvp_run.add_argument("--tick-seconds", type=float, default=2.0, help="Intervalle de boucle, entre 0,25 et 60 s.")
    p_mvp_run.add_argument("--max-ticks", type=int, default=0, help="0 = jusqu'à Ctrl+C; borne utile pour un essai contrôlé.")

    p_mvp_run.add_argument(
        "--guardian-interval", type=int, default=3600,
        help="Intervalle du gardien local en secondes (défaut : 3600).",
    )
    p_rodage_run = sub.add_parser(
        "rodage-run",
        help="Lance un rodage officiel avec preuve du checkout et du moteur actif.",
    )
    p_rodage_run.add_argument("--db", required=True, help="Base officielle existante et préparée.")
    p_rodage_run.add_argument("--world-id", type=int, default=None)
    p_rodage_run.add_argument("--checkout-root", type=Path, required=True)
    p_rodage_run.add_argument("--runtime-head", required=True)
    p_rodage_run.add_argument("--product-head", default=None)
    p_rodage_run.add_argument("--enable-local-llm", action="store_true")
    p_rodage_run.add_argument("--port", type=int, default=8765)
    p_rodage_run.add_argument("--tick-seconds", type=float, default=2.0)
    p_rodage_run.add_argument("--max-ticks", type=int, default=0)
    p_rodage_run.add_argument("--guardian-interval", type=int, default=3600)

    args = parser.parse_args(argv)

    from .logging_setup import configure_logging

    configure_logging(Settings())

    if not args.command:
        print(f"vivarium-social {__version__}")
        return 0

    if args.command == "llm-status":
        return _run_llm_status()
    if args.command == "mvp-preflight":
        return _run_mvp_preflight(Path(args.db), args.world_id)
    if args.command == "mvp-init":
        return _run_mvp_init(Path(args.db), args.name)
    if args.command == "mvp-run":
        return _run_mvp_runtime(
            Path(args.db), args.world_id,
            enable_local_llm=args.enable_local_llm,
            port=args.port,
            tick_seconds=args.tick_seconds,
            max_ticks=args.max_ticks,
            guardian_interval=args.guardian_interval,
        )
    if args.command == "rodage-run":
        return _run_mvp_runtime(
            Path(args.db), args.world_id,
            enable_local_llm=args.enable_local_llm,
            port=args.port,
            tick_seconds=args.tick_seconds,
            max_ticks=args.max_ticks,
            guardian_interval=args.guardian_interval,
            official_checkout_root=args.checkout_root,
            official_runtime_head=args.runtime_head,
            official_product_head=args.product_head,
        )

    db_path = _resolve_db_path(getattr(args, "db", None))
    conn = connect_database(db_path)
    try:
        ensure_schema(conn)
        if args.command == "init":
            return _run_init(conn, args)
        if args.command == "status":
            return _run_status(conn)
        if args.command == "upgrade-dev":
            return _run_upgrade_dev(conn)
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return 0
