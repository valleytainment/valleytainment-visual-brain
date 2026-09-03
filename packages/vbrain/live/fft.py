"""FFT band helpers for live mode.

The original prototype normalized every chunk by its loudest band. That makes
near-silence look energetic because one band is always promoted to 1.0. This
implementation separates absolute loudness from spectral balance so quiet audio
stays quiet while the relative band mix still drives the visual instrument.
"""

from __future__ import annotations

import numpy as np

SILENCE_EPS = 1e-9


def _db_unit(amplitude: float, floor_db: float = -60.0, ceiling_db: float = -8.0) -> float:
    """Map linear full-scale amplitude to a stable 0..1 perceptual range."""
    db = 20.0 * np.log10(max(float(amplitude), SILENCE_EPS))
    return float(np.clip((db - floor_db) / (ceiling_db - floor_db), 0.0, 1.0))


def live_bands(samples: np.ndarray, sr: int = 44100) -> dict[str, float]:
    """Return level-aware normalized band energies for a mono float buffer.

    Inputs are expected to be floating-point audio around -1..1. Band values are
    based on the fraction of spectral power in each range multiplied by an
    absolute dBFS loudness gate. This avoids noise-floor false drops.
    """
    if samples.size == 0:
        return {
            "kick": 0.0,
            "bass": 0.0,
            "snare": 0.0,
            "mid": 0.0,
            "vocal": 0.0,
            "hat": 0.0,
            "loudness": 0.0,
        }

    mono = np.asarray(samples, dtype=np.float64).reshape(-1)
    if not np.all(np.isfinite(mono)):
        mono = np.nan_to_num(mono, nan=0.0, posinf=0.0, neginf=0.0)

    rms = float(np.sqrt(np.mean(np.square(mono)) + SILENCE_EPS))
    loudness = _db_unit(rms)
    if loudness <= 0.0:
        return {
            "kick": 0.0,
            "bass": 0.0,
            "snare": 0.0,
            "mid": 0.0,
            "vocal": 0.0,
            "hat": 0.0,
            "loudness": 0.0,
        }

    window = np.hanning(len(mono))
    windowed = mono * window
    spec = np.abs(np.fft.rfft(windowed))
    power = np.square(spec)
    freqs = np.fft.rfftfreq(len(windowed), d=1.0 / sr)
    total_power = float(np.sum(power)) + SILENCE_EPS

    def spectral_share(lo: float, hi: float, gain: float = 1.0) -> float:
        mask = (freqs >= lo) & (freqs < hi)
        if not np.any(mask):
            return 0.0
        share = np.sqrt(float(np.sum(power[mask])) / total_power)
        return float(np.clip(share * loudness * gain, 0.0, 1.0))

    return {
        "kick": spectral_share(38, 125, 1.35),
        "bass": spectral_share(38, 260, 1.18),
        "snare": spectral_share(140, 2600, 1.12),
        "mid": spectral_share(250, 4200, 1.05),
        "vocal": spectral_share(300, 3600, 1.08),
        "hat": spectral_share(5000, min(18000, sr / 2), 1.55),
        "loudness": loudness,
    }
