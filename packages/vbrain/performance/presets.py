"""Display / LED / OBS performance presets."""

from __future__ import annotations

from pydantic import BaseModel


class OutputPreset(BaseModel):
    id: str
    label: str
    width: int
    height: int
    notes: str = ""


OUTPUT_PRESETS: list[OutputPreset] = [
    OutputPreset(id="fhd", label="1080p LED / projector", width=1920, height=1080),
    OutputPreset(id="qhd", label="1440p stage", width=2560, height=1440),
    OutputPreset(id="uhd", label="4K LED wall", width=3840, height=2160),
    OutputPreset(id="square_led", label="Square LED tile", width=1080, height=1080),
    OutputPreset(id="portrait_led", label="Portrait LED totem", width=1080, height=1920),
    OutputPreset(id="obs_canvas", label="OBS canvas default", width=1920, height=1080),
]


def get_preset(preset_id: str) -> OutputPreset:
    for p in OUTPUT_PRESETS:
        if p.id == preset_id:
            return p
    return OUTPUT_PRESETS[0]


def randomize_seed(base: int, salt: int = 0) -> int:
    return int((base * 1000003 + salt * 9176) % 1_000_000_000)
