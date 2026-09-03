"""CLI: Valleytainment Visual Brain — analyze, live, factory, performance."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich import print as rprint
from rich.table import Table

app = typer.Typer(
    name="vbrain",
    help="Valleytainment Visual Brain — AI visual performance instrument",
    add_completion=False,
    no_args_is_help=True,
)
factory_app = typer.Typer(help="AI factory (ComfyUI / GPU routing)")
app.add_typer(factory_app, name="factory")


@app.command()
def analyze(
    track: Path = typer.Argument(..., exists=True, readable=True, help="Audio file (wav/mp3/flac)"),
    out: Path = typer.Option(Path("shows"), help="Shows root directory"),
    style: str = typer.Option("biomechanical_cyber_cathedral", help="Visual style preset"),
    seed: int = typer.Option(926183, help="Show seed for controlled randomization"),
    artist: str = typer.Option("Valleytainment", help="Artist name"),
    ollama: bool = typer.Option(False, "--ollama", help="Use local Ollama/Qwen director"),
    ollama_model: str = typer.Option("qwen3:8b", help="Ollama model tag"),
    stems: bool = typer.Option(False, "--stems", help="Run Demucs stem separation if installed"),
    show_id: str | None = typer.Option(None, help="Override show id"),
) -> None:
    """Analyze a track and write a prepared show pack."""
    from vbrain.analyzer import analyze_track
    from vbrain.director import plan_show
    from vbrain.showpack import write_show_pack

    rprint(f"[bold]Analyzing[/bold] {track}")
    analysis = analyze_track(track, separate=stems)
    pack = plan_show(
        analysis,
        style=style,
        seed=seed,
        artist=artist,
        use_ollama=ollama,
        ollama_model=ollama_model,
        show_id=show_id,
        mode="PREPARED",
    )
    show_dir = write_show_pack(pack, out)
    _print_summary(pack)
    rprint(f"\n[green]Show pack written →[/green] {show_dir}")
    rprint(f"Godot runtime file: [cyan]{show_dir / 'runtime.json'}[/cyan]")


@app.command("list-styles")
def list_styles() -> None:
    """List built-in visual style presets."""
    from vbrain.director.ollama_director import STYLE_PRESETS

    for name, preset in STYLE_PRESETS.items():
        rprint(f"[bold]{name}[/bold]")
        rprint(f"  env: {preset['environment']}")
        rprint(f"  subject: {preset['subject']}")


@app.command()
def status() -> None:
    """Show GPU tier, ComfyUI reachability, and output presets."""
    from vbrain.ai import ComfyUIClient, detect_gpu
    from vbrain.performance.presets import OUTPUT_PRESETS

    gpu = detect_gpu()
    comfy = ComfyUIClient().status_report()
    rprint(f"[bold]GPU[/bold] {gpu.tier.value} · {gpu.backend} · {gpu.device_name}")
    if gpu.vram_gb is not None:
        rprint(f"  VRAM ≈ {gpu.vram_gb:.1f} GB")
    rprint(f"  models: {', '.join(gpu.recommended_models)}")
    rprint(f"  note: {gpu.notes}")
    rprint(
        f"[bold]ComfyUI[/bold] {'online' if comfy['online'] else 'offline'} @ {comfy['base_url']}"
    )
    rprint("[bold]Outputs[/bold]")
    for p in OUTPUT_PRESETS:
        rprint(f"  {p.id}: {p.width}x{p.height} — {p.label}")


@app.command()
def live(
    source: str = typer.Option("file", help="file | mic"),
    track: Path | None = typer.Option(None, help="WAV for file source (default: demo)"),
    host: str = typer.Option("127.0.0.1", help="Performance API host"),
    port: int = typer.Option(8765, help="Performance API port"),
    seed: int = typer.Option(926183, help="Show seed"),
    style: str = typer.Option("biomechanical_cyber_cathedral", help="Style preset"),
    seconds: float = typer.Option(0.0, help="Stop after N seconds (0 = forever)"),
    sidecar: Path = typer.Option(
        Path("shows/_live/live_state.json"),
        help="JSON sidecar for Godot / tools",
    ),
) -> None:
    """Run live brain + control panel API (Mode B)."""
    from time import monotonic

    from vbrain.live import FileAudioSource, LiveBrain, MicAudioSource
    from vbrain.paths import ensure_demo_wav
    from vbrain.performance import PerformanceState, run_server, sleep_chunk, write_live_sidecar

    if source == "file":
        path = track or ensure_demo_wav()
        audio = FileAudioSource(path)
        rprint(f"[bold]LIVE[/bold] file source → {path}")
    elif source == "mic":
        audio = MicAudioSource()
        rprint("[bold]LIVE[/bold] microphone source")
    else:
        raise typer.BadParameter("source must be file or mic")

    brain = LiveBrain(sr=audio.sr, seed=seed, style=style)
    state = PerformanceState()
    state.patch_controls({"mode": "LIVE", "seed": seed, "style": style})
    server = run_server(state, host=host, port=port)
    rprint(f"Control panel → [cyan]http://{host}:{port}/[/cyan]")
    rprint(f"Live JSON     → [cyan]http://{host}:{port}/api/live[/cyan]")
    rprint(f"Sidecar       → [cyan]{sidecar}[/cyan]")

    start = monotonic()
    try:
        while True:
            chunk = audio.read()
            live_state = brain.process(chunk)
            # Honor control-panel blackout / seed / style
            snap = state.get_snapshot()["controls"]
            payload = live_state.as_dict()
            payload["seed"] = snap.get("seed", seed)
            payload["style"] = snap.get("style", style)
            if snap.get("blackout"):
                payload["intensity"] = 0.0
                payload["section"] = "SILENCE"
                payload["action"] = "trigger_silence"
            bias = float(snap.get("intensity_bias", 0.0))
            payload["intensity"] = max(0.0, min(1.0, float(payload["intensity"]) + bias))
            state.update_live(payload)
            write_live_sidecar(sidecar, payload)
            sleep_chunk(0.05)
            if seconds > 0 and (monotonic() - start) >= seconds:
                break
    except KeyboardInterrupt:
        rprint("\n[yellow]Live stopped[/yellow]")
    finally:
        server.shutdown()


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8765),
) -> None:
    """Serve control panel only (no audio loop)."""
    from vbrain.performance import PerformanceState, run_server

    state = PerformanceState()
    run_server(state, host=host, port=port)
    rprint(f"Control panel → [cyan]http://{host}:{port}/[/cyan]")
    rprint("Press Ctrl+C to stop")
    try:
        while True:
            from vbrain.performance import sleep_chunk

            sleep_chunk(1.0)
    except KeyboardInterrupt:
        rprint("stopped")


@app.command()
def launch(
    source: str = typer.Option("file", help="file | mic"),
    no_godot: bool = typer.Option(False, "--no-godot", help="Skip opening Godot"),
    no_browser: bool = typer.Option(False, "--no-browser", help="Skip opening panel"),
    port: int = typer.Option(8765),
) -> None:
    """One-command show: live brain + control panel + Godot."""
    from vbrain.launcher import launch_stack

    rprint("[bold]Launching Valleytainment Visual Brain stack…[/bold]")
    raise SystemExit(
        launch_stack(
            open_browser=not no_browser,
            open_godot=not no_godot,
            live_source=source,
            port=port,
        )
    )


@factory_app.command("status")
def factory_status(
    comfy_url: str = typer.Option("http://127.0.0.1:8188", help="ComfyUI base URL"),
) -> None:
    """GPU routing + ComfyUI connectivity."""
    from vbrain.ai import ComfyUIClient, detect_gpu, route_job

    gpu = detect_gpu()
    client = ComfyUIClient(comfy_url)
    report = client.status_report()
    rprint(f"tier=[bold]{gpu.tier.value}[/bold] backend={gpu.backend} device={gpu.device_name}")
    for job in ("flux", "wan", "depth", "image"):
        rprint(f"  route {job} → {route_job(job, gpu)}")
    rprint(json.dumps(report, indent=2)[:1200])


@factory_app.command("init-manifest")
def factory_init_manifest(
    out: Path = typer.Option(Path("assets/manifest.json"), help="Manifest path"),
) -> None:
    """Register the Valleytainment logo as the canonical hero asset."""
    from vbrain.ai import register_placeholder_hero

    logo = Path("apps/visual-engine/assets/brand/valleytainment_logo.png")
    manifest = register_placeholder_hero(out, logo)
    rprint(f"[green]Manifest[/green] {out} · {len(manifest.assets)} assets")


@factory_app.command("queue")
def factory_queue(
    workflow: Path = typer.Argument(
        Path("ai/comfyui/workflows/sd15_cyber_cathedral.json"),
        exists=True,
        readable=True,
    ),
    comfy_url: str = typer.Option("http://127.0.0.1:8188"),
    dry_run: bool = typer.Option(True, help="Do not submit if Comfy offline / dry-run"),
) -> None:
    """Queue a ComfyUI workflow (dry-run by default when offline)."""
    from vbrain.ai import ComfyUIClient, detect_gpu, route_job

    gpu = detect_gpu()
    route = route_job("image", gpu)
    rprint(f"GPU route → [bold]{route}[/bold]")
    client = ComfyUIClient(comfy_url)
    graph = client.load_workflow(workflow)
    if dry_run or not client.available():
        rprint(
            f"[yellow]Dry-run[/yellow] would queue {workflow.name} "
            f"({len(graph)} nodes). Start ComfyUI and pass --no-dry-run to submit."
        )
        return
    result = client.queue_prompt(graph)
    rprint(result)


@factory_app.command("generate-world")
def factory_generate_world(
    workflow: Path = typer.Option(
        Path("ai/comfyui/workflows/sd15_cyber_cathedral.json"),
        exists=True,
        readable=True,
    ),
    comfy_url: str = typer.Option("http://127.0.0.1:8188"),
    timeout: float = typer.Option(900.0, help="Seconds to wait for CPU/GPU render"),
    procedural: bool = typer.Option(
        False, "--procedural", help="Skip Comfy and bake a procedural plate"
    ),
) -> None:
    """Generate a cyber-cathedral world plate and install it into Godot textures."""
    import runpy

    from vbrain.ai import AssetRecord, ComfyUIClient, register_placeholder_hero
    from vbrain.ai.asset_manifest import AssetManifest
    from vbrain.ai.comfy_client import ingest_world_plate

    plate: Path | None = None
    model_name = "procedural"

    client = ComfyUIClient(comfy_url)
    if not procedural and client.available():
        ckpts = client.list_checkpoints()
        rprint(f"Checkpoints: {ckpts or '(none)'}")
        graph = client.load_workflow(workflow)
        rprint(f"[bold]Generating[/bold] via {workflow.name}…")
        try:
            saved = client.run_and_save(
                graph, Path("assets/worlds/raw"), timeout_s=timeout, prefix="cathedral"
            )
            if saved:
                plate = ingest_world_plate(
                    saved[0],
                    Path("assets/worlds"),
                    Path("apps/visual-engine/assets/textures"),
                )
                model_name = ckpts[0] if ckpts else "comfy"
            else:
                rprint("[yellow]Comfy returned no images[/yellow]; baking procedural plate")
        except Exception as exc:
            rprint(f"[yellow]ComfyUI failed[/yellow] ({exc}); baking procedural plate")

    if plate is None:
        runpy.run_path(str(Path("scripts/bake_world_plate.py")), run_name="__main__")
        plate = Path("assets/worlds/cyber_cathedral_plate.png")

    register_placeholder_hero(
        Path("assets/manifest.json"),
        Path("apps/visual-engine/assets/brand/valleytainment_logo.png"),
    )
    manifest = AssetManifest.load(Path("assets/manifest.json"))
    manifest.add(
        AssetRecord(
            asset_id="cyber_cathedral_plate",
            kind="image",
            path=str(plate),
            prompt="cyber cathedral festival LED backdrop",
            model=model_name,
            workflow=(
                str(workflow) if model_name != "procedural" else "scripts/bake_world_plate.py"
            ),
            tags=["world", "backdrop", "ai-factory"],
        )
    )
    manifest.save(Path("assets/manifest.json"))
    rprint(f"[green]World plate installed →[/green] {plate}")
    rprint("Press R in Godot to reload the hero texture.")


def _print_summary(pack) -> None:
    a = pack.analysis
    rprint(
        f"BPM [bold]{a.bpm}[/bold] · key [bold]{a.key_estimate}[/bold] · "
        f"{a.duration_s:.1f}s · {a.beat_count} beats · {a.bar_count} bars"
    )
    table = Table(title="Sections")
    table.add_column("Section")
    table.add_column("Bars", justify="right")
    table.add_column("Time")
    table.add_column("Intensity", justify="right")
    table.add_column("Band")
    for s in a.sections:
        table.add_row(
            s.label.value,
            str(s.duration_bars),
            f"{s.start_t:.1f}–{s.end_t:.1f}s",
            f"{s.intensity:.2f}",
            s.intensity_band.value,
        )
    rprint(table)
    rprint(f"Story: [bold]{pack.visual_story.title}[/bold]")
    rprint(f"Subject: {pack.visual_story.central_subject}")
    rprint(f"Cues: {len(pack.cue_map.cues)}")


if __name__ == "__main__":
    app()
