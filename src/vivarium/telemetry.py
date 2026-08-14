"""Télémétrie locale de rodage, séparée du canon et de la cognition.

Les mesures sont descriptives. Les seuils de signalement sont des heuristiques
opérationnelles : ils ne prouvent ni un état psychologique ni une cause.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sqlite3
from typing import Any


_SPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class TelemetryWarning:
    key: str
    detail: str


@dataclass(frozen=True)
class RodageSnapshot:
    world_id: int
    event_seq: int
    cognition_admissions: int
    scenes_total: int
    scenes_empty: int
    scenes_interrupted: int
    speech_acts: int
    distinct_utterances: int
    activity_starts: int
    activity_mix: dict[str, dict[str, int]]
    activity_origin_mix: dict[str, dict[str, int]]
    technical_idle_starts: int
    warnings: tuple[TelemetryWarning, ...]

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["warnings"] = [asdict(item) for item in self.warnings]
        return result


def _normalise_utterance(value: str) -> str:
    return _SPACE.sub(" ", value.strip().casefold())


def inspect_rodage(conn: sqlite3.Connection, world_id: int) -> RodageSnapshot:
    """Calcule un portrait borné sans écrire dans le monde observé."""
    if not isinstance(world_id, int) or isinstance(world_id, bool) or world_id < 1:
        raise ValueError("monde invalide")

    event_seq = int(conn.execute(
        "SELECT COALESCE(MAX(seq), 0) FROM canonical_event WHERE world_id = ?",
        (world_id,),
    ).fetchone()[0])
    admissions = int(conn.execute(
        "SELECT COUNT(*) FROM cognition_call_admission WHERE world_id = ?",
        (world_id,),
    ).fetchone()[0])
    scene_row = conn.execute(
        "SELECT COUNT(*) AS total, "
        "SUM(CASE WHEN status = 'interrupted' THEN 1 ELSE 0 END) AS interrupted "
        "FROM social_scene WHERE world_id = ?",
        (world_id,),
    ).fetchone()
    scenes_total = int(scene_row["total"] or 0)
    scenes_interrupted = int(scene_row["interrupted"] or 0)
    scenes_empty = int(conn.execute(
        "SELECT COUNT(*) FROM social_scene s WHERE s.world_id = ? AND NOT EXISTS "
        "(SELECT 1 FROM social_speech_act a WHERE a.scene_id = s.id)",
        (world_id,),
    ).fetchone()[0])
    utterances = [
        _normalise_utterance(row["content_text"])
        for row in conn.execute(
            "SELECT a.content_text FROM social_speech_act a "
            "JOIN social_scene s ON s.id = a.scene_id WHERE s.world_id = ? "
            "ORDER BY a.id DESC LIMIT 200",
            (world_id,),
        ).fetchall()
    ]
    speech_acts = len(utterances)
    distinct_utterances = len(set(utterances))

    mix: dict[str, Counter[str]] = defaultdict(Counter)
    origin_mix: dict[str, Counter[str]] = defaultdict(Counter)
    technical_idle_by_character: Counter[str] = Counter()
    technical_idle_origins = frozenset({
        "wo95_post_boundary_idle", "cognition_retry",
    })
    rows = conn.execute(
        "SELECT payload FROM canonical_event WHERE world_id = ? "
        "AND event_type = 'activity_started' ORDER BY seq DESC LIMIT 500",
        (world_id,),
    ).fetchall()
    for row in rows:
        try:
            payload = json.loads(row["payload"])
            character, activity = payload["character"], payload["activity"]
        except (KeyError, TypeError, ValueError):
            continue
        if isinstance(character, str) and isinstance(activity, str):
            provenance = payload.get("action_provenance")
            origin = provenance.get("origin") if isinstance(provenance, dict) else None
            if not isinstance(origin, str) or not origin:
                origin = "unattributed"
            origin_mix[character][origin] += 1
            if activity == "idle" and origin in technical_idle_origins:
                technical_idle_by_character[character] += 1
            else:
                mix[character][activity] += 1
    activity_mix = {
        character: dict(sorted(counts.items()))
        for character, counts in sorted(mix.items()) if counts
    }
    activity_origin_mix = {
        character: dict(sorted(counts.items()))
        for character, counts in sorted(origin_mix.items()) if counts
    }
    non_sapient: set[str] = set()
    for row in conn.execute(
        "SELECT c.key, o.resolved_initial_definition_json FROM character c "
        "JOIN character_instance_origin o ON o.character_id=c.id "
        "WHERE c.world_id=?",
        (world_id,),
    ):
        try:
            components = json.loads(row["resolved_initial_definition_json"])["components"]
            if any(
                item.get("key") == "behavior.non_sapient_agency"
                for item in components if isinstance(item, dict)
            ):
                non_sapient.add(row["key"])
        except (KeyError, TypeError, ValueError):
            continue

    warnings: list[TelemetryWarning] = []
    if speech_acts >= 6 and distinct_utterances / speech_acts <= 0.5:
        warnings.append(TelemetryWarning(
            "dialogue_repetition",
            f"{distinct_utterances}/{speech_acts} formulations distinctes sur la fenêtre",
        ))
    if scenes_total >= 4 and scenes_empty / scenes_total >= 0.5:
        warnings.append(TelemetryWarning(
            "empty_scenes",
            f"{scenes_empty}/{scenes_total} scènes sans parole",
        ))
    for character, amount in sorted(technical_idle_by_character.items()):
        if character in non_sapient:
            continue
        if amount >= 8:
            warnings.append(TelemetryWarning(
                "technical_idle_frequency",
                f"{character}: {amount} idle technique hors monoculture comportementale",
            ))
    for character, counts in activity_mix.items():
        # CAT-0 emploie `idle` comme attente bornée entre deux décisions. Sa
        # variété comportementale se mesure dans son journal de décisions et
        # ses déplacements, pas avec la taxonomie des activités sapientes.
        if character in non_sapient:
            continue
        total = sum(counts.values())
        dominant, amount = max(counts.items(), key=lambda item: item[1])
        if total >= 8 and amount / total >= 0.8:
            warnings.append(TelemetryWarning(
                "activity_monoculture",
                f"{character}: {dominant} représente {amount}/{total} départs d'activité",
            ))

    return RodageSnapshot(
        world_id, event_seq, admissions, scenes_total, scenes_empty,
        scenes_interrupted, speech_acts, distinct_utterances, len(rows),
        activity_mix, activity_origin_mix, sum(technical_idle_by_character.values()),
        tuple(warnings),
    )


class RuntimeOutcomeLog:
    """Journal JSONL technique des résultats LLM; jamais une source canonique."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def append(self, *, checked_at: str, cycle: str, character: str | None,
               outcome: str, provider_error: str | None = None,
               validation_error: str | None = None) -> None:
        record = {
            "checked_at": checked_at,
            "cycle": cycle,
            "character": character,
            "outcome": outcome,
            "provider_error": provider_error,
            "validation_error": validation_error,
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
