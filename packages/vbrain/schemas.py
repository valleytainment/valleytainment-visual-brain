"""Shared show-pack schemas used by analyzer, director, and Godot engine."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SectionLabel(str, Enum):
    INTRO = "INTRO"
    VERSE = "VERSE"
    BREAKDOWN = "BREAKDOWN"
    BUILD = "BUILD"
    PRE_DROP = "PRE_DROP"
    SILENCE = "SILENCE"
    DROP = "DROP"
    SECOND_DROP = "SECOND_DROP"
    POST_DROP = "POST_DROP"
    OUTRO = "OUTRO"
    UNKNOWN = "UNKNOWN"


class IntensityBand(str, Enum):
    BLACK = "BLACK"
    MINIMAL = "MINIMAL"
    ATMOSPHERIC = "ATMOSPHERIC"
    BUILDING = "BUILDING"
    ENERGETIC = "ENERGETIC"
    HEAVY = "HEAVY"
    APOCALYPSE = "APOCALYPSE"


INTENSITY_THRESHOLDS: list[tuple[float, IntensityBand]] = [
    (0.00, IntensityBand.BLACK),
    (0.10, IntensityBand.MINIMAL),
    (0.25, IntensityBand.ATMOSPHERIC),
    (0.40, IntensityBand.BUILDING),
    (0.60, IntensityBand.ENERGETIC),
    (0.80, IntensityBand.HEAVY),
    (1.00, IntensityBand.APOCALYPSE),
]

SECTION_DEFAULT_INTENSITY: dict[SectionLabel, float] = {
    SectionLabel.INTRO: 0.15,
    SectionLabel.VERSE: 0.25,
    SectionLabel.BREAKDOWN: 0.20,
    SectionLabel.BUILD: 0.55,
    SectionLabel.PRE_DROP: 0.90,
    SectionLabel.SILENCE: 0.00,
    SectionLabel.DROP: 1.00,
    SectionLabel.SECOND_DROP: 0.95,
    SectionLabel.POST_DROP: 0.65,
    SectionLabel.OUTRO: 0.20,
    SectionLabel.UNKNOWN: 0.35,
}


def intensity_band(value: float) -> IntensityBand:
    clamped = max(0.0, min(1.0, value))
    band = IntensityBand.BLACK
    for threshold, name in INTENSITY_THRESHOLDS:
        if clamped >= threshold:
            band = name
    return band


class FrameFeatures(BaseModel):
    """Per-hop music features (exported sparsely into analysis.json)."""

    t: float
    bass_energy: float = 0.0
    kick_energy: float = 0.0
    snare_energy: float = 0.0
    hat_energy: float = 0.0
    vocal_energy: float = 0.0
    spectral_brightness: float = 0.0
    loudness: float = 0.0
    rhythmic_density: float = 0.0
    tension: float = 0.0
    drop_probability: float = 0.0
    intensity: float = 0.0
    section: SectionLabel = SectionLabel.UNKNOWN


class BeatEvent(BaseModel):
    t: float
    beat_index: int
    bar_index: int
    is_downbeat: bool = False


class SectionSpan(BaseModel):
    label: SectionLabel
    start_t: float
    end_t: float
    start_bar: int
    end_bar: int
    duration_bars: int
    intensity: float
    intensity_band: IntensityBand
    drop_probability: float = 0.0
    mean_bass: float = 0.0
    mean_kick: float = 0.0
    mean_brightness: float = 0.0


class SongAnalysis(BaseModel):
    track_path: str
    duration_s: float
    sample_rate: int
    bpm: float
    beat_count: int
    bar_count: int
    key_estimate: str | None = None
    beats: list[BeatEvent] = Field(default_factory=list)
    sections: list[SectionSpan] = Field(default_factory=list)
    frames: list[FrameFeatures] = Field(default_factory=list)
    stem_paths: dict[str, str] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)


class CameraPlan(BaseModel):
    movement: str = "slow push forward"
    shake: float = 0.0
    fov_bias: float = 0.0


class ParticlePlan(BaseModel):
    behavior: str = "ambient drift"
    density: float = 0.3
    gravity: float = -0.2


class ShaderPlan(BaseModel):
    family: str = "atmospheric"
    glitch: float = 0.0
    bloom: float = 0.3
    chromatic: float = 0.0
    displacement: float = 0.0


class ScenePlan(BaseModel):
    section: SectionLabel
    duration_bars: int
    world: str
    subject: str
    color_state: str
    camera: CameraPlan = Field(default_factory=CameraPlan)
    particles: ParticlePlan = Field(default_factory=ParticlePlan)
    lighting: str = "soft rim"
    shader: ShaderPlan = Field(default_factory=ShaderPlan)
    intensity: float = 0.5
    visual_metaphor: str = ""
    transition: str = "crossfade"
    bass_effect: str = "subtle pulse"
    notes: str = ""


class VisualStory(BaseModel):
    title: str
    style: str
    central_subject: str
    environment: str
    color_palette: list[str] = Field(default_factory=list)
    scenes: list[ScenePlan] = Field(default_factory=list)
    director_notes: str = ""


class ShowSeed(BaseModel):
    show_seed: int
    artist: str = "Valleytainment"
    style: str = "biomechanical_cyber_cathedral"
    randomization: dict[str, float] = Field(
        default_factory=lambda: {
            "camera": 0.3,
            "particles": 0.7,
            "environment": 0.2,
            "shader": 0.4,
        }
    )


class CueEvent(BaseModel):
    t: float
    bar: int
    section: SectionLabel
    intensity: float
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)


class CueMap(BaseModel):
    cues: list[CueEvent] = Field(default_factory=list)


class ShowPack(BaseModel):
    show_id: str
    mode: str = "PREPARED"  # PREPARED | LIVE | HYBRID
    analysis: SongAnalysis
    visual_story: VisualStory
    show_seed: ShowSeed
    cue_map: CueMap
