"""Full-track analysis → SongAnalysis (song map).

Uses numpy/scipy/soundfile only (no librosa/numba) so install works on macOS
without compiling llvmlite. Optional librosa path can be layered later.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal
from scipy.ndimage import uniform_filter1d

from vbrain.analyzer.features import (
    band_energy,
    estimate_key,
    normalize,
    rhythmic_density,
    smooth,
    spectral_brightness,
)
from vbrain.analyzer.sections import compute_drop_probability, compute_tension, detect_sections
from vbrain.analyzer.stems import separate_stems
from vbrain.schemas import BeatEvent, FrameFeatures, SectionLabel, SongAnalysis


def _load_mono(path: Path, target_sr: int) -> tuple[np.ndarray, int]:
    y, file_sr = sf.read(str(path), always_2d=True)
    y = np.mean(y, axis=1).astype(np.float64)
    if file_sr != target_sr:
        # polyphase resample
        gcd = np.gcd(file_sr, target_sr)
        up, down = target_sr // gcd, file_sr // gcd
        y = signal.resample_poly(y, up, down)
    return y, target_sr


def _stft_mag(y: np.ndarray, n_fft: int, hop: int) -> tuple[np.ndarray, np.ndarray]:
    _, _, zxx = signal.stft(
        y,
        nperseg=n_fft,
        noverlap=n_fft - hop,
        window="hann",
        boundary=None,
        padded=False,
    )
    return np.abs(zxx), np.fft.rfftfreq(n_fft)


def _onset_envelope(mag: np.ndarray) -> np.ndarray:
    """Spectral flux onset strength."""
    flux = np.diff(mag, axis=1, prepend=mag[:, :1])
    flux = np.maximum(0.0, flux)
    return normalize(np.sum(flux, axis=0))


def _estimate_tempo(onset_env: np.ndarray, sr: int, hop: int) -> float:
    """Autocorrelation tempo estimate constrained to EDM-ish range."""
    if len(onset_env) < 8:
        return 128.0
    env = onset_env - np.mean(onset_env)
    corr = signal.correlate(env, env, mode="full")
    corr = corr[len(corr) // 2 :]
    # lag in frames for 70–180 BPM
    fps = sr / hop
    min_lag = max(1, int(fps * 60.0 / 180.0))
    max_lag = max(min_lag + 1, int(fps * 60.0 / 70.0))
    max_lag = min(max_lag, len(corr) - 1)
    if max_lag <= min_lag:
        return 128.0
    segment = corr[min_lag:max_lag]
    lag = int(np.argmax(segment)) + min_lag
    bpm = 60.0 * fps / max(lag, 1)
    # Prefer double-time / half-time into dance range
    while bpm < 90:
        bpm *= 2
    while bpm > 180:
        bpm /= 2
    return float(np.clip(bpm, 70.0, 180.0))


def _beat_track(onset_env: np.ndarray, sr: int, hop: int, bpm: float) -> np.ndarray:
    """Simple beat grid snapped to onset peaks near expected period."""
    fps = sr / hop
    period = max(1, int(round(fps * 60.0 / bpm)))
    # Pick strongest onset in each period window
    beats = []
    i = 0
    n = len(onset_env)
    # Start near first strong onset
    start = int(np.argmax(onset_env[: min(n, period * 2)]))
    i = start
    while i < n:
        lo = max(0, i - period // 4)
        hi = min(n, i + period // 4 + 1)
        local = lo + int(np.argmax(onset_env[lo:hi]))
        beats.append(local)
        i = local + period
    if not beats:
        beats = list(range(0, n, period))
    times = np.array(beats, dtype=np.float64) * (hop / sr)
    return times


def _chroma(y: np.ndarray, sr: int) -> np.ndarray:
    """Lightweight chroma via STFT folded into 12 pitch classes."""
    n_fft = 4096
    hop = 2048
    mag, freqs = _stft_mag(y, n_fft=n_fft, hop=hop)
    # map freqs to MIDI pitch classes
    chroma = np.zeros((12, mag.shape[1]), dtype=np.float64)
    for fi, f in enumerate(freqs * sr):  # freqs from rfftfreq are cycles/sample
        hz = f
        if hz < 50 or hz > 5000:
            continue
        midi = 69 + 12 * np.log2(hz / 440.0)
        pc = int(np.round(midi)) % 12
        chroma[pc] += mag[fi]
    return chroma


def analyze_track(
    track_path: str | Path,
    *,
    sr: int = 22050,
    hop_length: int = 512,
    frame_stride: int = 4,
    separate: bool = False,
    stems_dir: str | Path | None = None,
) -> SongAnalysis:
    path = Path(track_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Track not found: {path}")

    y, sr = _load_mono(path, sr)
    duration = float(len(y) / sr)
    n_fft = 2048

    mag, freqs_norm = _stft_mag(y, n_fft=n_fft, hop=hop_length)
    freqs = freqs_norm * sr
    n = mag.shape[1]
    times = np.arange(n, dtype=np.float64) * (hop_length / sr)

    kick = normalize(smooth(band_energy(mag, freqs, 40, 120)))
    bass = normalize(smooth(band_energy(mag, freqs, 40, 250)))
    snare = normalize(smooth(band_energy(mag, freqs, 150, 500)))
    hat = normalize(smooth(band_energy(mag, freqs, 5000, 12000)))
    vocal = normalize(smooth(band_energy(mag, freqs, 300, 3400)))
    brightness = smooth(spectral_brightness(mag, freqs))
    loudness = normalize(smooth(np.sqrt(np.mean(np.square(mag), axis=0) + 1e-12)))

    onset_env = _onset_envelope(mag)
    # light temporal smoothing for tempo
    onset_smooth = normalize(uniform_filter1d(onset_env.astype(np.float64), size=5, mode="nearest"))
    bpm = _estimate_tempo(onset_smooth, sr, hop_length)
    beat_times = _beat_track(onset_smooth, sr, hop_length, bpm)

    beats: list[BeatEvent] = []
    for i, t in enumerate(beat_times):
        beats.append(
            BeatEvent(
                t=float(t),
                beat_index=i,
                bar_index=i // 4,
                is_downbeat=(i % 4 == 0),
            )
        )

    density = rhythmic_density(onset_env, times)
    intensity = normalize(smooth(0.4 * kick + 0.3 * bass + 0.2 * loudness + 0.1 * density))
    drop_prob = compute_drop_probability(intensity, kick, bass, density)
    tension = compute_tension(intensity, brightness, density)

    sections = detect_sections(times, intensity, drop_prob, bass, kick, brightness, bpm=bpm)

    def section_at(t: float) -> SectionLabel:
        for s in sections:
            if s.start_t <= t <= s.end_t:
                return s.label
        return SectionLabel.UNKNOWN

    frames: list[FrameFeatures] = []
    for i in range(0, n, max(1, frame_stride)):
        t = float(times[i])
        frames.append(
            FrameFeatures(
                t=t,
                bass_energy=float(bass[i]),
                kick_energy=float(kick[i]),
                snare_energy=float(snare[i]),
                hat_energy=float(hat[i]),
                vocal_energy=float(vocal[i]),
                spectral_brightness=float(brightness[i]),
                loudness=float(loudness[i]),
                rhythmic_density=float(density[i]),
                tension=float(tension[i]),
                drop_probability=float(drop_prob[i]),
                intensity=float(intensity[i]),
                section=section_at(t),
            )
        )

    key_estimate = estimate_key(_chroma(y, sr))

    stem_paths: dict[str, str] = {}
    if separate:
        out = Path(stems_dir) if stems_dir else path.parent / "stems" / path.stem
        stem_paths = separate_stems(path, out)

    bar_count = max(1, (len(beats) + 3) // 4)

    return SongAnalysis(
        track_path=str(path),
        duration_s=duration,
        sample_rate=sr,
        bpm=round(bpm, 3),
        beat_count=len(beats),
        bar_count=bar_count,
        key_estimate=key_estimate,
        beats=beats,
        sections=sections,
        frames=frames,
        stem_paths=stem_paths,
        meta={
            "hop_length": hop_length,
            "frame_stride": frame_stride,
            "analyzer": "vbrain.analyzer.pipeline",
            "backend": "scipy",
            "version": "0.1.0",
        },
    )
