"""ComfyUI HTTP API client with queue + history fetch."""

from __future__ import annotations

import json
import shutil
import time
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

    def list_checkpoints(self) -> list[str]:
        with httpx.Client(timeout=self.timeout) as client:
            r = client.get(f"{self.base_url}/models/checkpoints")
            r.raise_for_status()
            data = r.json()
            return list(data) if isinstance(data, list) else []

    def queue_prompt(self, workflow: dict[str, Any]) -> dict[str, Any]:
        payload = {"prompt": workflow, "client_id": self.client_id}
        with httpx.Client(timeout=max(self.timeout, 60.0)) as client:
            r = client.post(f"{self.base_url}/prompt", json=payload)
            r.raise_for_status()
            return r.json()

    def history(self, prompt_id: str | None = None) -> dict[str, Any]:
        url = f"{self.base_url}/history"
        if prompt_id:
            url = f"{url}/{prompt_id}"
        with httpx.Client(timeout=self.timeout) as client:
            r = client.get(url)
            r.raise_for_status()
            return r.json()

    def view_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        with httpx.Client(timeout=max(self.timeout, 60.0)) as client:
            r = client.get(f"{self.base_url}/view", params=params)
            r.raise_for_status()
            return r.content

    def wait_for_prompt(
        self, prompt_id: str, timeout_s: float = 600.0, poll_s: float = 2.0
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            hist = self.history(prompt_id)
            if prompt_id in hist:
                return hist[prompt_id]
            time.sleep(poll_s)
        raise TimeoutError(f"ComfyUI prompt {prompt_id} timed out after {timeout_s}s")

    def collect_output_images(self, history_entry: dict[str, Any]) -> list[dict[str, str]]:
        images: list[dict[str, str]] = []
        outputs = history_entry.get("outputs", {})
        for node in outputs.values():
            for img in node.get("images", []):
                images.append(
                    {
                        "filename": img["filename"],
                        "subfolder": img.get("subfolder", ""),
                        "type": img.get("type", "output"),
                    }
                )
        return images

    def run_and_save(
        self,
        workflow: dict[str, Any],
        dest_dir: str | Path,
        *,
        timeout_s: float = 900.0,
        prefix: str = "world",
    ) -> list[Path]:
        dest = Path(dest_dir)
        dest.mkdir(parents=True, exist_ok=True)
        queued = self.queue_prompt(workflow)
        prompt_id = queued["prompt_id"]
        entry = self.wait_for_prompt(prompt_id, timeout_s=timeout_s)
        saved: list[Path] = []
        for i, meta in enumerate(self.collect_output_images(entry)):
            raw = self.view_image(meta["filename"], meta["subfolder"], meta["type"])
            out = dest / f"{prefix}_{i:02d}_{meta['filename']}"
            out.write_bytes(raw)
            saved.append(out)
        return saved

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
                report["checkpoints"] = self.list_checkpoints()
            except httpx.HTTPError as exc:
                report["error"] = str(exc)
        return report


def ingest_world_plate(src: Path, assets_worlds: Path, godot_textures: Path) -> Path:
    """Copy a generated plate into assets + Godot textures folder."""
    assets_worlds.mkdir(parents=True, exist_ok=True)
    godot_textures.mkdir(parents=True, exist_ok=True)
    dest = assets_worlds / "cyber_cathedral_plate.png"
    shutil.copy2(src, dest)
    shutil.copy2(src, godot_textures / "cyber_cathedral_plate.png")
    return dest
