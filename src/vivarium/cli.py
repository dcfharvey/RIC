"""Interface en ligne de commande du vivarium (Phase 1).

Commandes :
- `init`   : initialise un nouveau monde de développement ;
- `status` : inspecte l'état général du monde.
"""

from __future__ import annotations

import argparse
from pathlib import Path

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
    sub.add_parser("scene-smoke", help="Teste un tour de parole LLM dans une scène mémoire jetable.")
    p_scene_bench = sub.add_parser("scene-bench", help="Joue quelques tours sociaux LLM dans une scène jetable.")
    p_scene_bench.add_argument("--max-turns", type=int, default=4, help="Occasions de parole (1 à 20, défaut : 4).")

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
    if args.command == "scene-smoke":
        return _run_scene_smoke()
    if args.command == "scene-bench":
        return _run_scene_bench(args.max_turns)

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
