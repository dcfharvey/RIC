"""Technical flow control for cognitive opportunities.

This module owns neither canon nor subjective memory.  It provides a small
runtime scheduler and an append-only audit stream so that removing the normal
compute quota cannot turn a legitimate opportunity into a silent omission.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .util import Clock, new_uuid


FLOW_STATES = frozenset({
    "opportunity", "admitted", "queued", "executing", "completed",
    "duplicate", "coalesced", "stale", "cancelled", "invalidated",
    "provider_error", "timeout", "runaway_guard", "backpressure", "refused",
})


def flow_failure_state(reason_code: str | None) -> str:
    """Classify transport timeout separately without shaping cognition rate."""
    return "timeout" if reason_code in {
        "timeout", "provider_timeout", "llm_timeout", "request_timeout",
    } else "provider_error"


@dataclass(frozen=True)
class CognitiveFlowRequest:
    """A technical request, never a fact or a subjective memory."""

    world_id: int
    character_key: str
    trigger: str
    source_key: str
    requested_at: str
    source_event_seq: int | None = None
    parent_event_seq: int | None = None
    lineage_key: str | None = None
    causal_depth: int = 0
    logical_source_key: str | None = None

    @property
    def idempotency_key(self) -> str:
        logical_source = self.logical_source_key or self.source_key
        return f"{self.character_key}:{self.trigger}:{logical_source}"

    @property
    def opportunity_id(self) -> str:
        return self.idempotency_key

    @property
    def bucket(self) -> tuple[str, str]:
        return self.character_key, self.trigger

    @property
    def lineage(self) -> str | None:
        return self.lineage_key or (
            None if self.parent_event_seq is None else f"parent:{self.parent_event_seq}"
        )


@dataclass(frozen=True)
class FlowOffer:
    state: str
    reason_code: str


class CognitiveFlowScheduler:
    """Small fair scheduler for the synchronous runtime boundary.

    The runtime currently invokes providers synchronously.  The scheduler
    therefore allows one selected provider dispatch per runtime tick, keeps
    other valid requests pending, and rotates by character/trigger bucket.
    It is deliberately in-memory technical state; durable evidence belongs to
    ``cognition_flow_event``.
    """

    def __init__(
        self, *, max_dispatches_per_tick: int = 1, max_pending: int = 256,
        max_causal_depth: int = 64, max_lineage_requests: int = 128,
    ) -> None:
        if not isinstance(max_dispatches_per_tick, int) or max_dispatches_per_tick < 1:
            raise ValueError("max_dispatches_per_tick must be positive")
        if not isinstance(max_pending, int) or max_pending < 1:
            raise ValueError("max_pending must be positive")
        if not isinstance(max_causal_depth, int) or max_causal_depth < 1:
            raise ValueError("max_causal_depth must be positive")
        if not isinstance(max_lineage_requests, int) or max_lineage_requests < 1:
            raise ValueError("max_lineage_requests must be positive")
        self.max_dispatches_per_tick = max_dispatches_per_tick
        self.max_pending = max_pending
        self.max_causal_depth = max_causal_depth
        self.max_lineage_requests = max_lineage_requests
        self._pending: dict[str, CognitiveFlowRequest] = {}
        self._buckets: dict[tuple[str, str], deque[str]] = defaultdict(deque)
        self._selected_key: str | None = None
        self._dispatches = 0
        self._last_bucket: tuple[str, str] | None = None
        self._last_character: str | None = None
        self._lineage_counts: Counter[str] = Counter()

    def begin_tick(self) -> None:
        """Reset the per-tick dispatch allowance after synchronous work ended."""
        if self._selected_key is None:
            self._dispatches = 0

    def _select_if_available(self, *, preferred_key: str) -> None:
        if self._selected_key is None and self._dispatches < self.max_dispatches_per_tick:
            selected = self._choose()
            if selected == preferred_key:
                self._selected_key = selected

    def _choose(self) -> str | None:
        buckets = sorted(key for key, values in self._buckets.items() if values)
        if not buckets:
            return None
        residents = sorted({bucket[0] for bucket in buckets})
        if self._last_character is None:
            resident = residents[0]
        else:
            following = [candidate for candidate in residents if candidate > self._last_character]
            resident = following[0] if following else residents[0]
        resident_buckets = [bucket for bucket in buckets if bucket[0] == resident]
        if resident == self._last_character and self._last_bucket in resident_buckets:
            index = resident_buckets.index(self._last_bucket)
            bucket = resident_buckets[(index + 1) % len(resident_buckets)]
        else:
            bucket = resident_buckets[0]
        return self._buckets[bucket][0]

    def offer(self, request: CognitiveFlowRequest) -> FlowOffer:
        key = request.idempotency_key
        if key in self._pending:
            was_unselected = self._selected_key is None
            if was_unselected:
                self._select_if_available(preferred_key=key)
            if key == self._selected_key:
                return FlowOffer("ready", "selected")
            reason = "fairness_wait" if was_unselected else "already_queued"
            return FlowOffer("coalesced", reason)
        if request.causal_depth > self.max_causal_depth:
            return FlowOffer("runaway_guard", "causal_depth_exceeded")
        lineage = request.lineage
        if lineage is not None and self._lineage_counts[lineage] >= self.max_lineage_requests:
            return FlowOffer("runaway_guard", "causal_lineage_limit")
        if len(self._pending) >= self.max_pending:
            return FlowOffer("backpressure", "cognitive_queue_full")
        self._pending[key] = request
        self._buckets[request.bucket].append(key)
        if lineage is not None:
            self._lineage_counts[lineage] += 1
        self._select_if_available(preferred_key=key)
        if key == self._selected_key:
            return FlowOffer("ready", "selected")
        return FlowOffer("queued", "provider_dispatch_pending")

    def complete(self, idempotency_key: str) -> None:
        request = self._pending.pop(idempotency_key, None)
        if request is None:
            return
        values = self._buckets[request.bucket]
        try:
            values.remove(idempotency_key)
        except ValueError:
            pass
        if not values:
            self._buckets.pop(request.bucket, None)
        if self._selected_key == idempotency_key:
            self._selected_key = None
            self._last_bucket = request.bucket
            self._last_character = request.character_key
            self._dispatches += 1

    def cancel(self, idempotency_key: str) -> None:
        request = self._pending.pop(idempotency_key, None)
        if request is None:
            return
        values = self._buckets[request.bucket]
        try:
            values.remove(idempotency_key)
        except ValueError:
            pass
        if not values:
            self._buckets.pop(request.bucket, None)
        if self._selected_key == idempotency_key:
            self._selected_key = None

    def pending_count(self) -> int:
        return len(self._pending)

    def next_pending_request(self) -> CognitiveFlowRequest | None:
        """Expose the fair next retry candidate without mutating the queue."""
        key = self._choose()
        return None if key is None else self._pending.get(key)


class CognitiveFlowTelemetry:
    """Append-only technical evidence for every flow transition."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def record(
        self,
        request: CognitiveFlowRequest,
        state: str,
        *,
        reason_code: str | None = None,
        canonical_at: str | None = None,
        wait_started_at: str | None = None,
        provider_started_at: str | None = None,
        provider_finished_at: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        if state not in FLOW_STATES:
            raise ValueError("unknown cognitive flow state")
        character = self._conn.execute(
            "SELECT id FROM character WHERE world_id=? AND key=?",
            (request.world_id, request.character_key),
        ).fetchone()
        self._conn.execute(
            "INSERT INTO cognition_flow_event "
            "(public_id,world_id,character_id,opportunity_id,trigger,source_key,idempotency_key,state,"
            "reason_code,source_event_seq,parent_event_seq,canonical_at,recorded_at,wait_started_at,"
            "provider_started_at,provider_finished_at,details_json) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                new_uuid(), request.world_id, None if character is None else character["id"],
                request.opportunity_id, request.trigger, request.source_key, request.idempotency_key,
                state, reason_code, request.source_event_seq, request.parent_event_seq,
                canonical_at or request.requested_at, self._clock.now_iso(), wait_started_at,
                provider_started_at, provider_finished_at,
                json.dumps(details or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            ),
        )

    def record_provider_call(
        self,
        request: CognitiveFlowRequest,
        state: str,
        *,
        context: Any = None,
        provider_trace: Any = None,
        provider_call_attempted: bool = False,
        decision: Any = None,
        proposal_id: str | None = None,
        validation: Any = None,
        error_code: str | None = None,
        reason_code: str | None = None,
        canonical_at: str | None = None,
        provider_started_at: str | None = None,
        provider_finished_at: str | None = None,
    ) -> None:
        """Persist the complete terminal observation for one provider call.

        This is an extension of the existing flow journal, not a second
        ownership system.  The sections deliberately keep canonical input,
        LLM input/output, interpretation, and engine validation distinct.
        """
        context_wire = None
        if context is not None:
            wire = getattr(context, "wire", None)
            context_wire = wire() if callable(wire) else context

        trace_wire = None
        if provider_trace is not None:
            wire = getattr(provider_trace, "wire", None)
            trace_wire = wire() if callable(wire) else provider_trace
        else:
            trace_wire = {
                "available": False,
                "reason": "provider_did_not_expose_trace",
            }

        decision_wire = None
        interpretation_status = "not_reached"
        if decision is not None:
            decision_wire = {
                "schema_version": getattr(decision, "schema_version", None),
                "action": getattr(decision, "action", None),
                "connector_key": getattr(decision, "connector_key", None),
                "target_location_key": getattr(decision, "target_location_key", None),
                "activity_type": getattr(decision, "activity_type", None),
                "proposal_id": proposal_id,
            }
            interpretation_status = (
                "no_action" if decision_wire["action"] == "no_action" else "proposal"
            )
        elif error_code is not None:
            interpretation_status = "provider_or_parse_error"

        validation_wire = None
        consequence_wire: list[dict[str, Any]] = []
        if validation is not None:
            validation_wire = {
                "proposal_id": getattr(validation, "proposal_id", None),
                "status": getattr(validation, "status", None),
                "reason_code": getattr(validation, "reason_code", None),
            }
            for fact in getattr(validation, "facts", ()):
                consequence_wire.append({
                    "world_id": getattr(fact, "world_id", None),
                    "event_seq": getattr(fact, "event_seq", None),
                    "event_type": getattr(fact, "event_type", None),
                    "occurred_at": getattr(fact, "occurred_at", None),
                    "payload": _plain_observation(getattr(fact, "payload", None)),
                })

        details = {
            "observation_version": 1,
            "provider_call_attempted": provider_call_attempted,
            "canonical_input": {
                "world_id": request.world_id,
                "character_key": request.character_key,
                "trigger": request.trigger,
                "source_key": request.source_key,
                "logical_source_key": request.logical_source_key or request.source_key,
                "opportunity_id": request.opportunity_id,
                "idempotency_key": request.idempotency_key,
                "source_event_seq": request.source_event_seq,
                "parent_event_seq": request.parent_event_seq,
                "requested_at": request.requested_at,
                "causal_depth": request.causal_depth,
            },
            "llm_context": {
                "wire": _plain_observation(context_wire),
            },
            "options_presented": {
                "traversals": _plain_observation(
                    None if not isinstance(context_wire, Mapping)
                    else context_wire.get("allowed_traversals")
                ),
                "activities": _plain_observation(
                    None if not isinstance(context_wire, Mapping)
                    else context_wire.get("allowed_activities")
                ),
                "elimination_reasons": "not_available_from_current_contract",
            },
            "provider": _plain_observation(trace_wire),
            "interpretation": {
                "status": interpretation_status,
                "error_code": error_code,
                "decision": decision_wire,
            },
            "engine_validation": validation_wire,
            "canonical_consequence": consequence_wire,
        }
        self.record(
            request,
            state,
            reason_code=reason_code or error_code,
            canonical_at=canonical_at,
            provider_started_at=provider_started_at,
            provider_finished_at=provider_finished_at,
            details=details,
        )


def _plain_observation(value: Any) -> Any:
    """Convert frozen/mapping-proxy values without changing their meaning."""
    if isinstance(value, Mapping):
        return {str(key): _plain_observation(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain_observation(item) for item in value]
    return value
