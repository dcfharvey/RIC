"""Planner naturel V0.1, deterministe et sans acces aux faits."""
from __future__ import annotations

import re
import sqlite3
from datetime import timedelta
from typing import Any

from .observation import ObservationError, ObservationQuery
from .util import parse_iso, to_iso
from .world import WorldEngine


class ObserverPlannerError(ObservationError):
    pass


def _names(conn: sqlite3.Connection, world_id: int) -> dict[str, str]:
    rows = conn.execute("SELECT key,name FROM character WHERE world_id=?", (world_id,)).fetchall()
    result: dict[str, str] = {}
    for row in rows:
        result[row["key"].lower()] = row["key"]
        result[row["name"].lower()] = row["key"]
    return result


def _locations(conn: sqlite3.Connection, world_id: int) -> dict[str, str]:
    rows = conn.execute("SELECT key,name FROM location WHERE world_id=?", (world_id,)).fetchall()
    result: dict[str, str] = {}
    for row in rows:
        result[row["key"].lower()] = row["key"]
        result[row["name"].lower()] = row["key"]
    return result


def _subject(text: str, names: dict[str, str]) -> str:
    found = {value for label, value in names.items() if re.search(rf"\b{re.escape(label)}\b", text, re.I)}
    if len(found) != 1:
        code = "subject_unknown" if not found else "subject_ambiguous"
        raise ObserverPlannerError("sujet introuvable ou ambigu", code=code)
    return next(iter(found))


def plan_question(conn: sqlite3.Connection, world_id: int, question: Any) -> ObservationQuery:
    """Traduit quelques formulations de rodage en query, sans produire de faits."""
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 500:
        raise ObserverPlannerError("question invalide", code="invalid_question")
    text = question.strip().lower()
    names = _names(conn, world_id)
    locations = _locations(conn, world_id)

    if any(word in text for word in ("qui est dans", "qui se trouve dans")):
        found = {value for label, value in locations.items() if re.search(rf"\b{re.escape(label)}\b", text)}
        if len(found) != 1:
            raise ObserverPlannerError("lieu introuvable ou ambigu", code="location_unknown")
        return ObservationQuery(mode="hugin", focus="current_state", location_key=next(iter(found)))
    if any(word in text for word in ("où est", "ou est", "que fait", "fait actuellement")):
        return ObservationQuery(mode="hugin", focus="current_state", subject_keys=(_subject(text, names),))
    if "compris la même chose" in text or "compris la meme chose" in text:
        subjects = {value for label, value in names.items() if re.search(rf"\b{re.escape(label)}\b", text)}
        if len(subjects) != 2:
            raise ObserverPlannerError("comparaison exige deux sujets distincts", code="subject_ambiguous")
        return ObservationQuery(mode="munin", focus="comparison", subject_keys=tuple(sorted(subjects)))
    if "comment" in text and any(word in text for word in ("vécu", "vecu", "interaction", "conversation")):
        return ObservationQuery(mode="munin", focus="causal_chain", subject_keys=(_subject(text, names),))
    if "pourquoi" in text and any(word in text for word in ("réaction", "reaction", "réagi", "reagi")):
        return ObservationQuery(mode="munin", focus="causal_chain", subject_keys=(_subject(text, names),))
    if any(word in text for word in ("passé", "passe", "s'est passé", "s’est passé", "récemment", "recemment", "dernière heure", "derniere heure")):
        now = parse_iso(WorldEngine(conn).read_canonical_time(world_id))
        minutes = 60 if "heure" in text else 15
        return ObservationQuery(mode="hugin", focus="conversation", start_at=to_iso(now - timedelta(minutes=minutes)), end_at=to_iso(now), max_events=50)
    raise ObserverPlannerError("formulation non planifiable; utilisez les controles structures", code="planner_unavailable")


def query_from_payload(conn: sqlite3.Connection, world_id: int, payload: dict[str, Any]) -> ObservationQuery:
    allowed = {"question", "mode", "subject_keys", "focus", "relative_time_scope", "start_at", "end_at", "location_key", "max_events", "max_items_per_owner"}
    unknown = set(payload) - allowed
    if unknown:
        raise ObserverPlannerError("champ de plan inconnu", code="unknown_planner_field")
    if "question" in payload:
        if len(payload) != 1:
            raise ObserverPlannerError("question naturelle exclusive des controles structures", code="mixed_planner_input")
        return plan_question(conn, world_id, payload["question"])
    values = dict(payload)
    values.setdefault("mode", "hugin")
    values.setdefault("focus", "events")
    if "subject_keys" in values:
        if not isinstance(values["subject_keys"], list):
            raise ObserverPlannerError("subject_keys doit etre une liste", code="invalid_planner_plan")
        values["subject_keys"] = tuple(values["subject_keys"])
    relative = values.pop("relative_time_scope", None)
    if relative is not None:
        if relative not in {"now", "15m", "1h", "custom"}:
            raise ObserverPlannerError("fenetre relative invalide", code="invalid_planner_plan")
        if relative == "custom":
            if not values.get("start_at") or not values.get("end_at"):
                raise ObserverPlannerError("fenetre personnalisee incomplete", code="invalid_planner_plan")
        elif values.get("start_at") is not None or values.get("end_at") is not None:
            raise ObserverPlannerError("fenetres combinees interdites", code="invalid_planner_plan")
        elif relative in {"15m", "1h"}:
            now = parse_iso(WorldEngine(conn).read_canonical_time(world_id))
            delta = timedelta(minutes=15 if relative == "15m" else 60)
            values["start_at"], values["end_at"] = to_iso(now - delta), to_iso(now)
    return ObservationQuery(**values)
