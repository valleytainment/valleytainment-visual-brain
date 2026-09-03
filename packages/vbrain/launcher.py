"""One-command local show launcher with fail-fast process supervision."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from shutil import which

import httpx


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def find_godot() -> str | None:
    """Find a Godot editor binary without tying the project to one OS."""
    override = os.environ.get("GODOT_BIN")
    if override:
        path = Path(override).expanduser()
        if path.exists():
            return str(path)

    absolute_candidates = [
        "/Applications/Godot.app/Contents/MacOS/Godot",
        "/usr/local/bin/godot",
        "/usr/bin/godot",
    ]
    for candidate in absolute_candidates:
        if Path(candidate).exists():
            return candidate

    for command in ("godot4", "godot", "godot.exe"):
        found = which(command)
        if found:
            return found
    return None


def _terminate_processes(procs: list[subprocess.Popen], grace_s: float = 3.0) -> None:
    """Terminate the stack, then kill only processes that ignore the grace period."""
    for process in procs:
        if process.poll() is None:
            try:
                process.send_signal(signal.SIGTERM)
            except OSError:
                pass

    deadline = time.monotonic() + grace_s
    for process in procs:
        if process.poll() is not None:
            continue
        remaining = max(0.0, deadline - time.monotonic())
        try:
            process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except OSError:
                pass


def _wait_for_health(
    url: str,
    process: subprocess.Popen,
    timeout_s: float = 15.0,
) -> tuple[bool, str]:
    deadline = time.monotonic() + timeout_s
    last_error = "performance API did not answer"
    while time.monotonic() < deadline:
        exit_code = process.poll()
        if exit_code is not None:
            return False, f"live brain exited before health check (code {exit_code})"
        try:
            response = httpx.get(url, timeout=1.0)
            if response.status_code == 200:
                payload = response.json()
                if payload.get("ok") is True:
                    return True, "ok"
            last_error = f"health returned HTTP {response.status_code}"
        except (httpx.HTTPError, ValueError) as exc:
            last_error = str(exc)
        time.sleep(0.25)
    return False, last_error


def launch_stack(
    *,
    open_browser: bool = True,
    open_godot: bool = True,
    live_source: str = "file",
    host: str = "127.0.0.1",
    port: int = 8765,
) -> int:
    """Start and supervise live brain, control panel, and optional Godot runtime."""
    root = _repo_root()
    env = os.environ.copy()
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

    health_url = f"http://{host}:{port}/api/health"
    healthy, detail = _wait_for_health(health_url, live)
    if not healthy:
        print(f"[vbrain] startup failed: {detail}", file=sys.stderr)
        _terminate_processes(procs)
        code = live.poll()
        return code if code not in (None, 0) else 2

    if open_browser:
        webbrowser.open(f"http://{host}:{port}/")

    godot: subprocess.Popen | None = None
    godot_bin = find_godot() if open_godot else None
    if open_godot and not godot_bin:
        print(
            "[vbrain] Godot not found; live brain and control panel are running. "
            "Set GODOT_BIN or install Godot 4.6+ to launch the renderer automatically.",
            file=sys.stderr,
        )
    elif godot_bin:
        project = root / "apps" / "visual-engine"
        godot = subprocess.Popen([godot_bin, "--path", str(project)], cwd=str(root), env=env)
        procs.append(godot)

    def _shutdown(*_args: object) -> None:
        _terminate_processes(procs)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        while True:
            live_code = live.poll()
            if live_code is not None:
                if godot and godot.poll() is None:
                    print(
                        f"[vbrain] live brain exited unexpectedly (code {live_code}); "
                        "stopping renderer",
                        file=sys.stderr,
                    )
                _terminate_processes(procs)
                return int(live_code)

            if godot is not None:
                godot_code = godot.poll()
                if godot_code is not None:
                    print(
                        f"[vbrain] Godot exited unexpectedly (code {godot_code}); "
                        "stopping live brain",
                        file=sys.stderr,
                    )
                    _terminate_processes(procs)
                    return int(godot_code) if godot_code != 0 else 3

            time.sleep(0.25)
    finally:
        _terminate_processes(procs)
