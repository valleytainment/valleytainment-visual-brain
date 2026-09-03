"""FFT band helpers for live mode."""

from __future__ import annotations

import numpy as np


def live_bands(samples: np.ndarray, sr: int = 44100) -> dict[str, float]:
    """Return normalized band energies for a mono float buffer."""
    if samples.size == 0:
        return {
            "kick": 0.0,
            "bass": 0.0,
            "mid": 0.0,
            "hat": 0.0,
            "loudness": 0.0,
        }
    windowed = samples * np.hanning(len(samples))
    spec = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(len(windowed), d=1.0 / sr)

    def energy(lo: float, hi: float) -> float:
        mask = (freqs >= lo) & (freqs < hi)
        if not np.any(mask):
            return 0.0
        return float(np.sqrt(np.mean(np.square(spec[mask])) + 1e-12))

    raw = {
        "kick": energy(40, 120),
        "bass": energy(40, 250),
        "mid": energy(250, 4000),
        "hat": energy(5000, 12000),
        "loudness": float(np.sqrt(np.mean(np.square(samples)) + 1e-12)),
    }
    peak = max(raw.values()) or 1.0
    return {k: float(min(1.0, v / peak)) for k, v in raw.items()}
