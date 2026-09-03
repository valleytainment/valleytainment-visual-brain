"""Shared test helpers."""

from __future__ import annotations

from pathlib import Path

from vbrain.paths import ensure_demo_wav as ensure_demo_wav

ROOT = Path(__file__).resolve().parents[1]
DEMO_WAV = ROOT / "assets" / "demo" / "demo_drop.wav"

__all__ = ["DEMO_WAV", "ROOT", "ensure_demo_wav"]
