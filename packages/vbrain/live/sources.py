"""Audio sources for live brain: file playback simulator + optional mic."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf


class FileAudioSource:
    """Stream a WAV as if it were live input (for rehearsals / no-mic machines)."""

    def __init__(
        self,
        path: str | Path,
        sr: int = 44100,
        chunk_s: float = 0.05,
    ) -> None:
        y, file_sr = sf.read(str(path), always_2d=True)
        y = np.mean(y, axis=1).astype(np.float64)
        if file_sr != sr:
            n = int(len(y) * sr / file_sr)
            y = np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(y)), y)
        self.sr = sr
        self.y = y
        self.hop = max(1, int(chunk_s * sr))
        self.pos = 0
        self.loop = True

    def read(self) -> np.ndarray:
        if self.pos >= len(self.y):
            if self.loop:
                self.pos = 0
            else:
                return np.zeros(self.hop, dtype=np.float64)
        end = min(self.pos + self.hop, len(self.y))
        chunk = self.y[self.pos : end]
        self.pos = end
        if len(chunk) < self.hop:
            chunk = np.pad(chunk, (0, self.hop - len(chunk)))
        return chunk


class MicAudioSource:
    """Optional microphone capture via sounddevice."""

    def __init__(self, sr: int = 44100, chunk_s: float = 0.05) -> None:
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError(
                "Mic mode requires: pip install sounddevice. Use --source file instead."
            ) from exc
        self.sd = sd
        self.sr = sr
        self.hop = max(1, int(chunk_s * sr))

    def read(self) -> np.ndarray:
        frames = self.sd.rec(self.hop, samplerate=self.sr, channels=1, dtype="float64")
        self.sd.wait()
        return frames[:, 0]
