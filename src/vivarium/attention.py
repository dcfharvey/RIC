"""Sélection d'attention déterministe, sans cognition subjective.

Cette couche assemble les faits localement accessibles et les seuls signaux
internes du personnage concerné. Elle ne crée ni souvenir, ni émotion,
ni décision : sa petite liste ordonnée est un budget d'entrée explicite
pour les futures couches cognitives.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from .action_contract import CONTRACT_SCHEMA_VERSION, WorldFact
from .activities import ActivityEngine, recovery_regime
from .injury import InjuryEngine
from .needs import NeedsEngine
from .perception import PerceptionService
from .registry import KEY_RE as _KEY_RE
from .resources import ResourceEngine
from .util import Clock


DEFAULT_ATTENTION_LIMIT = 5
MAX_ATTENTION_LIMIT = 20


class AttentionError(ValueError):
    """Demande d'attention invalide, toujours sans mutation du canon."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class AttentionItem:
    """Un fait candidat et sa priorité technique, jamais une émotion imposée."""

    observer_key: str
    source_kind: str
    priority_milli: int
    fact: WorldFact
    schema_version: int = CONTRACT_SCHEMA_VERSION


@dataclass(frozen=True)
class AttentionSnapshot:
    """Vue bornée d'un personnage à l'instant canonique observé."""

    observer_key: str
    observed_at: str
    available: tuple[AttentionItem, ...]
    selected: tuple[AttentionItem, ...]
    schema_version: int = CONTRACT_SCHEMA_VERSION


class AttentionService:
    """Produit une projection pure, locale et stable des priorités d'entrée."""

    _SOURCE_RANK = {
        "injury": 0,
        "resource_capability": 1,
        "need": 2,
        "resource_signal": 3,
        "perception:adjacent_connector": 4,
        "perception:co_presence": 5,
        "perception:local_object": 6,
        "perception:self_location": 7,
    }

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    @staticmethod
    def _world_id(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise AttentionError("monde invalide", code="invalid_world")
        return value

    @staticmethod
    def _key(value: Any) -> str:
        if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
            raise AttentionError("observateur invalide", code="invalid_observer")
        return value

    @staticmethod
    def _limit(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= MAX_ATTENTION_LIMIT:
            raise AttentionError("limite d'attention invalide", code="invalid_limit")
        return value

    def _effective_thresholds(self, world_id: int, character_key: str) -> dict[str, int]:
        """Seuils réellement applicables, profil compris.

        Les quatre multiplicateurs actuels appartiennent au profil MVP ; un
        futur besoin sans multiplicateur explicite conserve le facteur neutre.
        """
        profile = self._conn.execute(
            "SELECT cp.* FROM character_profile cp "
            "JOIN character ch ON ch.world_id = cp.world_id AND ch.id = cp.character_id "
            "WHERE ch.world_id = ? AND ch.key = ?",
            (world_id, character_key),
        ).fetchone()
        multiplier_column = {
            "satiete": "satiete_threshold_mult_milli",
            "repos": "repos_threshold_mult_milli",
            "energie": "energie_threshold_mult_milli",
            "hygiene": "hygiene_threshold_mult_milli",
        }
        out: dict[str, int] = {}
        for row in self._conn.execute(
            "SELECT need_key, threshold_milli FROM need_definition WHERE world_id = ? ORDER BY need_key",
            (world_id,),
        ):
            column = multiplier_column.get(row["need_key"])
            multiplier = profile[column] if profile is not None and column is not None else 1000
            out[row["need_key"]] = (row["threshold_milli"] * multiplier) // 1000
        return out

    @staticmethod
    def _perception_priority(access_kind: str, payload: Any) -> int:
        if access_kind == "co_presence":
            return 1_000
        if access_kind == "local_object":
            return 500
        if access_kind == "adjacent_connector":
            # La fermeture est un fait concret plus urgent à proposer à la
            # cognition qu'un passage déjà disponible; aucune intention n'est
            # déduite pour autant.
            state = payload["state"]
            return {"blocked": 20_000, "closed": 10_000}.get(state, 250)
        return 0

    def _internal_items(
        self, world_id: int, character_key: str, observed_at: str
    ) -> list[AttentionItem]:
        items: list[AttentionItem] = []
        thresholds = self._effective_thresholds(world_id, character_key)
        derived_needs = NeedsEngine(self._conn, clock=self._clock).derive_character(
            world_id, character_key, observed_at
        )
        for need_key, state in sorted(derived_needs.items()):
            threshold = thresholds[need_key]
            value = state["value_milli"]
            if value >= threshold:
                continue
            priority = min(100_000, ((threshold - value) * 100_000) // max(1, threshold))
            items.append(AttentionItem(
                character_key,
                "need",
                priority,
                WorldFact.state(
                    world_id,
                    "need_below_threshold",
                    observed_at,
                    {"character": character_key, "need": need_key, "value_milli": value,
                     "threshold_milli": threshold},
                ),
            ))

        activity = ActivityEngine(self._conn, clock=self._clock).activity_sheet(world_id, character_key)
        regime = recovery_regime(activity["type"]) if activity is not None else "passive"
        injury = InjuryEngine(self._conn, clock=self._clock).injury_sheet_at(
            world_id, character_key, observed_at, regime
        )
        if injury is not None and injury["severity_milli"] > 0:
            items.append(AttentionItem(
                character_key,
                "injury",
                injury["severity_milli"],
                WorldFact.state(
                    world_id,
                    "injury_active",
                    observed_at,
                    {"character": character_key, "kind": injury["kind"],
                     "severity_milli": injury["severity_milli"], "level": injury["level"],
                     "recovery_regime": regime},
                ),
            ))

        resources = ResourceEngine(self._conn, clock=self._clock)
        resource_rows = self._conn.execute(
            "SELECT rs.resource_key FROM resource_state rs "
            "JOIN character ch ON ch.world_id = rs.world_id AND ch.id = rs.character_id "
            "WHERE rs.world_id = ? AND ch.key = ? ORDER BY rs.resource_key",
            (world_id, character_key),
        )
        for row in resource_rows:
            active = resources.active_effects(world_id, character_key, row["resource_key"], observed_at)
            for effect in active["effects"]:
                if effect["effect_type"] == "capability_availability" and effect["availability"] != "available":
                    priority = 95_000 if effect["availability"] == "unavailable" else 75_000
                    items.append(AttentionItem(
                        character_key,
                        "resource_capability",
                        priority,
                        WorldFact.state(
                            world_id,
                            "resource_capability_state",
                            observed_at,
                            {"character": character_key, "resource": active["resource_key"],
                             "state": active["state_key"], "capability": effect["effect_key"],
                             "availability": effect["availability"]},
                        ),
                    ))
                elif effect["effect_type"] == "context_signal" and effect["value_milli"] != 0:
                    items.append(AttentionItem(
                        character_key,
                        "resource_signal",
                        min(100_000, abs(effect["value_milli"])),
                        WorldFact.state(
                            world_id,
                            "resource_context_signal",
                            observed_at,
                            {"character": character_key, "resource": active["resource_key"],
                             "state": active["state_key"], "signal": effect["effect_key"],
                             "value_milli": effect["value_milli"]},
                        ),
                    ))
        return items

    def snapshot(
        self, world_id: Any, observer_key: Any, *, limit: Any = DEFAULT_ATTENTION_LIMIT
    ) -> AttentionSnapshot:
        """Lit et classe les entrées potentielles sans jamais les mémoriser."""
        world_id = self._world_id(world_id)
        observer_key = self._key(observer_key)
        limit = self._limit(limit)
        perception = PerceptionService(self._conn, clock=self._clock).snapshot(world_id, observer_key)
        items = self._internal_items(world_id, observer_key, perception.observed_at)
        for candidate in perception.candidates:
            items.append(AttentionItem(
                observer_key,
                f"perception:{candidate.access_kind}",
                self._perception_priority(candidate.access_kind, candidate.fact.payload),
                candidate.fact,
            ))
        ordered = tuple(sorted(
            items,
            key=lambda item: (
                -item.priority_milli,
                self._SOURCE_RANK[item.source_kind],
                item.fact.event_type,
                tuple(sorted((str(key), str(value)) for key, value in item.fact.payload.items())),
            ),
        ))
        return AttentionSnapshot(observer_key, perception.observed_at, ordered, ordered[:limit])
