#!/usr/bin/env python3
"""Bake a procedural cyber-cathedral world plate (no GPU / Comfy required)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


def bake(seed: int = 926183, width: int = 1600, height: int = 900) -> Image.Image:
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float64)
    x = (xx / width) * 2 - 1
    y = (yy / height) * 2 - 1
    r = np.sqrt(x * x + y * y) + 1e-5
    a = np.arctan2(y, x)

    tunnel = np.mod(1.1 / r + 0.35, 1.0)
    ribs = np.abs(np.sin(a * 8.0)) ** 6
    vignette = np.clip(1.2 - r, 0, 1)

    gold = np.stack([np.ones_like(r), 0.78 * np.ones_like(r), 0.28 * np.ones_like(r)], axis=-1)
    plasma = 0.5 + 0.5 * np.stack(
        [
            np.cos(tunnel * 6.28),
            np.cos(tunnel * 6.28 + 2.094),
            np.cos(tunnel * 6.28 + 4.188),
        ],
        axis=-1,
    )
    deep = np.array([0.02, 0.02, 0.06])
    band = 1.0 - np.abs(tunnel - 0.5) * 2
    img = deep + plasma * (0.35 + 0.45 * band[..., None])
    img = img * (0.45 + 0.55 * vignette[..., None])
    img = img + gold * ribs[..., None] * 0.22 * vignette[..., None]

    rng = np.random.default_rng(seed)
    stars = (rng.random((height, width)) > 0.997).astype(np.float64)
    img = np.clip(img + stars[..., None] * 0.7, 0, 1)
    return Image.fromarray((img * 255).astype(np.uint8), "RGB")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    img = bake()
    paths = [
        root / "assets" / "worlds" / "cyber_cathedral_plate.png",
        root / "apps" / "visual-engine" / "assets" / "textures" / "cyber_cathedral_plate.png",
    ]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path)
        print(f"Wrote {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
