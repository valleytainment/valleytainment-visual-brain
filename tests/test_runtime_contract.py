"""Runtime.json contract + schema validation tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from vbrain.runtime_contract import RuntimeExport
from vbrain.schemas import intensity_band
from vbrain.showpack import build_runtime_export, load_runtime

FIXTURE = Path(__file__).parent / "fixtures" / "demo_runtime.json"
GODOT_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "apps"
    / "visual-engine"
    / "assets"
    / "fixtures"
    / "demo_runtime.json"
)


def test_fixture_runtime_validates():
    assert FIXTURE.exists(), "run: python scripts/build_demo_fixture.py"
    runtime = load_runtime(FIXTURE)
    assert runtime.hero_scene == "valleytainment_logo"
    assert runtime.bpm > 0
    assert len(runtime.frames) >= 8
    assert len(runtime.sections) >= 2
    assert runtime.frames[0].t <= runtime.frames[-1].t


def test_godot_fixture_matches_contract():
    assert GODOT_FIXTURE.exists()
    a = json.loads(FIXTURE.read_text())
    b = json.loads(GODOT_FIXTURE.read_text())
    assert a["show_id"] == b["show_id"]
    assert a["hero_scene"] == b["hero_scene"]
    RuntimeExport.model_validate(b)


def test_runtime_rejects_bad_bpm():
    with pytest.raises(ValidationError):
        RuntimeExport.model_validate(
            {
                "show_id": "x",
                "bpm": 0,
                "duration_s": 1,
                "story": {"title": "t"},
                "frames": [],
            }
        )


def test_build_runtime_export_from_pack(tmp_path: Path):
    from vbrain.analyzer import analyze_track
    from vbrain.director import plan_show

    demo = Path(__file__).resolve().parents[1] / "assets" / "demo" / "demo_drop.wav"
    if not demo.exists():
        import runpy

        runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "make_demo_track.py"))

    pack = plan_show(analyze_track(demo, frame_stride=16), seed=1, show_id="contract")
    runtime = build_runtime_export(pack, frame_every=4)
    assert isinstance(runtime, RuntimeExport)
    assert runtime.hero_scene == "valleytainment_logo"
    dumped = json.loads(runtime.model_dump_json())
    RuntimeExport.model_validate(dumped)


def test_show_pack_roundtrip_schema():
    assert intensity_band(0.96).value in {"HEAVY", "APOCALYPSE"}
