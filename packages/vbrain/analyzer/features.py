"""Low-level spectral / rhythmic feature extraction."""

from __future__ import annotations

import numpy as np


def band_energy(mag: np.ndarray, freqs: np.ndarray, lo: float, hi: float) -> np.ndarray:
    mask = (freqs >= lo) & (freqs < hi)
    if not np.any(mask):
        return np.zeros(mag.shape[1], dtype=np.float64)
    band = mag[mask]
    return np.sqrt(np.mean(np.square(band), axis=0) + 1e-12)


def normalize(x: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    mn, mx = float(np.min(x)), float(np.max(x))
    if mx - mn < eps:
        return np.zeros_like(x)
    return (x - mn) / (mx - mn)


def smooth(x: np.ndarray, win: int = 9) -> np.ndarray:
    if win < 2 or len(x) < win:
        return x
    kernel = np.ones(win, dtype=np.float64) / win
    return np.convolve(x, kernel, mode="same")


def spectral_brightness(mag: np.ndarray, freqs: np.ndarray) -> np.ndarray:
    """Centroid-like brightness normalized 0..1 against Nyquist."""
    power = np.square(mag) + 1e-12
    centroid = np.sum(freqs[:, None] * power, axis=0) / np.sum(power, axis=0)
    nyquist = float(freqs[-1]) if len(freqs) else 1.0
    return np.clip(centroid / max(nyquist, 1.0), 0.0, 1.0)


def rhythmic_density(onset_env: np.ndarray, hop_times: np.ndarray, window_s: float = 2.0) -> np.ndarray:
    """Local onset activity density."""
    if len(onset_env) == 0:
        return onset_env
    dens = np.zeros_like(onset_env)
    half = window_s / 2.0
    for i, t in enumerate(hop_times):
        lo = np.searchsorted(hop_times, t - half)
        hi = np.searchsorted(hop_times, t + half)
        dens[i] = float(np.mean(onset_env[lo:hi])) if hi > lo else 0.0
    return normalize(dens)


def estimate_key(chroma: np.ndarray) -> str:
    """Very lightweight major/minor key guess from mean chroma."""
    if chroma.size == 0:
        return "unknown"
    pitch_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    major = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1], dtype=np.float64)
    minor = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0], dtype=np.float64)
    profile = np.mean(chroma, axis=1)
    best_score = -1e9
    best = "unknown"
    for i, name in enumerate(pitch_names):
        maj = float(np.dot(np.roll(major, i), profile))
        min_ = float(np.dot(np.roll(minor, i), profile))
        if maj > best_score:
            best_score, best = maj, f"{name} major"
        if min_ > best_score:
            best_score, best = min_, f"{name} minor"
    return best
