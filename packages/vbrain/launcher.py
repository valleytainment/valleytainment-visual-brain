"""One-command local show launcher."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def find_godot() -> str | None:
    candidates = [
        "/Applications/Godot.app/Contents/MacOS/Godot",
        "/usr/local/bin/godot",
        "godot",
    ]
    for c in candidates:
        p = Path(c) if c.startswith("/") else None
        if p and p.exists():
            return str(p)
        if c == "godot":
            from shutil import which

            found = which("godot")
            if found:
                return found
    return None


def launch_stack(
    *,
    open_browser: bool = True,
    open_godot: bool = True,
    live_source: str = "file",
    host: str = "127.0.0.1",
    port: int = 8765,
) -> int:
    """Start live brain, open control panel, optionally Godot. Blocks until Ctrl+C."""
    root = _repo_root()
    env = os.environ.copy()
    # Prefer installed console script; fall back to module invocation.
    vbrain_bin = Path(sys.executable).parent / "vbrain"
    if vbrain_bin.exists():
        live_cmd = [
            str(vbrain_bin),
            "live",
            "--source",
            live_source,
            "--host",
            host,
            "--port",
            str(port),
        ]
    else:
        live_cmd = [
            sys.executable,
            "-m",
            "vbrain",
            "live",
            "--source",
            live_source,
            "--host",
            host,
            "--port",
            str(port),
        ]
    procs: list[subprocess.Popen] = []
    live = subprocess.Popen(live_cmd, cwd=str(root), env=env)
    procs.append(live)

    # Wait for API
    import httpx

    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            r = httpx.get(f"http://{host}:{port}/api/health", timeout=1.0)
            if r.status_code == 200:
                break
        except httpx.HTTPError:
            time.sleep(0.25)

    if open_browser:
        webbrowser.open(f"http://{host}:{port}/")

    godot_bin = find_godot() if open_godot else None
    if godot_bin:
        project = root / "apps" / "visual-engine"
        godot = subprocess.Popen(
            [godot_bin, "--path", str(project), "--resolution", "1600x900"],
            cwd=str(root),
        )
        procs.append(godot)

    def _shutdown(*_args: object) -> None:
        for p in procs:
            if p.poll() is None:
                p.send_signal(signal.SIGTERM)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Keep launcher alive while live process runs
    return live.wait()
