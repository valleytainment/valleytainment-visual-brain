"""Contracts for the sentient Valleytainment monster hero."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps" / "visual-engine"


def test_living_monster_files_exist():
    required = [
        "scripts/living_face.gd",
        "shaders/shock_ring.gdshader",
        "assets/fx/soft_orb.svg",
    ]
    missing = [path for path in required if not (GODOT / path).exists()]
    assert not missing, f"missing living monster files: {missing}"


def test_logo_shader_exposes_persistent_life_controls():
    shader = (GODOT / "shaders" / "logo_reactive.gdshader").read_text(encoding="utf-8")
    for uniform in (
        "life",
        "breath_phase",
        "heartbeat",
        "mouth_pulse",
        "wetness",
        "goo_motion",
    ):
        assert f"uniform float {uniform}" in shader
    assert "pseudo-normal" in shader
    assert "Tongue gets its own" in shader


def test_scene_wires_sentient_layers_and_real_backbuffer():
    scene = (GODOT / "scenes" / "main.tscn").read_text(encoding="utf-8")
    for marker in (
        "LivingFace",
        "LifeAura",
        "BreathMist",
        "DroolMist",
        "shock_ring.gdshader",
        'type="BackBufferCopy"',
    ):
        assert marker in scene


def test_face_has_deterministic_blink_and_gaze():
    face = (GODOT / "scripts" / "living_face.gd").read_text(encoding="utf-8")
    assert "_rng.seed = 926183" in face
    assert "_update_blink" in face
    assert "_update_gaze" in face
    assert "_eye_open" in face


def test_godot_project_targets_supported_stable_line():
    project = (GODOT / "project.godot").read_text(encoding="utf-8")
    assert 'config/features=PackedStringArray("4.6", "Forward Plus")' in project
    assert "â" not in project
