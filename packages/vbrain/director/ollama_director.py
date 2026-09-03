"""Visual directors: rule-based (offline) + optional local Ollama/Qwen."""

from __future__ import annotations

import json
import random
from typing import Protocol

import httpx

from vbrain.schemas import (
    CameraPlan,
    ParticlePlan,
    ScenePlan,
    SectionLabel,
    SectionSpan,
    ShaderPlan,
    SongAnalysis,
    VisualStory,
)

DIRECTOR_SYSTEM = """You are the visual director for an EDM festival performance.
Design a coherent visual narrative around this song.
Do not change visuals randomly.
Create environment, central subject, color state, camera movement,
particle behavior, shader behavior, transition, intensity, and visual metaphor
for every musical section. Respond with JSON only matching the schema."""


STYLE_PRESETS = {
    "biomechanical_cyber_cathedral": {
        "environment": "black chrome cathedral under a neon storm",
        "subject": "floating chrome skull angel",
        "palette": ["#0a0a0f", "#ff003c", "#4deeea", "#c0c0c0"],
    },
    "liquid_neon_void": {
        "environment": "infinite liquid neon void",
        "subject": "pulsing geometric idol",
        "palette": ["#050510", "#7b2fff", "#00ffa3", "#ffffff"],
    },
    "desert_rave_ruins": {
        "environment": "moonlit desert rave ruins",
        "subject": "colossal speaker monolith",
        "palette": ["#1a120b", "#ff6b2c", "#f0e6d2", "#2ec4b6"],
    },
}


SECTION_BEHAVIOR: dict[SectionLabel, dict] = {
    SectionLabel.INTRO: {
        "camera": "wide establishing drift",
        "particles": "sparse dust",
        "lighting": "single overhead beam",
        "shader": "atmospheric",
        "transition": "fade in",
        "bass_effect": "subtle breathe",
        "metaphor": "awakening",
    },
    SectionLabel.VERSE: {
        "camera": "slow orbit",
        "particles": "ambient drift",
        "lighting": "soft rim",
        "shader": "atmospheric",
        "transition": "crossfade",
        "bass_effect": "mesh pulse",
        "metaphor": "procession",
    },
    SectionLabel.BREAKDOWN: {
        "camera": "pull back",
        "particles": "falling ash",
        "lighting": "dim volumetric",
        "shader": "desaturate fog",
        "transition": "dissolve",
        "bass_effect": "slow wave",
        "metaphor": "collapse",
    },
    SectionLabel.BUILD: {
        "camera": "accelerating push",
        "particles": "inward spiral",
        "lighting": "strobing edges",
        "shader": "tension glitch",
        "transition": "hard cut risk",
        "bass_effect": "geometry wind-up",
        "metaphor": "compression",
    },
    SectionLabel.PRE_DROP: {
        "camera": "locked slow push",
        "particles": "reverse gravity",
        "lighting": "single overhead beam",
        "shader": "hold + micro stutter",
        "transition": "fracture",
        "bass_effect": "held displacement",
        "metaphor": "the held breath",
    },
    SectionLabel.SILENCE: {
        "camera": "freeze",
        "particles": "none",
        "lighting": "blackout",
        "shader": "black",
        "transition": "hard black",
        "bass_effect": "none",
        "metaphor": "void",
    },
    SectionLabel.DROP: {
        "camera": "rapid forward acceleration",
        "particles": "outward shockwave",
        "lighting": "strobe on kick",
        "shader": "apocalypse tunnel",
        "transition": "explosion cut",
        "bass_effect": "geometry displacement",
        "metaphor": "detonation",
    },
    SectionLabel.SECOND_DROP: {
        "camera": "barrel roll through tunnel",
        "particles": "shrapnel storm",
        "lighting": "dual strobe",
        "shader": "kaleidoscope fracture",
        "transition": "smash cut",
        "bass_effect": "heavy displacement",
        "metaphor": "second impact",
    },
    SectionLabel.POST_DROP: {
        "camera": "stabilizing glide",
        "particles": "ember trail",
        "lighting": "afterglow",
        "shader": "echo trails",
        "transition": "soft land",
        "bass_effect": "residual pulse",
        "metaphor": "aftermath",
    },
    SectionLabel.OUTRO: {
        "camera": "recede to void",
        "particles": "dissipating sparks",
        "lighting": "fade",
        "shader": "soft bloom",
        "transition": "fade out",
        "bass_effect": "dying pulse",
        "metaphor": "exhale",
    },
    SectionLabel.UNKNOWN: {
        "camera": "slow push forward",
        "particles": "ambient drift",
        "lighting": "soft rim",
        "shader": "atmospheric",
        "transition": "crossfade",
        "bass_effect": "subtle pulse",
        "metaphor": "searching",
    },
}


class VisualDirector(Protocol):
    def direct(self, analysis: SongAnalysis, style: str, seed: int) -> VisualStory: ...


class RuleBasedDirector:
    """Deterministic offline director — no LLM required."""

    def direct(self, analysis: SongAnalysis, style: str, seed: int) -> VisualStory:
        rng = random.Random(seed)
        preset = STYLE_PRESETS.get(style, STYLE_PRESETS["biomechanical_cyber_cathedral"])
        color_variants = list(preset["palette"])
        rng.shuffle(color_variants)

        scenes: list[ScenePlan] = []
        for section in analysis.sections:
            scenes.append(self._scene_for(section, preset, color_variants, rng))

        return VisualStory(
            title=f"{style.replace('_', ' ').title()} — Show {seed}",
            style=style,
            central_subject=preset["subject"],
            environment=preset["environment"],
            color_palette=preset["palette"],
            scenes=scenes,
            director_notes="Rule-based director (offline). Swap to OllamaDirector for Qwen.",
        )

    def _scene_for(
        self,
        section: SectionSpan,
        preset: dict,
        colors: list[str],
        rng: random.Random,
    ) -> ScenePlan:
        beh = SECTION_BEHAVIOR[section.label]
        world = preset["environment"]
        subject = preset["subject"]
        if section.label in (SectionLabel.DROP, SectionLabel.SECOND_DROP):
            world = f"{preset['environment']} explodes into infinite cybernetic tunnel"
            subject = f"{preset['subject']} shattering outward"
        elif section.label == SectionLabel.PRE_DROP:
            subject = f"{preset['subject']} — fracture held at the edge"

        glitch = min(1.0, section.intensity * (1.2 if "glitch" in beh["shader"] else 0.2))
        return ScenePlan(
            section=section.label,
            duration_bars=section.duration_bars,
            world=world,
            subject=subject,
            color_state=rng.choice(colors),
            camera=CameraPlan(
                movement=beh["camera"],
                shake=0.8
                if section.label in (SectionLabel.DROP, SectionLabel.SECOND_DROP)
                else 0.05,
                fov_bias=0.3 if section.label == SectionLabel.BUILD else 0.0,
            ),
            particles=ParticlePlan(
                behavior=beh["particles"],
                density=min(1.0, 0.2 + section.intensity * 0.8),
                gravity=-0.8 if "reverse" in beh["particles"] else -0.2,
            ),
            lighting=beh["lighting"],
            shader=ShaderPlan(
                family=beh["shader"],
                glitch=glitch,
                bloom=0.3 + section.intensity * 0.5,
                chromatic=section.intensity * 0.6,
                displacement=section.mean_bass,
            ),
            intensity=section.intensity,
            visual_metaphor=beh["metaphor"],
            transition=beh["transition"],
            bass_effect=beh["bass_effect"],
        )


class OllamaDirector:
    """Local LLM director via Ollama (Qwen3/Qwen3.5). Falls back to rules on failure."""

    def __init__(
        self,
        model: str = "qwen3:8b",
        base_url: str = "http://127.0.0.1:11434",
        timeout: float = 120.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._fallback = RuleBasedDirector()

    def direct(self, analysis: SongAnalysis, style: str, seed: int) -> VisualStory:
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": DIRECTOR_SYSTEM},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "style": style,
                            "seed": seed,
                            "bpm": analysis.bpm,
                            "key": analysis.key_estimate,
                            "duration_s": analysis.duration_s,
                            "sections": [s.model_dump() for s in analysis.sections],
                            "schema_hint": VisualStory.model_json_schema(),
                        },
                        default=str,
                    ),
                },
            ],
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.post(f"{self.base_url}/api/chat", json=payload)
                r.raise_for_status()
                content = r.json()["message"]["content"]
            data = json.loads(content)
            return VisualStory.model_validate(data)
        except Exception:
            story = self._fallback.direct(analysis, style, seed)
            story.director_notes = f"Ollama unavailable or invalid JSON (model={self.model}); used rule-based fallback."
            return story
