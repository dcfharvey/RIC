from datetime import datetime, timezone
from pathlib import Path

import pytest

from vivarium.cognition import CognitionError
from vivarium.rodage_v2_official import OfficialBootstrapError, _check_provider, bootstrap_official
from vivarium.util import Clock


class FakeClock(Clock):
    def __init__(self, value: datetime):
        self.value = value

    def now(self):
        return self.value


def _configure(monkeypatch, model="qwen3-14b"):
    monkeypatch.setenv("VIVARIUM_LLM_BASE_URL", "http://127.0.0.1:1234")
    monkeypatch.setenv("VIVARIUM_LLM_MODEL", model)


def _record(*, key="qwen3-14b", quantization="Q4_K_M", loaded=True):
    return {
        "key": key,
        "quantization": {"name": quantization, "bits_per_weight": 4},
        "loaded_instances": [{"id": "qwen-instance-1", "config": {}}] if loaded else [],
    }


def test_provider_accepts_exact_loaded_qwen3_14b_q4_k_m(monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setattr(
        "vivarium.rodage_v2_official.LMStudioProvider.list_model_records",
        lambda self: (_record(),),
    )
    assert _check_provider() == "qwen3-14b"


@pytest.mark.parametrize("quantization", ["Q8_0", "Q4_0", None])
def test_provider_rejects_wrong_or_unverifiable_quantization(monkeypatch, quantization):
    _configure(monkeypatch)
    record = _record(quantization=quantization or "Q4_K_M")
    if quantization is None:
        record["quantization"] = None
    monkeypatch.setattr(
        "vivarium.rodage_v2_official.LMStudioProvider.list_model_records",
        lambda self: (record,),
    )
    with pytest.raises(OfficialBootstrapError) as exc:
        _check_provider()
    assert exc.value.code in {"unexpected_quantization", "provider_quantization_unknown"}


def test_provider_rejects_other_model(monkeypatch):
    _configure(monkeypatch, model="qwen3-8b")
    monkeypatch.setattr(
        "vivarium.rodage_v2_official.LMStudioProvider.list_model_records",
        lambda self: (_record(key="qwen3-8b"),),
    )
    with pytest.raises(OfficialBootstrapError) as exc:
        _check_provider()
    assert exc.value.code == "unexpected_llm_model"


def test_provider_rejects_configured_model_that_is_not_loaded(monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setattr(
        "vivarium.rodage_v2_official.LMStudioProvider.list_model_records",
        lambda self: (_record(loaded=False),),
    )
    with pytest.raises(OfficialBootstrapError) as exc:
        _check_provider()
    assert exc.value.code == "provider_model_not_loaded"


def test_provider_inaccessible_is_a_refusal(monkeypatch):
    _configure(monkeypatch)

    def unavailable(self):
        raise CognitionError("LM Studio est inaccessible", code="llm_unavailable")

    monkeypatch.setattr("vivarium.rodage_v2_official.LMStudioProvider.list_model_records", unavailable)
    with pytest.raises(OfficialBootstrapError) as exc:
        _check_provider()
    assert exc.value.code == "llm_unavailable"


def test_provider_failure_happens_before_official_database_creation(tmp_path: Path):
    target = tmp_path / "rodage-v2.sqlite"

    def unavailable():
        raise OfficialBootstrapError("provider indisponible", code="llm_unavailable")

    with pytest.raises(OfficialBootstrapError) as exc:
        bootstrap_official(
            target,
            clock=FakeClock(datetime(2026, 8, 13, 15, tzinfo=timezone.utc)),
            launch_runtime=False,
            provider_checker=unavailable,
        )
    assert exc.value.code == "llm_unavailable"
    assert not target.exists()
    assert not Path(str(target) + "-wal").exists()
    assert not Path(str(target) + "-shm").exists()
