"""Small filesystem helpers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def ensure_demo_wav() -> Path:
    root = repo_root()
    demo = root / "assets" / "demo" / "demo_drop.wav"
    if demo.exists():
        return demo
    script = root / "scripts" / "make_demo_track.py"
    subprocess.check_call([sys.executable, str(script)], cwd=str(root))
    if not demo.exists():
        raise FileNotFoundError(f"Demo track was not created at {demo}")
    return demo
