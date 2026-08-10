"""SCC-1B2E: bench-only audit of possible Gemma home-field effects."""
from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .cognition import LocalLLMSettings
from .social_interpretation import SocialInterpretationService
from .social_interpretation_bench import BenchScenario, _build_fixture, _safe_model_id
from .social_interpretation_provider import (
    LMStudioSocialInterpretationProvider,
    SocialInterpretationContextBuilder,
    SocialInterpretationProviderError,
    parse_provider_proposal,
)

HOME_FIELD_MODELS = (
    "google/gemma-4-12b-qat", "qwen3-8b", "qwen3-14b",
    "ministral-3-8b-instruct-2512", "ministral-3-14b-instruct-2512-k-m",
)
HOME_FIELD_CONDITIONS = ("C1_NATIVE_STRICT", "C2_OUTER_FENCE_NORMALIZED")
HOME_FIELD_MAX_CALLS = 180
_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```$", re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class HomeFieldScenario:
    scenario_id: str
    content: str
    property: str
    context_contents: tuple[str, ...] = ()
    recipient_key: str | None = "erika"


HOME_FIELD_SCENARIOS = (
    HomeFieldScenario("H01", "Oui, ça me va.", "preserve ambiguous antecedent"),
    HomeFieldScenario("H02", "Elle s'appelle Julie.", "correction without imposed motive"),
    HomeFieldScenario("H03", "Je suis désolée que ça soit arrivé.", "no unsupported responsibility"),
    HomeFieldScenario("H04", "Ta présentation était vraiment bonne.", "no forced sarcasm or manipulation"),
    HomeFieldScenario("H05", "Je dois me lever à cinq heures demain.", "indirect refusal remains qualified"),
    HomeFieldScenario("H06", "Si j'ai fini avant huit heures, je viendrai.", "preserve conditional promise"),
    HomeFieldScenario("H07", 'Erika m\'a dit : "Luna a cassé la tasse."', "preserve reported-source hierarchy"),
    HomeFieldScenario("H08", "Erika pense que la porte est verrouillée, mais je n'en sais rien.", "separate another person's belief"),
    HomeFieldScenario("H09", "Elle m'a dit qu'elle viendrait plus tard.", "preserve unresolved reference"),
    HomeFieldScenario("H10", "T'es un ange.", "avoid literal or romantic overclaim"),
    HomeFieldScenario("H11", "Je préfère rester ici.", "fatigue is not automatically causal", ("Je suis fatiguée.",)),
    HomeFieldScenario("H12", "Je ne suis pas fâchée.", "preserve contradiction without hidden-state verdict", ("Ça m'irrite encore.",)),
    HomeFieldScenario("H13", "Je vais vendre ton ordinateur. Je blague.", "use explicit joke marker only"),
    HomeFieldScenario("H14", "Quelqu'un peut fermer la fenêtre?", "do not invent individual addressee", recipient_key=None),
    HomeFieldScenario("H15", "C'est... original.", "held-out initial remains open", ("Tu aimes le cadeau?",)),
    HomeFieldScenario("H16", "Ce n'est pas vraiment mon style, mais merci d'y avoir pensé.", "held-out revision integrates clarification", ("C'est... original.",)),
)


def normalize_outer_json_fence(raw: str) -> tuple[str, bool, str | None]:
    """Remove only one complete outer Markdown JSON fence, if present."""
    trimmed = raw.strip()
    match = _FENCE_RE.fullmatch(trimmed)
    if match is None:
        return raw, False, None
    inner = match.group(1)
    if "```" in inner:
        return raw, False, None
    return inner, True, "single_outer_code_fence"


def _validate_without_persistence(value: Mapping[str, Any]) -> dict[str, Any]:
    parsed = parse_provider_proposal(value)
    meaning = SocialInterpretationService._hypotheses(parsed["meaning_hypotheses"], "meaning")
    motive = SocialInterpretationService._hypotheses(parsed["motive_hypotheses"], "motive")
    status = parsed["understanding_status"]
    if status == "unresolved" and (meaning or motive):
        raise SocialInterpretationProviderError("unresolved has hypotheses", code="semantic_validation_reject")
    if status == "clear" and not meaning:
        raise SocialInterpretationProviderError("clear has no meaning hypothesis", code="semantic_validation_reject")
    if status == "ambiguous" and len(meaning) < 2:
        raise SocialInterpretationProviderError("ambiguous has fewer than two meanings", code="semantic_validation_reject")
    return {"understanding_status": status, "meaning_hypotheses": list(meaning), "motive_hypotheses": list(motive)}


def _snapshot_for(item: HomeFieldScenario) -> tuple[Any, Any]:
    scenario = BenchScenario(item.scenario_id, "home_field", item.content,
                             recipient_key=item.recipient_key, context_contents=item.context_contents,
                             select_context=bool(item.context_contents))
    fixture = _build_fixture(scenario)
    snapshot = SocialInterpretationContextBuilder(fixture.conn).build(
        fixture.world_id, "erika", "primary", selected_trace_request_keys=fixture.selected_keys)
    return fixture, snapshot


def _one_call(provider: LMStudioSocialInterpretationProvider, item: HomeFieldScenario,
              condition: str, repeat: int) -> dict[str, Any]:
    fixture, snapshot = _snapshot_for(item)
    started = time.perf_counter()
    raw = normalized = None
    applied = False
    kind = None
    outcome = "valid"
    error_code = None
    parsed: dict[str, Any] = {}
    try:
        raw_value = provider.propose(snapshot)
        raw = raw_value if isinstance(raw_value, str) else json.dumps(raw_value, ensure_ascii=False)
        normalized, applied, kind = normalize_outer_json_fence(raw) if condition == HOME_FIELD_CONDITIONS[1] else (raw, False, None)
        parsed = _validate_without_persistence(json.loads(normalized))
    except SocialInterpretationProviderError as exc:
        outcome = "parse_error" if exc.code == "invalid_provider_output" else "semantic_validation_reject"
        error_code = exc.code
    except Exception as exc:
        outcome = "provider_error"
        error_code = getattr(exc, "code", type(exc).__name__)
    finally:
        fixture.conn.close()
    return {"scenario_id": item.scenario_id, "condition": condition, "repeat": repeat,
            "snapshot_fingerprint": snapshot.fingerprint, "snapshot": snapshot.data,
            "raw_provider_output": raw, "normalized_provider_output": normalized,
            "normalization_applied": applied, "normalization_kind": kind,
            "outcome": outcome, "error_code": error_code, **parsed,
            "elapsed_ms": round((time.perf_counter() - started) * 1000)}


def _planned_items() -> tuple[tuple[HomeFieldScenario, int], ...]:
    items = [(item, 1) for item in HOME_FIELD_SCENARIOS[:14]]
    items.extend(((HOME_FIELD_SCENARIOS[14], 1), (HOME_FIELD_SCENARIOS[15], 1),
                  (HOME_FIELD_SCENARIOS[14], 2), (HOME_FIELD_SCENARIOS[15], 2)))
    return tuple(items)


def run_model_condition(model_id: str, condition: str, output_dir: str | Path) -> dict[str, Any]:
    if condition not in HOME_FIELD_CONDITIONS:
        raise ValueError(f"unknown condition: {condition}")
    settings = LocalLLMSettings.from_environment(require_model=False)
    settings = LocalLLMSettings(settings.base_url, model_id, settings.api_token, settings.timeout_seconds)
    provider = LMStudioSocialInterpretationProvider(settings)
    results = [_one_call(provider, item, condition, repeat) for item, repeat in _planned_items()]
    pairs = []
    for repeat in (1, 2):
        initial = next(r for r in results if r["scenario_id"] == "H15" and r["repeat"] == repeat)
        revision = next(r for r in results if r["scenario_id"] == "H16" and r["repeat"] == repeat)
        pairs.append({"pair_id": f"H15_H16_{repeat}", "lineage_valid": bool(initial["snapshot_fingerprint"] and revision["snapshot_fingerprint"]),
                      "initial_snapshot_fingerprint": initial["snapshot_fingerprint"], "revision_snapshot_fingerprint": revision["snapshot_fingerprint"]})
    payload = {"audit_schema_version": 1, "model_id": model_id, "condition": condition,
               "provider_version": provider.provider_version, "calls_attempted": len(results),
               "results": results, "h15_h16_pairs": pairs, "hard_blockers": []}
    target = Path(output_dir); target.mkdir(parents=True, exist_ok=True)
    path = target / f"principal_{_safe_model_id(model_id)}_{condition.lower()}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--condition", choices=HOME_FIELD_CONDITIONS, required=True)
    parser.add_argument("--output-dir", default="data/bench/home_field")
    args = parser.parse_args()
    payload = run_model_condition(args.model_id, args.condition, args.output_dir)
    print(json.dumps({k: payload[k] for k in ("model_id", "condition", "calls_attempted", "hard_blockers")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
