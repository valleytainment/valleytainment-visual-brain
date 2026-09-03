"""EDM-oriented section / drop detection from energy curves."""

from __future__ import annotations

import numpy as np

from vbrain.schemas import (
    SECTION_DEFAULT_INTENSITY,
    IntensityBand,
    SectionLabel,
    SectionSpan,
    intensity_band,
)


def _label_from_state(
    intensity: float,
    drop_prob: float,
    rising: bool,
    falling: bool,
    low_energy: bool,
    near_silence: bool,
) -> SectionLabel:
    if near_silence:
        return SectionLabel.SILENCE
    # Sustained heavy body OR sharp drop onset
    if intensity >= 0.82 or (drop_prob >= 0.72 and intensity >= 0.70):
        return SectionLabel.DROP
    if (drop_prob >= 0.55 and rising and intensity >= 0.45) or (
        intensity >= 0.75 and rising
    ):
        return SectionLabel.PRE_DROP
    if rising and intensity >= 0.32:
        return SectionLabel.BUILD
    if low_energy and falling:
        return SectionLabel.BREAKDOWN
    if intensity <= 0.2:
        return SectionLabel.INTRO if intensity < 0.18 else SectionLabel.OUTRO
    return SectionLabel.VERSE


def detect_sections(
    times: np.ndarray,
    intensity: np.ndarray,
    drop_prob: np.ndarray,
    bass: np.ndarray,
    kick: np.ndarray,
    brightness: np.ndarray,
    bpm: float,
    min_bars: float = 4.0,
) -> list[SectionSpan]:
    """Segment a track into EDM-ish sections using intensity + drop probability."""
    if len(times) == 0:
        return []

    bar_dur = (60.0 / max(bpm, 1.0)) * 4.0
    min_dur = bar_dur * min_bars

    # Derivatives for rise/fall context
    d_int = np.gradient(intensity)
    rising = d_int > 0.008
    falling = d_int < -0.008
    low_energy = intensity < 0.28
    near_silence = intensity < 0.06

    labels = [
        _label_from_state(
            float(intensity[i]),
            float(drop_prob[i]),
            bool(rising[i]),
            bool(falling[i]),
            bool(low_energy[i]),
            bool(near_silence[i]),
        )
        for i in range(len(times))
    ]

    # Merge short fragments into neighbors
    spans: list[tuple[SectionLabel, int, int]] = []
    start = 0
    for i in range(1, len(labels)):
        if labels[i] != labels[start]:
            spans.append((labels[start], start, i))
            start = i
    spans.append((labels[start], start, len(labels)))

    merged: list[tuple[SectionLabel, int, int]] = []
    for label, a, b in spans:
        dur = float(times[min(b - 1, len(times) - 1)] - times[a])
        if merged and dur < min_dur:
            prev_label, pa, _ = merged[-1]
            merged[-1] = (prev_label, pa, b)
        else:
            merged.append((label, a, b))

    # Promote consecutive high-energy DROP after first DROP → SECOND_DROP
    seen_drop = False
    promoted: list[tuple[SectionLabel, int, int]] = []
    for label, a, b in merged:
        if label == SectionLabel.DROP:
            if seen_drop:
                label = SectionLabel.SECOND_DROP
            seen_drop = True
        promoted.append((label, a, b))

    # Fix first/last heuristics
    if promoted:
        first_label, a, b = promoted[0]
        if float(np.mean(intensity[a:b])) < 0.3:
            promoted[0] = (SectionLabel.INTRO, a, b)
        last_label, a, b = promoted[-1]
        if last_label not in (SectionLabel.DROP, SectionLabel.SECOND_DROP) and float(
            np.mean(intensity[a:b])
        ) < 0.35:
            promoted[-1] = (SectionLabel.OUTRO, a, b)

    sections: list[SectionSpan] = []
    for label, a, b in promoted:
        start_t = float(times[a])
        end_t = float(times[min(b, len(times) - 1)])
        if b >= len(times):
            end_t = float(times[-1])
        start_bar = int(start_t / bar_dur)
        end_bar = max(start_bar + 1, int(end_t / bar_dur))
        mean_intensity = float(np.mean(intensity[a:b]))
        # Prefer musical default intensity, blended with measured
        default = SECTION_DEFAULT_INTENSITY.get(label, 0.35)
        final_intensity = float(np.clip(0.45 * mean_intensity + 0.55 * default, 0.0, 1.0))
        sections.append(
            SectionSpan(
                label=label,
                start_t=start_t,
                end_t=end_t,
                start_bar=start_bar,
                end_bar=end_bar,
                duration_bars=max(1, end_bar - start_bar),
                intensity=final_intensity,
                intensity_band=intensity_band(final_intensity),
                drop_probability=float(np.max(drop_prob[a:b])),
                mean_bass=float(np.mean(bass[a:b])),
                mean_kick=float(np.mean(kick[a:b])),
                mean_brightness=float(np.mean(brightness[a:b])),
            )
        )
    return sections


def compute_tension(intensity: np.ndarray, brightness: np.ndarray, density: np.ndarray) -> np.ndarray:
    raw = 0.5 * intensity + 0.25 * brightness + 0.25 * density
    return np.clip(raw, 0.0, 1.0)


def compute_drop_probability(
    intensity: np.ndarray,
    kick: np.ndarray,
    bass: np.ndarray,
    density: np.ndarray,
) -> np.ndarray:
    """Heuristic drop likelihood: rising energy + sustained kick/bass body."""
    d = np.gradient(intensity)
    surge = np.clip(d * 8.0, 0.0, 1.0)
    # Keep surge elevated briefly after onset so DROP spans hold
    if len(surge) > 3:
        kernel = np.array([0.15, 0.25, 0.35, 0.25], dtype=np.float64)
        surge = np.convolve(surge, kernel, mode="same")
        surge = np.clip(surge, 0.0, 1.0)
    body = 0.35 * intensity + 0.25 * kick + 0.25 * bass + 0.15 * density
    heavy = np.clip((intensity - 0.65) / 0.35, 0.0, 1.0)
    return np.clip(0.40 * body + 0.30 * surge + 0.30 * heavy, 0.0, 1.0)
