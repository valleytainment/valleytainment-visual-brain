"""Section detector unit tests (no audio I/O)."""

import numpy as np

from vbrain.analyzer.sections import compute_drop_probability, detect_sections
from vbrain.schemas import SectionLabel, intensity_band


def test_intensity_band_edges():
    assert intensity_band(0.0).value == "BLACK"
    assert intensity_band(0.15).value == "MINIMAL"
    assert intensity_band(1.0).value == "APOCALYPSE"


def test_detect_sections_finds_drop():
    # 40s @ 128bpm synthetic intensity curve
    sr_hop = 0.1
    times = np.arange(0, 40, sr_hop)
    intensity = np.zeros_like(times)
    intensity[(times >= 0) & (times < 8)] = 0.15
    intensity[(times >= 8) & (times < 16)] = np.linspace(0.3, 0.8, np.sum((times >= 8) & (times < 16)))
    intensity[(times >= 16) & (times < 17)] = 0.05  # silence
    intensity[(times >= 17) & (times < 33)] = 0.95
    intensity[(times >= 33)] = 0.25

    kick = intensity.copy()
    bass = intensity.copy()
    brightness = np.clip(intensity * 0.7, 0, 1)
    drop = compute_drop_probability(intensity, kick, bass, intensity)

    sections = detect_sections(times, intensity, drop, bass, kick, brightness, bpm=128.0, min_bars=2.0)
    labels = [s.label for s in sections]
    assert SectionLabel.DROP in labels or SectionLabel.SECOND_DROP in labels
    assert any(s.label in (SectionLabel.INTRO, SectionLabel.BUILD, SectionLabel.PRE_DROP) for s in sections)
