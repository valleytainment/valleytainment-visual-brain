"""Intensity mapping for musical sections and live frames."""

from __future__ import annotations

from vbrain.schemas import SECTION_DEFAULT_INTENSITY, SectionLabel, SectionSpan, intensity_band


def map_intensity(value: float) -> tuple[float, str]:
    v = max(0.0, min(1.0, float(value)))
    return v, intensity_band(v).value


def intensity_curve_for_section(section: SectionSpan) -> list[tuple[str, float]]:
    """Return a simple intensity envelope for a section (start → end)."""
    base = SECTION_DEFAULT_INTENSITY.get(section.label, section.intensity)
    if section.label == SectionLabel.BUILD:
        return [("start", 0.40), ("mid", 0.65), ("end", 0.85)]
    if section.label == SectionLabel.PRE_DROP:
        return [("start", 0.85), ("end", 0.95)]
    if section.label == SectionLabel.DROP:
        return [("start", 1.0), ("end", 0.9)]
    if section.label == SectionLabel.SILENCE:
        return [("start", 0.0), ("end", 0.0)]
    return [("start", base), ("end", base)]
