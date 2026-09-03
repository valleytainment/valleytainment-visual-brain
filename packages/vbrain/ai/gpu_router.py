"""GPU capability detection and AI model routing."""

from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum


class GpuTier(str, Enum):
    HIGH = "high"
    LOW = "low"
    NONE = "none"


@dataclass(frozen=True)
class GpuProfile:
    tier: GpuTier
    backend: str
    device_name: str
    vram_gb: float | None
    recommended_models: tuple[str, ...]
    notes: str = ""


HIGH_MODELS = ("wan2.2", "hunyuanvideo-1.5", "flux.1-schnell", "qwen-image")
LOW_MODELS = ("framepack", "ltx", "flux.1-schnell")
NONE_MODELS = ("prebuilt-assets-only",)


def _nvidia_smi() -> tuple[str | None, float | None]:
    if not shutil.which("nvidia-smi"):
        return None, None
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=5,
        ).strip()
    except (subprocess.SubprocessError, OSError):
        return None, None
    if not out:
        return None, None
    line = out.splitlines()[0]
    parts = [p.strip() for p in line.split(",")]
    name = parts[0] if parts else "NVIDIA"
    vram = None
    if len(parts) > 1:
        try:
            vram = float(parts[1]) / 1024.0
        except ValueError:
            vram = None
    return name, vram


def detect_gpu() -> GpuProfile:
    name, vram = _nvidia_smi()
    if name:
        if vram is not None and vram >= 14:
            return GpuProfile(
                tier=GpuTier.HIGH,
                backend="cuda",
                device_name=name,
                vram_gb=vram,
                recommended_models=HIGH_MODELS,
                notes="Full Wan/Hunyuan/FLUX factory available",
            )
        return GpuProfile(
            tier=GpuTier.LOW,
            backend="cuda",
            device_name=name,
            vram_gb=vram,
            recommended_models=LOW_MODELS,
            notes="Prefer FramePack/LTX; offload heavy jobs to Kaggle/Colab",
        )

    if platform.system() == "Darwin" and platform.machine() == "arm64":
        return GpuProfile(
            tier=GpuTier.LOW,
            backend="metal",
            device_name="Apple Silicon",
            vram_gb=None,
            recommended_models=("flux.1-schnell", "qwen-image", "prebuilt-assets-only"),
            notes="Use ComfyUI Metal builds for stills; video gen optional/remote",
        )

    return GpuProfile(
        tier=GpuTier.NONE,
        backend="cpu",
        device_name="CPU only",
        vram_gb=None,
        recommended_models=NONE_MODELS,
        notes="Performance machine mode — run Godot from prebuilt show packs",
    )


def route_job(job: str, profile: GpuProfile | None = None) -> str:
    profile = profile or detect_gpu()
    job = job.lower()
    if profile.tier == GpuTier.NONE:
        return "skip-use-prebuilt"
    if job in {"wan", "hunyuan", "i2v", "t2v"} and profile.tier != GpuTier.HIGH:
        return "remote-or-framepack"
    if job in {"flux", "qwen-image", "depth", "image"}:
        return "local-comfyui" if profile.tier != GpuTier.NONE else "skip-use-prebuilt"
    return "local-comfyui" if profile.tier != GpuTier.NONE else "skip-use-prebuilt"
