"""Asset library manifest + provenance for AI-generated worlds."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class AssetRecord(BaseModel):
    asset_id: str
    kind: str  # image | video | depth | texture | loop
    path: str
    prompt: str = ""
    model: str = ""
    seed: int | None = None
    workflow: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    tags: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class AssetManifest(BaseModel):
    version: int = 1
    library_root: str
    assets: list[AssetRecord] = Field(default_factory=list)

    def add(self, record: AssetRecord) -> None:
        self.assets = [a for a in self.assets if a.asset_id != record.asset_id]
        self.assets.append(record)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> AssetManifest:
        return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))

    @classmethod
    def load_or_create(cls, path: str | Path, library_root: str | Path) -> AssetManifest:
        p = Path(path)
        if p.exists():
            return cls.load(p)
        manifest = cls(library_root=str(library_root))
        p.parent.mkdir(parents=True, exist_ok=True)
        manifest.save(p)
        return manifest


def register_placeholder_hero(manifest_path: Path, logo_path: Path) -> AssetManifest:
    """Ensure the Valleytainment logo is the first canonical asset."""
    root = logo_path.parent.parent
    manifest = AssetManifest.load_or_create(manifest_path, root)
    manifest.add(
        AssetRecord(
            asset_id="valleytainment_logo",
            kind="image",
            path=str(logo_path),
            prompt="Valleytainment brand monster logo — canonical hero",
            model="brand-artwork",
            tags=["hero", "logo", "brand"],
            meta={"role": "canonical_hero_scene"},
        )
    )
    manifest.save(manifest_path)
    return manifest


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
