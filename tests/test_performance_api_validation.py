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
            "creature_profile": "aggressive",
            "intensity_bias": 0.25,
            "blackout": False,
        }
    )
    assert patch["mode"] == "HYBRID"
    assert patch["resolution"] == "3840x2160"
    assert patch["seed"] == 42
    assert patch["creature_profile"] == "AGGRESSIVE"


def test_creature_profile_mirrors_into_low_latency_live_payload():
    state = PerformanceState()
    controls = state.patch_controls({"creature_profile": "wet"})
    snapshot = state.get_snapshot()
    assert controls["creature_profile"] == "WET"
    assert snapshot["live"]["creature_profile"] == "WET"


def test_unknown_or_unsafe_controls_are_rejected():
    with pytest.raises(ValueError, match="unsupported control fields"):
        validate_control_patch({"shell_command": "nope"})
    with pytest.raises(ValueError, match="resolution"):
        validate_control_patch({"resolution": "99999x1"})
    with pytest.raises(ValueError, match="style"):
        validate_control_patch({"style": "../../escape"})
    with pytest.raises(ValueError, match="creature_profile"):
        validate_control_patch({"creature_profile": "meltdown../../"})


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
