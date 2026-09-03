"""Persist / load show packs for the Godot performance engine."""

from __future__ import annotations

from pathlib import Path

from vbrain.runtime_contract import RuntimeExport, RuntimeStory
from vbrain.schemas import ShowPack


def build_runtime_export(pack: ShowPack, *, frame_every: int = 1) -> RuntimeExport:
    frames = pack.analysis.frames
    if frame_every > 1 and frames:
        frames = frames[::frame_every]
        if pack.analysis.frames[-1] not in frames:
            frames = [*list(frames), pack.analysis.frames[-1]]
    return RuntimeExport(
        show_id=pack.show_id,
        mode=pack.mode,
        bpm=pack.analysis.bpm,
        duration_s=pack.analysis.duration_s,
        key=pack.analysis.key_estimate,
        seed=pack.show_seed.show_seed,
        style=pack.show_seed.style,
        artist=pack.show_seed.artist,
        randomization=pack.show_seed.randomization,
        sections=pack.analysis.sections,
        cues=[c.model_dump() for c in pack.cue_map.cues],
        story=RuntimeStory(
            title=pack.visual_story.title,
            central_subject=pack.visual_story.central_subject,
            environment=pack.visual_story.environment,
            color_palette=pack.visual_story.color_palette,
            scenes=[s.model_dump() for s in pack.visual_story.scenes],
        ),
        frames=frames,
        hero_scene="valleytainment_logo",
    )


def write_show_pack(
    pack: ShowPack,
    shows_root: str | Path,
    *,
    frame_every: int = 1,
) -> Path:
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
    (show_dir / "cue_map.json").write_text(pack.cue_map.model_dump_json(indent=2), encoding="utf-8")
    (show_dir / "show_pack.json").write_text(pack.model_dump_json(indent=2), encoding="utf-8")

    runtime = build_runtime_export(pack, frame_every=frame_every)
    (show_dir / "runtime.json").write_text(runtime.model_dump_json(indent=2), encoding="utf-8")
    return show_dir


def load_show_pack(show_dir: str | Path) -> ShowPack:
    path = Path(show_dir) / "show_pack.json"
    return ShowPack.model_validate_json(path.read_text(encoding="utf-8"))


def load_runtime(path: str | Path) -> RuntimeExport:
    return RuntimeExport.model_validate_json(Path(path).read_text(encoding="utf-8"))
