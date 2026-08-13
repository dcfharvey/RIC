import inspect

from vivarium.action_arbitration_runtime import CausalArbitrationBuilder


def test_owner_backed_arbitration_contract_uses_owner_projection():
    signature = inspect.signature(CausalArbitrationBuilder.build_owner_backed)
    assert "wake_source" not in signature.parameters
    source = inspect.getsource(CausalArbitrationBuilder.build_owner_backed)
    assert "project_owner_backed" in source
    assert "project_synthetic" not in source
