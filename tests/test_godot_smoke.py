"""Godot project smoke checks without requiring the Godot binary."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "apps" / "visual-engine"


def test_godot_project_files_exist():
    required = [
        "project.godot",
        "scenes/main.tscn",
        "scripts/show_player.gd",
        "scripts/logo_hero.gd",
        "scripts/living_face.gd",
        "scripts/audio_bus.gd",
        "shaders/logo_reactive.gdshader",
        "shaders/cosmic_portal.gdshader",
        "shaders/post_fx.gdshader",
        "shaders/shock_ring.gdshader",
        "assets/fx/soft_orb.svg",
        "assets/brand/valleytainment_logo.png",
        "assets/fixtures/demo_runtime.json",
    ]
    missing = [path for path in required if not (ROOT / path).exists()]
    assert not missing, f"missing: {missing}"


def test_main_scene_wires_living_logo_hero():
    text = (ROOT / "scenes" / "main.tscn").read_text(encoding="utf-8")
    for marker in (
        "logo_hero.gd",
        "living_face.gd",
        "valleytainment_logo.png",
        "logo_reactive.gdshader",
        "cosmic_portal.gdshader",
        "shock_ring.gdshader",
        "LifeAura",
        "BreathMist",
        "DroolMist",
    ):
        assert marker in text


def test_logo_shader_has_audio_and_life_uniforms():
    text = (ROOT / "shaders" / "logo_reactive.gdshader").read_text(encoding="utf-8")
    names = (
        "kick",
        "bass",
        "snare",
        "hat",
        "drop",
        "blackout",
        "shockwave",
        "life",
        "breath_phase",
        "heartbeat",
        "mouth_pulse",
        "wetness",
        "goo_motion",
    )
    for name in names:
        assert f"uniform float {name}" in text
