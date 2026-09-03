"""Godot runtime.json contract — shared between Python exporter and engine."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from vbrain.schemas import FrameFeatures, SectionSpan


class RuntimeStory(BaseModel):
    title: str
    central_subject: str = ""
    environment: str = ""
    color_palette: list[str] = Field(default_factory=list)
    scenes: list[dict[str, Any]] = Field(default_factory=list)


class RuntimeExport(BaseModel):
    """Compact show payload consumed by apps/visual-engine."""

    show_id: str
    mode: str = "PREPARED"
    bpm: float
    duration_s: float
    key: str | None = None
    seed: int = 0
    style: str = ""
    artist: str = "Valleytainment"
    randomization: dict[str, float] = Field(default_factory=dict)
    sections: list[SectionSpan] = Field(default_factory=list)
    cues: list[dict[str, Any]] = Field(default_factory=list)
    story: RuntimeStory
    frames: list[FrameFeatures] = Field(default_factory=list)
    hero_scene: str = "valleytainment_logo"

    @field_validator("bpm")
    @classmethod
    def bpm_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("bpm must be positive")
        return v

    @field_validator("duration_s")
    @classmethod
    def duration_nonneg(cls, v: float) -> float:
        if v < 0:
            raise ValueError("duration_s must be >= 0")
        return v

    @field_validator("frames")
    @classmethod
    def frames_sorted(cls, frames: list[FrameFeatures]) -> list[FrameFeatures]:
        if len(frames) >= 2:
            times = [f.t for f in frames]
            if any(times[i] > times[i + 1] for i in range(len(times) - 1)):
                raise ValueError("frames must be sorted by t ascending")
        return frames
