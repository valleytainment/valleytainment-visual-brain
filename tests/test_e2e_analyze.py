"""End-to-end analyze → show pack on synthetic audio."""

from pathlib import Path

from vbrain.analyzer import analyze_track
from vbrain.director import plan_show
from vbrain.showpack import write_show_pack


def test_analyze_demo_track(tmp_path: Path):
    demo = Path(__file__).resolve().parents[1] / "assets" / "demo" / "demo_drop.wav"
    if not demo.exists():
        # Generate on the fly if fixture missing
        import runpy

        runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "make_demo_track.py"))

    analysis = analyze_track(demo)
    assert analysis.bpm > 100
    assert analysis.duration_s > 5
    assert len(analysis.sections) >= 2
    assert len(analysis.frames) > 10

    pack = plan_show(analysis, seed=42, show_id="test-demo")
    assert pack.visual_story.scenes
    assert pack.cue_map.cues

    out = write_show_pack(pack, tmp_path)
    assert (out / "runtime.json").exists()
    assert (out / "analysis.json").exists()
