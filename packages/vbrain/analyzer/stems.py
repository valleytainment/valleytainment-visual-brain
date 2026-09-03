"""Optional Demucs stem separation (requires optional [stems] extra)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def separate_stems(track_path: Path, out_dir: Path) -> dict[str, str]:
    """Run Demucs if installed; otherwise return empty dict."""
    if shutil.which("demucs") is None:
        try:
            import demucs  # noqa: F401
        except ImportError:
            return {}

    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "python3",
        "-m",
        "demucs",
        "--two-stems=vocals",
        "-o",
        str(out_dir),
        str(track_path),
    ]
    # Prefer 4-stem default when available
    cmd = ["python3", "-m", "demucs", "-o", str(out_dir), str(track_path)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {}

    # Demucs writes to out_dir/htdemucs/<trackname>/
    candidates = list(out_dir.rglob("*.wav"))
    stems: dict[str, str] = {}
    for wav in candidates:
        name = wav.stem.lower()
        if name in {"vocals", "drums", "bass", "other", "no_vocals"}:
            stems[name] = str(wav)
    return stems
