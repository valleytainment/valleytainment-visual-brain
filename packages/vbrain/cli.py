"""CLI: analyze tracks and compile Valleytainment show packs."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.table import Table

from vbrain.analyzer import analyze_track
from vbrain.director import plan_show
from vbrain.showpack import write_show_pack

app = typer.Typer(
    name="vbrain",
    help="Valleytainment Visual Brain — AI visual performance instrument",
    add_completion=False,
)


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
    show_id: Optional[str] = typer.Option(None, help="Override show id"),
) -> None:
    """Analyze a track and write a prepared show pack."""
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
