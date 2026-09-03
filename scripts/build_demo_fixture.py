"""Build a compact deterministic demo_runtime.json fixture for Godot + CI."""

from __future__ import annotations

import json
from pathlib import Path

from vbrain.analyzer import analyze_track
from vbrain.director import plan_show
from vbrain.runtime_contract import RuntimeExport, RuntimeStory
from vbrain.showpack import write_show_pack


def downsample_frames(frames: list, every: int = 24) -> list:
    if not frames:
        return []
    picked = frames[:: max(1, every)]
    if frames[-1] not in picked:
        picked = [*list(picked), frames[-1]]
    return picked


def build_runtime_dict(pack, *, frame_every: int = 24) -> dict:
    analysis = pack.analysis
    story = pack.visual_story
    frames = downsample_frames(analysis.frames, every=frame_every)
    runtime = RuntimeExport(
        show_id=pack.show_id,
        mode=pack.mode,
        bpm=analysis.bpm,
        duration_s=analysis.duration_s,
        key=analysis.key_estimate,
        seed=pack.show_seed.show_seed,
        style=pack.show_seed.style,
        artist=pack.show_seed.artist,
        randomization=pack.show_seed.randomization,
        sections=analysis.sections,
        cues=[c.model_dump() for c in pack.cue_map.cues],
        story=RuntimeStory(
            title=story.title,
            central_subject=story.central_subject,
            environment=story.environment,
            color_palette=story.color_palette,
            scenes=[s.model_dump() for s in story.scenes],
        ),
        frames=frames,
        hero_scene="valleytainment_logo",
    )
    return json.loads(runtime.model_dump_json())


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    demo_wav = root / "assets" / "demo" / "demo_drop.wav"
    if not demo_wav.exists():
        import runpy

        runpy.run_path(str(root / "scripts" / "make_demo_track.py"))

    analysis = analyze_track(demo_wav, frame_stride=8)
    pack = plan_show(analysis, seed=926183, show_id="_demo")
    write_show_pack(pack, root / "shows")

    runtime = build_runtime_dict(pack, frame_every=12)
    out_paths = [
        root / "tests" / "fixtures" / "demo_runtime.json",
        root / "apps" / "visual-engine" / "assets" / "fixtures" / "demo_runtime.json",
    ]
    text = json.dumps(runtime, indent=2)
    for out in out_paths:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"Wrote {out} ({out.stat().st_size} bytes, {len(runtime['frames'])} frames)")


if __name__ == "__main__":
    main()
