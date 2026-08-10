"""SCC-1B2I: final FR/FR versus EN/EN language qualification bench."""
from __future__ import annotations

import argparse
import json
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .cognition import LocalLLMSettings, request_local_model
from .home_field_audit import HOME_FIELD_SCENARIOS, HomeFieldScenario, _snapshot_for
from .social_interpretation_bench import BenchScenario, _build_fixture, _safe_model_id, get_scenario_variants
from .social_interpretation_provider import SocialInterpretationContextBuilder, SocialInterpretationProviderError, SocialInterpretationSnapshot
from .system_prompt_language import EN_SYSTEM_PROMPT, FR_SYSTEM_PROMPT, MODELS, validate_interpretation_only

CONDITIONS = ("FR_FR", "EN_EN")
CONTROL_KEYS = (("B04", "negative"), ("B10", "supported"), ("B13", "accusation"), ("B15", "initial"), ("B16", "clarified"), ("B19", "contradictory"))
HELD_IDS = ("H03", "H07", "H08", "H10", "H12", "H13", "H15", "H16")
SCENARIO_IDS = ("G01", "G05", "G09", *HELD_IDS, "B04", "B10", "B13", "B15", "B16", "B19")
PLANNED_UNITS = 17
PLANNED_CALLS = len(MODELS) * len(CONDITIONS) * PLANNED_UNITS

TRANSLATIONS = {
    "Oui, ça me va.": "Yes, that works for me.",
    "On réserve la salle bleue.": "We're booking the blue room.",
    "On reporte la réunion à mardi.": "We're postponing the meeting until Tuesday.",
    "Tu veux venir avec nous ce soir ?": "Do you want to come with us tonight?",
    "Je dois me lever à cinq heures demain.": "I have to get up at five tomorrow.",
    "Sophie et Luna sont toutes deux dans la scène.": "Sophie and Luna are both in the scene.",
    "Elle m'a dit qu'elle viendrait plus tard.": "She told me she would come later.",
    "Je suis désolée que ça soit arrivé.": "I'm sorry that happened.",
    'Erika m\'a dit : "Luna a cassé la tasse."': 'Erika told me: "Luna broke the cup."',
    "Erika pense que la porte est verrouillée, mais je n'en sais rien.": "Erika thinks the door is locked, but I don't know.",
    "T'es un ange.": "You're an angel.",
    "Je ne suis pas fâchée.": "I'm not angry.",
    "Ça m'irrite encore.": "It still irritates me.",
    "Je vais vendre ton ordinateur. Je blague.": "I'm going to sell your computer. I'm joking.",
    "C'est... original.": "It's... original.",
    "Ce n'est pas vraiment mon style, mais merci d'y avoir pensé.": "I mean, it's not really my style, but thank you for thinking of it.",
    "Super.": "Great.",
    "Le projet vient d'être refusé.": "The project was rejected.",
    "Il fait froid ici.": "It's cold in here.",
    "La fenêtre est ouverte.": "The window is open.",
    "X a volé mon téléphone.": "X stole my phone.",
    "Tout va bien.": "Everything is fine.",
    "Je plaisantais; le problème demeure.": "I was joking; the problem remains.",
    "D'accord.": "Okay.",
    "La porte est ouverte.": "The door is open.",
    "La porte est fermée.": "The door is closed.",
}

TRANSLATION_AUDIT = [
    ("G01", "Oui, ça me va. / deux propositions", "Yes, that works for me. / two proposals", "ambiguous antecedent", "PASS", "PASS", "Two explicit prior proposals remain plausible."),
    ("G05", "invitation + réveil à cinq heures", "invitation + getting up at five", "indirect refusal", "PASS", "PASS", "The schedule remains a natural indirect response."),
    ("G09", "Elle m'a dit qu'elle viendrait plus tard.", "She told me she would come later.", "ambiguous pronouns", "PASS", "LIMITED", "English preserves pronoun ambiguity but has different discourse morphology."),
    ("H03", "Je suis désolée que ça soit arrivé.", "I'm sorry that happened.", "sympathy without confession", "PASS", "PASS", "Regret remains distinct from responsibility."),
    ("H07", 'Erika m\'a dit: "Luna a cassé la tasse."', 'Erika told me: "Luna broke the cup."', "reported-source hierarchy", "PASS", "PASS", "Quotation and reporting hierarchy are retained."),
    ("H08", "croyance d'Erika + ignorance de Sophie", "Erika's belief + Sophie's ignorance", "belief/source discipline", "PASS", "PASS", "Belief and uncertainty roles are explicit."),
    ("H10", "T'es un ange.", "You're an angel.", "figurative social formula", "PASS", "PASS", "Conventional figurative reading remains available."),
    ("H12", "irritation + Je ne suis pas fâchée.", "irritation + I'm not angry.", "contradictory self-report", "PASS", "PASS", "Natural contrast without forced synonymy."),
    ("H13", "Je vais vendre ton ordinateur. Je blague.", "I'm going to sell your computer. I'm joking.", "explicit joke marker", "PASS", "PASS", "The joke marker remains explicit."),
    ("H15/H16", "réserve puis clarification", "reserve then clarification", "revision", "PASS", "PASS", "The update remains a genuine clarification."),
    ("B04", "projet refusé + Super.", "rejected project + Great.", "pragmatic contradiction", "PASS", "PASS", "Direct counterpart."),
    ("B10", "froid + fenêtre ouverte", "cold + open window", "contextual implication", "PASS", "PASS", "Causal/contextual clue preserved."),
    ("B13", "X a volé mon téléphone.", "X stole my phone.", "assertion versus fact", "PASS", "PASS", "Required lexical item 'stole' is explicit."),
    ("B15/B16", "initial puis clarification", "initial then clarification", "revision", "PASS", "PASS", "Lineage and content update preserved."),
    ("B19", "porte ouverte et fermée", "door open and closed", "contradiction", "PASS", "PASS", "Both assertions remain present."),
]


def _units() -> tuple[tuple[str, str, Any], ...]:
    corrected = {s.scenario_id: s for s in (
        BenchScenario("G01", "corrected", "Oui, ça me va.", context_contents=("On réserve la salle bleue.", "On reporte la réunion à mardi."), select_context=True),
        BenchScenario("G05", "corrected", "Je dois me lever à cinq heures demain.", context_contents=("Tu veux venir avec nous ce soir ?",), select_context=True),
        BenchScenario("G09", "corrected", "Elle m'a dit qu'elle viendrait plus tard.", context_contents=("Sophie et Luna sont toutes deux dans la scène.",), select_context=True),
    )}
    held = {s.scenario_id: s for s in HOME_FIELD_SCENARIOS if s.scenario_id in HELD_IDS}
    units = [(sid, "corrected", corrected[sid]) for sid in ("G01", "G05", "G09")]
    for sid in ("H03", "H07", "H08", "H10", "H12", "H13"):
        units.append((sid, "default", held[sid]))
    units.extend((("H15", "initial", held["H15"]), ("H16", "revision", held["H16"])))
    units.extend((s.scenario_id, s.variant_id, s) for s in get_scenario_variants(CONTROL_KEYS))
    return tuple(units)


def _snapshot(item: Any):
    if isinstance(item, HomeFieldScenario):
        return _snapshot_for(item)
    fixture = _build_fixture(item)
    return fixture, SocialInterpretationContextBuilder(fixture.conn).build(fixture.world_id, "erika", "primary", selected_trace_request_keys=fixture.selected_keys)


def _translated_snapshot(snapshot: SocialInterpretationSnapshot) -> SocialInterpretationSnapshot:
    def convert(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {key: convert(item) for key, item in value.items()}
        if isinstance(value, list):
            return [convert(item) for item in value]
        if isinstance(value, tuple):
            return tuple(convert(item) for item in value)
        return TRANSLATIONS.get(value, value) if isinstance(value, str) else value
    # SocialInterpretationSnapshot freezes nested mappings as mappingproxy.  A
    # controlled recursive projection is sufficient and avoids mutating or
    # deep-copying proxy objects; only pre-registered linguistic string values
    # are translated.
    return SocialInterpretationSnapshot(data=convert(snapshot.data))


def run_model_condition(model_id: str, condition: str, output_dir: str | Path) -> dict[str, Any]:
    if model_id not in MODELS or condition not in CONDITIONS:
        raise ValueError("model or condition outside preregistration")
    settings = LocalLLMSettings.from_environment(require_model=False)
    settings = LocalLLMSettings(settings.base_url, model_id, settings.api_token, settings.timeout_seconds)
    prompt = FR_SYSTEM_PROMPT if condition == "FR_FR" else EN_SYSTEM_PROMPT
    results = []
    for scenario_id, variant_id, item in _units():
        fixture, snapshot = _snapshot(item)
        wire_snapshot = snapshot if condition == "FR_FR" else _translated_snapshot(snapshot)
        started = time.perf_counter(); raw = None
        record = {"model_id": model_id, "condition": condition, "scenario_id": scenario_id, "variant_id": variant_id, "repeat": 1, "snapshot_fingerprint": wire_snapshot.fingerprint, "source_snapshot_fingerprint": snapshot.fingerprint}
        try:
            raw = request_local_model(settings, system_prompt=prompt, input_text=wire_snapshot.wire)
            record.update(validate_interpretation_only(raw)); record["outcome"] = "valid_interpretation"
        except SocialInterpretationProviderError as exc:
            record.update({"outcome": "semantic_validation_reject" if exc.code == "semantic_validation_reject" else "parse_error", "error_code": exc.code})
        except Exception as exc:
            record.update({"outcome": "provider_error", "error_code": getattr(exc, "code", type(exc).__name__)})
        finally:
            fixture.conn.close()
        record.update({"raw_provider_output": raw, "elapsed_ms": round((time.perf_counter() - started) * 1000)})
        results.append(record)
    payload = {"bench_schema_version": 1, "model_id": model_id, "condition": condition, "calls_attempted": len(results), "results": results, "hard_blockers": []}
    target = Path(output_dir); target.mkdir(parents=True, exist_ok=True)
    (target / f"principal_{_safe_model_id(model_id)}_{condition.lower()}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("--model-id", choices=MODELS, required=True); p.add_argument("--condition", choices=CONDITIONS, required=True); p.add_argument("--output-dir", default="data/bench/final_language_qualification")
    args = p.parse_args(); result = run_model_condition(args.model_id, args.condition, args.output_dir)
    print(json.dumps({"model_id": result["model_id"], "condition": result["condition"], "calls_attempted": result["calls_attempted"]}, ensure_ascii=False)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
