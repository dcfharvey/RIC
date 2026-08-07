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
            mix[character][activity] += 1
    activity_mix = {
        character: dict(sorted(counts.items())) for character, counts in sorted(mix.items())
    }

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
    for character, counts in activity_mix.items():
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
        activity_mix, tuple(warnings),
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
