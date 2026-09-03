"""Local performance server: live state API + control panel."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


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
        with self.lock:
            self.controls.update(patch)
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
            body = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _html(self, body: str) -> None:
            data = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

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
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self._json(400, {"error": "invalid json"})
                return
            if path == "/api/controls":
                controls = state.patch_controls(payload)
                if on_control:
                    on_control(controls)
                self._json(200, {"controls": controls})
                return
            if path == "/api/cue":
                # Immediate cue injection into live state
                state.update_live({"action": str(payload.get("action", "tick")), **payload})
                self._json(200, {"ok": True})
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
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def write_live_sidecar(path: Path, live: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(live), encoding="utf-8")


def sleep_chunk(seconds: float) -> None:
    time.sleep(seconds)
