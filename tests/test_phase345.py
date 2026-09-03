"""Phase 3–5 unit tests."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from vbrain.ai import ComfyUIClient, detect_gpu, register_placeholder_hero, route_job
from vbrain.live import FileAudioSource, LiveBrain, live_bands
from vbrain.paths import ensure_demo_wav
from vbrain.performance import PerformanceState, make_handler
from vbrain.performance.presets import OUTPUT_PRESETS, get_preset, randomize_seed


def test_detect_gpu_returns_profile():
    profile = detect_gpu()
    assert profile.tier.value in {"high", "low", "none"}
    assert route_job("flux", profile)


def test_live_bands_on_sine():
    sr = 44100
    t = np.arange(2048) / sr
    kickish = 0.5 * np.sin(2 * np.pi * 60 * t)
    bands = live_bands(kickish, sr=sr)
    assert bands["kick"] >= bands["hat"]


def test_live_brain_processes_file_chunks():
    demo = ensure_demo_wav()
    src = FileAudioSource(demo, chunk_s=0.05)
    brain = LiveBrain(sr=src.sr)
    state = brain.process(src.read())
    assert state.bpm > 0
    assert 0.0 <= state.intensity <= 1.0
    assert state.section
    assert "kick_energy" in state.as_dict()


def test_asset_manifest_registers_logo(tmp_path: Path):
    logo = (
        Path(__file__).resolve().parents[1]
        / "apps"
        / "visual-engine"
        / "assets"
        / "brand"
        / "valleytainment_logo.png"
    )
    manifest_path = tmp_path / "manifest.json"
    manifest = register_placeholder_hero(manifest_path, logo)
    assert manifest_path.exists()
    assert any(a.asset_id == "valleytainment_logo" for a in manifest.assets)


def test_comfy_client_offline_report():
    report = ComfyUIClient("http://127.0.0.1:9").status_report()
    assert report["online"] is False


def test_output_presets():
    assert get_preset("uhd").width == 3840
    assert len(OUTPUT_PRESETS) >= 4
    assert randomize_seed(926183, 1) != 926183


def test_performance_state_roundtrip():
    state = PerformanceState()
    state.update_live({"section": "DROP", "intensity": 1.0})
    state.patch_controls({"seed": 42})
    snap = state.get_snapshot()
    assert snap["live"]["section"] == "DROP"
    assert snap["controls"]["seed"] == 42
    handler = make_handler(state, "<html></html>")
    assert handler is not None


def test_flux_workflow_stub_loads():
    path = Path("ai/comfyui/workflows/flux_schnell_hero_stub.json")
    data = json.loads(path.read_text())
    assert "prompt" in data
    client = ComfyUIClient()
    graph = client.load_workflow(path)
    assert "3" in graph
