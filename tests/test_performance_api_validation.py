"""Safety contracts for the local performer control API."""

from pathlib import Path

import pytest
from vbrain.performance import PerformanceState, validate_control_patch, write_live_sidecar


def test_valid_control_patch_is_normalized():
    patch = validate_control_patch(
        {
            "mode": "hybrid",
            "resolution": "3840x2160",
            "seed": 42,
            "style": "liquid_neon_void",
            "intensity_bias": 0.25,
            "blackout": False,
        }
    )
    assert patch["mode"] == "HYBRID"
    assert patch["resolution"] == "3840x2160"
    assert patch["seed"] == 42


def test_unknown_or_unsafe_controls_are_rejected():
    with pytest.raises(ValueError, match="unsupported control fields"):
        validate_control_patch({"shell_command": "nope"})
    with pytest.raises(ValueError, match="resolution"):
        validate_control_patch({"resolution": "99999x1"})
    with pytest.raises(ValueError, match="style"):
        validate_control_patch({"style": "../../escape"})


def test_performance_state_does_not_mutate_after_invalid_patch():
    state = PerformanceState()
    before = state.get_snapshot()["controls"]
    with pytest.raises(ValueError):
        state.patch_controls({"seed": -1})
    assert state.get_snapshot()["controls"] == before


def test_live_sidecar_publish_is_atomic(tmp_path: Path):
    path = tmp_path / "live.json"
    write_live_sidecar(path, {"section": "DROP", "intensity": 1.0})
    assert path.exists()
    assert not path.with_suffix(".json.tmp").exists()
    assert '"section":"DROP"' in path.read_text(encoding="utf-8")
