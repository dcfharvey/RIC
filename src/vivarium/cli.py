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


def _run_llm_smoke(character_key: str) -> int:
    """Exécute un tour local dans une base mémoire, jamais dans un monde réel."""
    from .cognition import CognitionError, LocalLLMSettings
    from .cognition_smoke import run_local_cognition_smoke

    try:
        report = run_local_cognition_smoke(
            LocalLLMSettings.from_environment(), character_key=character_key
        )
    except CognitionError as exc:
        print(f"Essai LLM local : {exc.code} — {exc}", file=__import__("sys").stderr)
        return 2
    print(f"Essai LLM local : modèle={report.model_id} personnage={report.character_key}")
    print(f"  décision     : {report.decision}")
    if report.connector_key:
        print(f"  passage      : {report.connector_key} -> {report.target_location_key}")
    print(f"  validation   : {report.validation_status or 'aucune'}")
    if report.validation_reason:
        print(f"  raison       : {report.validation_reason}")
    print(f"  événement    : {report.event_type or 'aucun'}")
    print(f"  sain         : {'oui' if report.healthy else 'non'} (base mémoire jetable)")
    return 0 if report.healthy else 1


def _run_living_bench(max_ticks: int, verbose: bool) -> int:
    """Affiche chaque tick d'un essai autonome isolé, avec le LLM local réel."""
    from .cognition import CognitionError, LMStudioProvider, LocalLLMSettings
    from .cognition_policy import CognitionCallLimits
    from .living_bench import run_living_bench

    try:
        settings = LocalLLMSettings.from_environment()
        print(f"Banc vivant jetable — modèle : {settings.model_id}")
        print("Aucun monde persistant n'est ouvert.\n")
        def show(tick):
            counts = {}
            for item in tick.outcomes:
                counts[item.outcome] = counts.get(item.outcome, 0) + 1
            summary = ", ".join(f"{kind}={count}" for kind, count in sorted(counts.items())) or "aucune source"
            print(f"[tick] jusqu'à l'événement {tick.through_event_seq} — {summary}")
            visible = tick.outcomes if verbose else tuple(item for item in tick.outcomes if item.outcome != "unperceived")
            for item in visible:
                detail = f" ({item.detail_code})" if item.detail_code else ""
                print(f"  {item.character_key:<8} event_{item.source_event_seq:<3} {item.outcome}{detail}")
        report = run_living_bench(LMStudioProvider(settings), CognitionCallLimits(0, 3600, 20), max_ticks=max_ticks, on_tick=show)
    except (CognitionError, ValueError) as exc:
        print(f"Banc vivant : {getattr(exc, 'code', 'invalid_request')} — {exc}", file=__import__('sys').stderr)
        return 2
    print(f"\nAudit structurel : {'sain' if not report.audit_findings['bad_causes'] else 'anomalie'}")
    print(f"Digest final : état canonique calculé après {len(report.ticks)} tick(s)")
    return 0


def _run_llm_calibration(trials: int, character: str) -> int:
    """Mesure des tours LLM réels répétés, sans monde persistant."""
    from .cognition import CognitionError, LMStudioProvider, LocalLLMSettings
    from .local_llm_calibration import LocalCalibrationError, run_local_cognition_calibration

    try:
        settings = LocalLLMSettings.from_environment()
        report = run_local_cognition_calibration(
            LMStudioProvider(settings), settings.model_id, trials=trials, character_key=character
        )
    except (CognitionError, LocalCalibrationError, ValueError) as exc:
        print(f"Calibration LLM : {getattr(exc, 'code', 'invalid_request')} — {exc}", file=__import__('sys').stderr)
        return 2
    print(f"Calibration LLM jetable — modèle : {report.model_id}, personnage : {report.character_key}")
    for trial in report.trials:
        validation = "aucune" if trial.validation_status is None else trial.validation_status
        detail = trial.provider_error_code or trial.validation_reason or ""
        suffix = f" ({detail})" if detail else ""
        print(f"  essai {trial.number:>2}: {trial.outcome:<14} {trial.elapsed_ms:>5} ms  décision={trial.decision or '-'}  validation={validation}{suffix}")
    print(f"Médiane : {report.median_elapsed_ms} ms — issues : {report.outcome_counts} — décisions : {report.decision_counts}")
    print(f"Verdict : {'sain' if report.healthy else 'anomalie explicite'} (bases mémoire jetables)")
    return 0 if report.healthy else 1


def _run_social_interpretation_bench(level: str, trials: int | None, model_id: str | None,
                                     scenario_ids: list[str], report_path: str | None) -> int:
    from .social_interpretation_bench import BenchError, run_bench, run_t2a_campaign, write_report, write_t2a_campaign
    from .social_interpretation_provider import DeterministicInterpretationProvider, LMStudioSocialInterpretationProvider

    try:
        if level == "T0":
            provider = DeterministicInterpretationProvider(
                {"schema_version": 1, "understanding_status": "ambiguous",
                 "meaning_hypotheses": ["Lecture A", "Lecture B"], "motive_hypotheses": []},
                model_id=model_id or "deterministic-bench-model",
            )
        else:
            from .cognition import LocalLLMSettings
            settings = LocalLLMSettings.from_environment(require_model=level == "T2")
            if model_id:
                settings = LocalLLMSettings(settings.base_url, model_id, settings.api_token, settings.timeout_seconds)
            if level == "T2" and settings.model_id != "google/gemma-4-12b-qat":
                raise BenchError("T2a exige google/gemma-4-12b-qat", code="t2_model_mismatch")
            provider = LMStudioSocialInterpretationProvider(settings)
        effective_trials = trials if trials is not None else (5 if level == "T2" else 1)
        if level == "T2":
            if scenario_ids:
                raise BenchError("T2a exécute la matrice complète", code="t2_scenario_override_forbidden")
            report = run_t2a_campaign(provider, trials=effective_trials)
            principal = report_path or "data/bench/scc1b2_t2a_gemma4_12b.json"
            write_t2a_campaign(report, principal, Path(principal).with_name("scc1b2_t2a_review.json"))
            payload = report.as_dict()
        else:
            report = run_bench(provider, level=level, trials=effective_trials,
                               scenario_ids=tuple(scenario_ids) or None)
            if report_path:
                write_report(report, report_path)
            payload = report.as_dict()
    except (BenchError, ValueError) as exc:
        print(f"Banc SCC-1B2 : {getattr(exc, 'code', 'invalid_request')} — {exc}", file=__import__('sys').stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not payload["hard_blockers"] else 1


def _run_scene_smoke() -> int:
    """Teste un tour de parole local réel dans une scène mémoire jetable."""
    from .cognition import CognitionError, LocalLLMSettings
    from .scene_turn import SceneTurnError
    from .scene_turn_smoke import run_local_scene_turn_smoke

    try:
        settings = LocalLLMSettings.from_environment()
        report = run_local_scene_turn_smoke(settings)
    except (CognitionError, SceneTurnError, ValueError) as exc:
        print(f"Essai de scène : {getattr(exc, 'code', 'invalid_request')} — {exc}", file=__import__('sys').stderr)
        return 2
    print(f"Essai de scène jetable — modèle : {report.model_id}")
    print(f"  décision     : {report.decision or '-'}")
    print(f"  acte          : {report.act_kind or '-'}")
    print(f"  parole        : {report.content or '-'}")
    detail = report.provider_error_code or report.validation_error_code or report.deferred_reason_code or "aucun"
    print(f"  anomalie      : {detail}")
    print(f"  sain          : {'oui' if report.healthy else 'non'} (base mémoire jetable)")
    return 0 if report.healthy else 1


def _run_scene_bench(max_turns: int) -> int:
    """Affiche une courte conversation locale, strictement jetable."""
    from .cognition import CognitionError, LocalLLMSettings
    from .cognition_policy import CognitionCallLimits
    from .scene_bench import run_scene_bench
    from .scene_turn import LMStudioSceneTurnProvider, SceneTurnError
    from .scene_scheduler import SceneSchedulerError

    try:
        settings = LocalLLMSettings.from_environment()
        report = run_scene_bench(
            LMStudioSceneTurnProvider(settings), CognitionCallLimits(0, 3_600, max_turns), max_turns=max_turns
        )
    except (CognitionError, SceneTurnError, SceneSchedulerError, ValueError) as exc:
        print(f"Banc de scène : {getattr(exc, 'code', 'invalid_request')} — {exc}", file=__import__('sys').stderr)
        return 2
    print(f"Banc de scène jetable — modèle : {settings.model_id}")
    for turn in report.turns:
        result = turn.result
        detail = result.provider_error_code or result.validation_error_code or result.deferred_reason_code or ""
        speech = "-" if result.speech is None else result.speech["content"]
        print(f"  tour {turn.opportunity.turn_number}: {turn.opportunity.speaker_key:<6} {result.decision.action if result.decision else '-':<10} {speech}" + (f" ({detail})" if detail else ""))
    print(f"Scène : {len(report.final_scene['acts'])} parole(s) — verdict : {'sain' if report.healthy else 'anomalie explicite'}")
    return 0 if report.healthy else 1


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
) -> int:
    """Lance le runtime alpha et le tableau local jusqu'à Ctrl+C ou la borne."""
    from .cognition import LMStudioProvider, LocalLLMSettings
    from .mvp_preflight import inspect_mvp_preflight
    from .mvp_runtime import MVPRuntime
    from .runtime_session import RuntimeSessionService
    from .guardian import LocalGuardian
    from .scene_turn import LMStudioSceneTurnProvider
    from .simulation import SimulationLimitError
    from .telemetry import RuntimeOutcomeLog
    from .util import Clock
    from .world_rules import WorldRuleService
    from .web import WebServerError, create_server, serve, shutdown

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
    protective_stop = False
    try:
        ensure_schema(conn)
        report = inspect_mvp_preflight(conn, world_id=world_id)
        if not report.healthy:
            print("Runtime MVP : prévol en échec; lancement refusé.", file=__import__("sys").stderr)
            for check in report.failures:
                print(f"  {check.key} : {check.detail}", file=__import__("sys").stderr)
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
        cognition_provider = scene_provider = None
        if enable_local_llm:
            settings = LocalLLMSettings.from_environment()
            cognition_provider = LMStudioProvider(settings)
            scene_provider = LMStudioSceneTurnProvider(settings)
        runtime = MVPRuntime(
            conn, report.world_id, cognition_provider=cognition_provider, scene_provider=scene_provider
        )
        guardian = LocalGuardian(
            conn,
            report.world_id,
            log_path=db_path.parent.parent / "logs" / "guardian.jsonl",
            model_lister=cognition_provider,
            service_probe=lambda: thread is not None and thread.is_alive(),
            interval_seconds=guardian_interval,
        )
        outcome_log = RuntimeOutcomeLog(
            db_path.parent.parent / "logs" / "runtime_outcomes.jsonl"
        )
        thread = threading.Thread(target=serve, args=(server,), daemon=True)
        thread.start()
        actual_port = server.server_address[1]
        print(f"Runtime MVP actif — tableau de contrôle : http://127.0.0.1:{actual_port}/")
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
    p_smoke = sub.add_parser(
        "llm-smoke", help="Teste un tour LLM réel dans une base mémoire jetable."
    )
    p_smoke.add_argument("--character", default="sophie", help="Résidente à utiliser pour l'essai (défaut : sophie).")
    p_living = sub.add_parser("living-bench", help="Affiche un essai autonome jetable avec le LLM local.")
    p_living.add_argument("--max-ticks", type=int, default=8, help="Nombre maximal de ticks (défaut : 8).")
    p_living.add_argument("--verbose", action="store_true", help="Affiche aussi chaque événement non perceptible.")
    p_calibration = sub.add_parser("llm-calibrate", help="Répète un tour LLM jetable pour mesurer le contrat et la latence.")
    p_calibration.add_argument("--trials", type=int, default=3, help="Nombre d'essais isolés (1 à 20, défaut : 3).")
    p_calibration.add_argument("--character", default="sophie", help="Résidente à utiliser (défaut : sophie).")
    p_social_bench = sub.add_parser("social-interpretation-bench", help="Banc SCC-1B2 jetable, sans runtime vivant.")
    p_social_bench.add_argument("--level", choices=("T0", "T1", "T2"), default="T0")
    p_social_bench.add_argument("--trials", type=int, default=None, help="Trials par scénario (T2a : 5 par défaut; sinon 1).")
    p_social_bench.add_argument("--model-id", default=None, help="Modèle T1 configuré; aucun secret n'est enregistré.")
    p_social_bench.add_argument("--scenario", action="append", default=[], help="ID B01 à B30; répétable.")
    p_social_bench.add_argument("--report", default=None, help="Chemin JSON du rapport technique jetable.")
    sub.add_parser("scene-smoke", help="Teste un tour de parole LLM dans une scène mémoire jetable.")
    p_scene_bench = sub.add_parser("scene-bench", help="Joue quelques tours sociaux LLM dans une scène jetable.")
    p_scene_bench.add_argument("--max-turns", type=int, default=4, help="Occasions de parole (1 à 20, défaut : 4).")
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

    args = parser.parse_args(argv)

    from .logging_setup import configure_logging

    configure_logging(Settings())

    if not args.command:
        print(f"vivarium-social {__version__}")
        return 0

    if args.command == "llm-status":
        return _run_llm_status()
    if args.command == "llm-smoke":
        return _run_llm_smoke(args.character)
    if args.command == "living-bench":
        return _run_living_bench(args.max_ticks, args.verbose)
    if args.command == "llm-calibrate":
        return _run_llm_calibration(args.trials, args.character)
    if args.command == "social-interpretation-bench":
        return _run_social_interpretation_bench(args.level, args.trials, args.model_id, args.scenario, args.report)
    if args.command == "scene-smoke":
        return _run_scene_smoke()
    if args.command == "scene-bench":
        return _run_scene_bench(args.max_turns)
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
