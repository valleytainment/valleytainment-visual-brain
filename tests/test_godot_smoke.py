"""Godot project smoke checks without requiring the Godot binary."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "apps" / "visual-engine"


def test_godot_project_files_exist():
    required = [
        "project.godot",
        "scenes/main.tscn",
        "scripts/show_player.gd",
        "scripts/logo_hero.gd",
        "scripts/audio_bus.gd",
        "shaders/logo_reactive.gdshader",
        "shaders/cosmic_portal.gdshader",
        "shaders/post_fx.gdshader",
        "assets/brand/valleytainment_logo.png",
        "assets/fixtures/demo_runtime.json",
    ]
    missing = [p for p in required if not (ROOT / p).exists()]
    assert not missing, f"missing: {missing}"


def test_main_scene_wires_logo_hero():
    text = (ROOT / "scenes" / "main.tscn").read_text(encoding="utf-8")
    assert "logo_hero.gd" in text
    assert "valleytainment_logo.png" in text
    assert "logo_reactive.gdshader" in text
    assert "cosmic_portal.gdshader" in text


def test_logo_shader_has_audio_uniforms():
    text = (ROOT / "shaders" / "logo_reactive.gdshader").read_text(encoding="utf-8")
    for name in ("kick", "bass", "snare", "hat", "drop", "blackout", "shockwave"):
        assert f"uniform float {name}" in text
