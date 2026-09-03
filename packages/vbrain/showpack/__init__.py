"""Persist / load show packs for the Godot performance engine."""

from __future__ import annotations

import json
from pathlib import Path

from vbrain.schemas import ShowPack


def write_show_pack(pack: ShowPack, shows_root: str | Path) -> Path:
    root = Path(shows_root).expanduser().resolve()
    show_dir = root / pack.show_id
    show_dir.mkdir(parents=True, exist_ok=True)

    (show_dir / "analysis.json").write_text(
        pack.analysis.model_dump_json(indent=2), encoding="utf-8"
    )
    (show_dir / "visual_story.json").write_text(
        pack.visual_story.model_dump_json(indent=2), encoding="utf-8"
    )
    (show_dir / "show_seed.json").write_text(
        pack.show_seed.model_dump_json(indent=2), encoding="utf-8"
    )
    (show_dir / "cue_map.json").write_text(
        pack.cue_map.model_dump_json(indent=2), encoding="utf-8"
    )
    (show_dir / "show_pack.json").write_text(pack.model_dump_json(indent=2), encoding="utf-8")

    # Compact runtime export for Godot (no dense frame dump unless needed)
    runtime = {
        "show_id": pack.show_id,
        "mode": pack.mode,
        "bpm": pack.analysis.bpm,
        "duration_s": pack.analysis.duration_s,
        "key": pack.analysis.key_estimate,
        "seed": pack.show_seed.show_seed,
        "style": pack.show_seed.style,
        "artist": pack.show_seed.artist,
        "randomization": pack.show_seed.randomization,
        "sections": [s.model_dump() for s in pack.analysis.sections],
        "cues": [c.model_dump() for c in pack.cue_map.cues],
        "story": {
            "title": pack.visual_story.title,
            "central_subject": pack.visual_story.central_subject,
            "environment": pack.visual_story.environment,
            "color_palette": pack.visual_story.color_palette,
            "scenes": [s.model_dump() for s in pack.visual_story.scenes],
        },
        # Downsample frames for live scrubbing (~4 Hz already via stride)
        "frames": [f.model_dump() for f in pack.analysis.frames],
    }
    (show_dir / "runtime.json").write_text(json.dumps(runtime, indent=2), encoding="utf-8")
    return show_dir


def load_show_pack(show_dir: str | Path) -> ShowPack:
    path = Path(show_dir) / "show_pack.json"
    return ShowPack.model_validate_json(path.read_text(encoding="utf-8"))
