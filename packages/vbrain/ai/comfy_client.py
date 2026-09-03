"""ComfyUI HTTP API client (optional — no-op when server offline)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import httpx


class ComfyUIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8188", timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client_id = str(uuid.uuid4())

    def available(self) -> bool:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.get(f"{self.base_url}/system_stats")
                return r.status_code == 200
        except httpx.HTTPError:
            return False

    def system_stats(self) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            r = client.get(f"{self.base_url}/system_stats")
            r.raise_for_status()
            return r.json()

    def queue_prompt(self, workflow: dict[str, Any]) -> dict[str, Any]:
        payload = {"prompt": workflow, "client_id": self.client_id}
        with httpx.Client(timeout=max(self.timeout, 60.0)) as client:
            r = client.post(f"{self.base_url}/prompt", json=payload)
            r.raise_for_status()
            return r.json()

    def load_workflow(self, path: str | Path) -> dict[str, Any]:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if "prompt" in data and isinstance(data["prompt"], dict):
            return data["prompt"]
        return data

    def status_report(self) -> dict[str, Any]:
        ok = self.available()
        report: dict[str, Any] = {
            "base_url": self.base_url,
            "online": ok,
            "client_id": self.client_id,
        }
        if ok:
            try:
                report["system_stats"] = self.system_stats()
            except httpx.HTTPError as exc:
                report["error"] = str(exc)
        return report
