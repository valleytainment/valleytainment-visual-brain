"""Local performance server: live state API + control panel."""

from __future__ import annotations

import json
import re
import threading
import time
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

MAX_BODY_BYTES = 32 * 1024
ALLOWED_MODES = {"PREPARED", "LIVE", "HYBRID"}
ALLOWED_CUES = {
    "tick",
    "trigger_drop",
    "trigger_pre_drop",
    "trigger_silence",
    "trigger_shockwave",
}
STYLE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,79}$")
RESOLUTION_RE = re.compile(r"^(\d{2,5})x(\d{2,5})$")
CONTROL_KEYS = {
    "playing",
    "mode",
    "resolution",
    "seed",
    "style",
    "intensity_bias",
    "blackout",
}


def validate_control_patch(patch: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize performer controls before mutating live state."""
    if not isinstance(patch, dict):
        raise ValueError("controls payload must be an object")
    unknown = sorted(set(patch) - CONTROL_KEYS)
    if unknown:
        raise ValueError(f"unsupported control fields: {', '.join(unknown)}")

    clean: dict[str, Any] = {}
    for key, value in patch.items():
        if key in {"playing", "blackout"}:
            if not isinstance(value, bool):
                raise ValueError(f"{key} must be boolean")
            clean[key] = value
        elif key == "mode":
            if not isinstance(value, str) or value.upper() not in ALLOWED_MODES:
                raise ValueError(f"mode must be one of {sorted(ALLOWED_MODES)}")
            clean[key] = value.upper()
        elif key == "resolution":
            if not isinstance(value, str):
                raise ValueError("resolution must be WIDTHxHEIGHT")
            match = RESOLUTION_RE.fullmatch(value)
            if not match:
                raise ValueError("resolution must be WIDTHxHEIGHT")
            width, height = (int(match.group(1)), int(match.group(2)))
            if not 320 <= width <= 8192 or not 240 <= height <= 8192:
                raise ValueError("resolution is outside the supported stage range")
            clean[key] = f"{width}x{height}"
        elif key == "seed":
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError("seed must be an integer")
            if not 0 <= value <= 2_147_483_647:
                raise ValueError("seed must be between 0 and 2147483647")
            clean[key] = value
        elif key == "style":
            if not isinstance(value, str) or not STYLE_RE.fullmatch(value):
                raise ValueError("style must be a safe preset identifier")
            clean[key] = value
        elif key == "intensity_bias":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("intensity_bias must be numeric")
            numeric = float(value)
            if not -1.0 <= numeric <= 1.0:
                raise ValueError("intensity_bias must be between -1 and 1")
            clean[key] = numeric
    return clean


class PerformanceState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.live: dict[str, Any] = {
            "section": "INTRO",
            "intensity": 0.15,
            "kick_energy": 0.0,
            "bass_energy": 0.0,
            "snare_energy": 0.0,
            "hat_energy": 0.0,
            "drop_probability": 0.0,
            "spectral_brightness": 0.2,
            "bpm": 128.0,
            "action": "tick",
            "hero_scene": "valleytainment_logo",
            "seed": 926183,
            "style": "biomechanical_cyber_cathedral",
        }
        self.controls: dict[str, Any] = {
            "playing": True,
            "mode": "LIVE",
            "resolution": "1920x1080",
            "seed": 926183,
            "style": "biomechanical_cyber_cathedral",
            "intensity_bias": 0.0,
            "blackout": False,
        }

    def update_live(self, data: dict[str, Any]) -> None:
        with self.lock:
            self.live = {**self.live, **data}

    def get_snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {"live": dict(self.live), "controls": dict(self.controls)}

    def patch_controls(self, patch: dict[str, Any]) -> dict[str, Any]:
        clean = validate_control_patch(patch)
        with self.lock:
            self.controls.update(clean)
            return dict(self.controls)


def make_handler(
    state: PerformanceState,
    panel_html: str,
    on_control: Callable[[dict[str, Any]], None] | None = None,
) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            return

        def _json(self, code: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _html(self, body: str) -> None:
            data = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path in {"/", "/panel"}:
                self._html(panel_html)
                return
            if path == "/api/state":
                self._json(200, state.get_snapshot())
                return
            if path == "/api/live":
                snap = state.get_snapshot()
                self._json(200, snap["live"])
                return
            if path == "/api/health":
                self._json(200, {"ok": True, "service": "vbrain-performance"})
                return
            self._json(404, {"error": "not found"})

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._json(400, {"error": "invalid content length"})
                return
            if length < 0 or length > MAX_BODY_BYTES:
                self._json(413, {"error": "request body too large"})
                return

            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._json(400, {"error": "invalid json"})
                return
            if not isinstance(payload, dict):
                self._json(400, {"error": "json body must be an object"})
                return

            if path == "/api/controls":
                try:
                    controls = state.patch_controls(payload)
                except ValueError as exc:
                    self._json(400, {"error": str(exc)})
                    return
                if on_control:
                    on_control(controls)
                self._json(200, {"controls": controls})
                return

            if path == "/api/cue":
                if set(payload) - {"action"}:
                    self._json(400, {"error": "cue accepts only the action field"})
                    return
                action = payload.get("action", "tick")
                if not isinstance(action, str) or action not in ALLOWED_CUES:
                    self._json(400, {"error": "unsupported cue action"})
                    return
                state.update_live({"action": action})
                self._json(200, {"ok": True, "action": action})
                return

            self._json(404, {"error": "not found"})

    return Handler


def load_panel_html() -> str:
    candidates = [
        Path(__file__).resolve().parents[3] / "apps" / "control-panel" / "index.html",
        Path.cwd() / "apps" / "control-panel" / "index.html",
    ]
    for path in candidates:
        if path.exists():
            return path.read_text(encoding="utf-8")
    return "<html><body><h1>Valleytainment Visual Brain</h1><p>Panel missing.</p></body></html>"


def run_server(
    state: PerformanceState,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> ThreadingHTTPServer:
    handler = make_handler(state, load_panel_html())
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def write_live_sidecar(path: Path, live: dict[str, Any]) -> None:
    """Atomically publish a live-state sidecar so readers never see partial JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(live, separators=(",", ":")), encoding="utf-8")
    temp.replace(path)


def sleep_chunk(seconds: float) -> None:
    time.sleep(seconds)
