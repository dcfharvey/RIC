"""One-shot WO88 repair: keep production paths off public *_synthetic physiology APIs."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


replace_once(
    "src/vivarium/sleep_physiology.py",
    '''    def project_synthetic(\n        self, world_id: Any, character_key: Any, source: RegulationInput\n    ) -> PhysiologyProjection:\n        """Projette propension additive et stabilité sans modifier l'ancre."""\n        state = self.read_state(world_id, character_key)\n        parameters = self.parameters_for_character(world_id, character_key)\n        return PhysiologyProjection(\n            state=state,\n            propensity=sleep_propensity(state.regulation, parameters, family="additive"),\n            stability=wake_stability(\n                state.regulation,\n                source,\n                parameters,\n                previous_band=state.previous_stability_band,\n            ),\n        )\n\n''',
    '''    def _project(\n        self, world_id: Any, character_key: Any, source: RegulationInput\n    ) -> PhysiologyProjection:\n        """Noyau pur commun; l'API appelante reste responsable de la provenance."""\n        state = self.read_state(world_id, character_key)\n        parameters = self.parameters_for_character(world_id, character_key)\n        return PhysiologyProjection(\n            state=state,\n            propensity=sleep_propensity(state.regulation, parameters, family="additive"),\n            stability=wake_stability(\n                state.regulation,\n                source,\n                parameters,\n                previous_band=state.previous_stability_band,\n            ),\n        )\n\n    def project_synthetic(\n        self, world_id: Any, character_key: Any, source: RegulationInput\n    ) -> PhysiologyProjection:\n        """API de banc: projection depuis une cause explicitement injectée."""\n        return self._project(world_id, character_key, source)\n\n    def project_owner_backed(\n        self, world_id: Any, character_key: Any, *, at_time: Any | None = None,\n        expected_event_seq: Any | None = None,\n    ) -> PhysiologyProjection:\n        """Projette depuis les causes Reality persistées, sans écriture."""\n        source = self.resolve_light_source_owner_backed(\n            world_id, character_key, at_time=at_time, expected_event_seq=expected_event_seq\n        )\n        state = self.read_state(world_id, character_key)\n        if state.anchor_at != source.canonical_at:\n            raise SleepPhysiologyError(\n                "etat physiologique hors ancre courante", code="stale_physiology_anchor"\n            )\n        return self._project(world_id, character_key, source.source)\n\n''',
)

replace_once(
    "src/vivarium/sleep_physiology.py",
    '''        projection = self.project_synthetic(world_id, character_key, source.source)\n''',
    '''        projection = self._project(world_id, character_key, source.source)\n''',
)

old_critical = '''    def next_critical_boundary_synthetic(\n        self,\n        world_id: Any,\n        character_key: Any,\n        source: RegulationInput,\n        until: Any,\n    ) -> str | None:\n        """Cherche, sans écrire, une entrée ``critical`` sous causes constantes.\n\n        Le quantum est identique à celui de matérialisation : le résultat ne\n        dépend donc pas du partitionnement de l'appelant. Il reste un choix\n        numérique de banc, non une cadence runtime ni une règle physiologique.\n        """\n        state = self.read_state(world_id, character_key)\n        target = _at(until)\n        remaining = self._seconds_between(state.anchor_at, target)\n        parameters = self.parameters_for_character(world_id, character_key)\n        regulation = state.regulation\n        band = state.previous_stability_band\n        cursor = parse_iso(state.anchor_at)\n        if band == "critical":\n            return state.anchor_at\n        while remaining:\n            duration = min(SYNTHETIC_INTEGRATION_QUANTUM_SECONDS, remaining)\n            advanced = advance_regulation(regulation, source, duration, parameters)\n            regulation = RegulationState(\n                advanced.homeostatic_load,\n                advanced.circadian_phase,\n                regulation.physical_capacity,\n            )\n            stability = wake_stability(regulation, source, parameters, previous_band=band)\n            cursor += timedelta(seconds=duration)\n            if band != "critical" and stability.band == "critical":\n                return to_iso(cursor)\n            band = stability.band\n            remaining -= duration\n        return None\n'''
new_critical = '''    def _next_critical_boundary(\n        self, world_id: Any, character_key: Any, source: RegulationInput, until: Any\n    ) -> str | None:\n        """Noyau pur de recherche d'entrée ``critical`` sous causes constantes."""\n        state = self.read_state(world_id, character_key)\n        target = _at(until)\n        remaining = self._seconds_between(state.anchor_at, target)\n        parameters = self.parameters_for_character(world_id, character_key)\n        regulation = state.regulation\n        band = state.previous_stability_band\n        cursor = parse_iso(state.anchor_at)\n        if band == "critical":\n            return state.anchor_at\n        while remaining:\n            duration = min(SYNTHETIC_INTEGRATION_QUANTUM_SECONDS, remaining)\n            advanced = advance_regulation(regulation, source, duration, parameters)\n            regulation = RegulationState(\n                advanced.homeostatic_load,\n                advanced.circadian_phase,\n                regulation.physical_capacity,\n            )\n            stability = wake_stability(regulation, source, parameters, previous_band=band)\n            cursor += timedelta(seconds=duration)\n            if band != "critical" and stability.band == "critical":\n                return to_iso(cursor)\n            band = stability.band\n            remaining -= duration\n        return None\n\n    def next_critical_boundary_synthetic(\n        self, world_id: Any, character_key: Any, source: RegulationInput, until: Any\n    ) -> str | None:\n        """API de banc pour une source injectée explicitement."""\n        return self._next_critical_boundary(world_id, character_key, source, until)\n\n    def next_critical_boundary_owner_backed(\n        self, world_id: Any, character_key: Any, *, until: Any\n    ) -> str | None:\n        """Cherche la frontière critique depuis les causes Reality courantes."""\n        state = self.read_state(world_id, character_key)\n        source = self.resolve_light_source_owner_backed(\n            world_id, character_key, at_time=state.anchor_at\n        )\n        return self._next_critical_boundary(world_id, character_key, source.source, until)\n'''
replace_once("src/vivarium/sleep_physiology.py", old_critical, new_critical)

replace_once(
    "src/vivarium/decision.py",
    '''   source=physiology.resolve_light_source_owner_backed(world_id,character_key,at_time=state.anchor_at)\n   projection=physiology.project_synthetic(world_id,character_key,source.source)\n''',
    '''   projection=physiology.project_owner_backed(world_id,character_key,at_time=state.anchor_at)\n''',
)

replace_once(
    "src/vivarium/active_simulation.py",
    '''            source=self._physiology.resolve_light_source_owner_backed(world_id,character_key,at_time=state.anchor_at)\n            critical=self._physiology.next_critical_boundary_synthetic(world_id,character_key,source.source,to_iso(horizon))\n''',
    '''            critical=self._physiology.next_critical_boundary_owner_backed(\n                world_id,character_key,until=to_iso(horizon)\n            )\n''',
)

with (ROOT / "tests/test_active_runtime_cutover.py").open("a", encoding="utf-8", newline="\n") as handle:
    handle.write('''\n\ndef test_active_runtime_paths_do_not_call_public_synthetic_physiology_apis(monkeypatch):\n conn,wid,clock=active_world()\n try:\n  def forbidden(*args,**kwargs):\n   raise AssertionError("public synthetic physiology API reached")\n  monkeypatch.setattr(SleepPhysiologyService,"project_synthetic",forbidden)\n  monkeypatch.setattr(SleepPhysiologyService,"next_critical_boundary_synthetic",forbidden)\n  DecisionFrameService(conn).build_current(wid,"sophie")\n  ActivityEngine(conn,clock=clock).start_activity(wid,"sophie","gaming","salon",sim_now=T0)\n  ActiveSimulationEngine(conn,clock=clock).next_boundary(\n   wid,"sophie",until=to_iso(T0_DT+timedelta(seconds=20))\n  )\n finally:conn.close()\n''')
