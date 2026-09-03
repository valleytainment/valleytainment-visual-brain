#!/usr/bin/env python3
"""Synthesize a short EDM-ish fixture: intro → build → drop → outro."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf


def main() -> None:
    sr = 22050
    bpm = 128.0
    beat = 60.0 / bpm
    rng = np.random.default_rng(7)

    def kick(n: int) -> np.ndarray:
        t = np.arange(n) / sr
        env = np.exp(-t * 28)
        return 0.9 * env * np.sin(2 * np.pi * (80 * np.exp(-t * 20)) * t)

    def hat(n: int) -> np.ndarray:
        t = np.arange(n) / sr
        env = np.exp(-t * 60)
        return 0.15 * env * rng.standard_normal(n)

    def bass_tone(n: int, freq: float, amp: float) -> np.ndarray:
        t = np.arange(n) / sr
        return amp * np.sin(2 * np.pi * freq * t)

    sections = [
        ("intro", 8, 0.18, False),
        ("build", 8, 0.45, False),
        ("silence", 2, 0.0, False),
        ("drop", 16, 1.0, True),
        ("outro", 8, 0.22, False),
    ]

    parts: list[np.ndarray] = []
    for name, bars, energy, heavy in sections:
        n_beats = bars * 4
        for b in range(n_beats):
            n = int(beat * sr)
            buf = np.zeros(n, dtype=np.float64)
            if name == "silence":
                parts.append(buf)
                continue
            # four-on-the-floor kicks stronger on drop
            build_ramp = 1.0
            if name == "build":
                build_ramp = 0.5 + 0.5 * (b / max(n_beats - 1, 1))
            k = kick(n) * (1.15 if heavy else 0.45) * energy * build_ramp
            buf[: len(k)] += k
            if b % 2 == 0:
                h = hat(n // 2)
                buf[: len(h)] += h * energy * (1.4 if heavy else 0.8)
            if heavy or energy > 0.35:
                buf += bass_tone(n, 50.0 if heavy else 65.0, (0.45 if heavy else 0.18) * energy)
            if heavy:
                burst = np.exp(-np.arange(n) / sr * 40) * rng.standard_normal(n) * 0.4
                buf += burst
            elif name == "build" and b % 4 == 3:
                burst = np.exp(-np.arange(n) / sr * 50) * rng.standard_normal(n) * 0.2 * build_ramp
                buf += burst
            parts.append(buf)

    audio = np.concatenate(parts)
    audio = audio / (np.max(np.abs(audio)) + 1e-9) * 0.9
    out = Path(__file__).resolve().parents[1] / "assets" / "demo" / "demo_drop.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, audio.astype(np.float32), sr)
    print(f"Wrote {out} ({len(audio) / sr:.1f}s @ {bpm} BPM)")


if __name__ == "__main__":
    main()
