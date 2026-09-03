"""Compile analysis + director output into a full show pack + cue map."""

from __future__ import annotations

import re
from pathlib import Path

from vbrain.director.ollama_director import OllamaDirector, RuleBasedDirector
from vbrain.schemas import (
    CueEvent,
    CueMap,
    ShowPack,
    ShowSeed,
    SongAnalysis,
    VisualStory,
)


def _slug(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return s or "show"


def build_cue_map(analysis: SongAnalysis, story: VisualStory) -> CueMap:
    cues: list[CueEvent] = []
    scene_by_section = {s.section: s for s in story.scenes}

    for section in analysis.sections:
        scene = scene_by_section.get(section.label)
        cues.append(
            CueEvent(
                t=section.start_t,
                bar=section.start_bar,
                section=section.label,
                intensity=section.intensity,
                action="enter_section",
                payload={
                    "world": scene.world if scene else "",
                    "subject": scene.subject if scene else "",
                    "transition": scene.transition if scene else "crossfade",
                    "shader": scene.shader.model_dump() if scene else {},
                    "camera": scene.camera.model_dump() if scene else {},
                    "particles": scene.particles.model_dump() if scene else {},
                    "end_t": section.end_t,
                },
            )
        )
        if section.label.value in {"DROP", "SECOND_DROP", "PRE_DROP", "SILENCE"}:
            cues.append(
                CueEvent(
                    t=section.start_t,
                    bar=section.start_bar,
                    section=section.label,
                    intensity=section.intensity,
                    action=f"trigger_{section.label.value.lower()}",
                    payload={"duration_bars": section.duration_bars},
                )
            )
    cues.sort(key=lambda c: (c.t, c.action))
    return CueMap(cues=cues)


def plan_show(
    analysis: SongAnalysis,
    *,
    style: str = "biomechanical_cyber_cathedral",
    seed: int = 926183,
    artist: str = "Valleytainment",
    use_ollama: bool = False,
    ollama_model: str = "qwen3:8b",
    show_id: str | None = None,
    mode: str = "PREPARED",
) -> ShowPack:
    director = OllamaDirector(model=ollama_model) if use_ollama else RuleBasedDirector()
    story = director.direct(analysis, style=style, seed=seed)
    show_seed = ShowSeed(show_seed=seed, artist=artist, style=style)
    cue_map = build_cue_map(analysis, story)
    sid = show_id or f"{_slug(Path(analysis.track_path).stem)}-{seed}"
    return ShowPack(
        show_id=sid,
        mode=mode,
        analysis=analysis,
        visual_story=story,
        show_seed=show_seed,
        cue_map=cue_map,
    )
