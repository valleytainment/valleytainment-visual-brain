"""Regression tests for level-aware live visual analysis."""

import numpy as np

from vbrain.live import LiveBrain, live_bands


def test_digital_silence_stays_silent():
    bands = live_bands(np.zeros(4096, dtype=np.float64))
    assert bands["loudness"] == 0.0
    assert max(bands.values()) == 0.0


def test_noise_floor_does_not_normalize_to_full_energy():
    rng = np.random.default_rng(926183)
    bands = live_bands(rng.normal(0.0, 1e-8, 4096))
    assert bands["loudness"] == 0.0
    assert bands["kick"] == 0.0
    assert bands["hat"] == 0.0


def test_level_changes_survive_spectral_normalization():
    sr = 44100
    t = np.arange(4096) / sr
    loud = 0.45 * np.sin(2 * np.pi * 60 * t)
    quiet = 0.0045 * np.sin(2 * np.pi * 60 * t)

    loud_bands = live_bands(loud, sr=sr)
    quiet_bands = live_bands(quiet, sr=sr)

    assert loud_bands["kick"] > quiet_bands["kick"]
    assert loud_bands["loudness"] > quiet_bands["loudness"]
    assert loud_bands["kick"] > loud_bands["hat"]


def test_live_brain_marks_silence_without_false_drop():
    brain = LiveBrain()
    state = brain.process(np.zeros(4096, dtype=np.float64))
    assert state.section == "SILENCE"
    assert state.intensity == 0.0
    assert state.drop_probability == 0.0
    assert state.action == "trigger_silence"
