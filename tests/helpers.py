"""Shared test helpers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO_WAV = ROOT / "assets" / "demo" / "demo_drop.wav"


def ensure_demo_wav() -> Path:
    """Generate the synthetic demo track if missing (CI / fresh clones)."""
    if DEMO_WAV.exists():
        return DEMO_WAV
    script = ROOT / "scripts" / "make_demo_track.py"
    subprocess.check_call([sys.executable, str(script)], cwd=str(ROOT))
    if not DEMO_WAV.exists():
        raise FileNotFoundError(f"Demo track was not created at {DEMO_WAV}")
    return DEMO_WAV
