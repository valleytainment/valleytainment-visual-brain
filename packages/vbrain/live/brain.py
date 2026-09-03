"""Live performance brain — FFT, onset, rolling BPM, section heuristic, cues."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from time import monotonic

import numpy as np

from vbrain.live.fft import live_bands
from vbrain.schemas import SectionLabel, intensity_band


@dataclass
class LiveState:
    t: float
    bpm: float
    section: str
    intensity: float
    intensity_band: str
    kick_energy: float
    bass_energy: float
    snare_energy: float
    hat_energy: float
    vocal_energy: float
    spectral_brightness: float
    loudness: float
    drop_probability: float
    onset: float
    action: str = "tick"
    seed: int = 926183
    style: str = "biomechanical_cyber_cathedral"
    hero_scene: str = "valleytainment_logo"

    def as_features(self) -> dict:
        return {
            "t": self.t,
            "intensity": self.intensity,
            "kick_energy": self.kick_energy,
            "bass_energy": self.bass_energy,
            "snare_energy": self.snare_energy,
            "hat_energy": self.hat_energy,
            "vocal_energy": self.vocal_energy,
            "spectral_brightness": self.spectral_brightness,
            "loudness": self.loudness,
            "drop_probability": self.drop_probability,
            "section": self.section,
        }

    def as_dict(self) -> dict:
        d = self.as_features()
        d.update(
            {
                "bpm": self.bpm,
                "intensity_band": self.intensity_band,
                "onset": self.onset,
                "action": self.action,
                "seed": self.seed,
                "style": self.style,
                "hero_scene": self.hero_scene,
            }
        )
        return d


@dataclass
class LiveBrain:
    """Stateful live analyzer for Mode B / HYBRID."""

    sr: int = 44100
    seed: int = 926183
    style: str = "biomechanical_cyber_cathedral"
    _onset_hist: deque[float] = field(default_factory=lambda: deque(maxlen=64))
    _bpm_hist: deque[float] = field(default_factory=lambda: deque(maxlen=16))
    _intensity_hist: deque[float] = field(default_factory=lambda: deque(maxlen=32))
    _last_onset_t: float = 0.0
    _start_t: float = field(default_factory=monotonic)
    _section: SectionLabel = SectionLabel.INTRO
    _drop_latched: bool = False

    def process(self, samples: np.ndarray) -> LiveState:
        now = monotonic()
        t = now - self._start_t
        bands = live_bands(samples, sr=self.sr)
        kick = bands["kick"]
        bass = bands["bass"]
        mid = bands["mid"]
        hat = bands["hat"]
        loud = bands["loudness"]

        # Onset proxy: kick jump
        prev = self._onset_hist[-1] if self._onset_hist else 0.0
        onset = max(0.0, kick - prev)
        self._onset_hist.append(kick)
        if onset > 0.18:
            if self._last_onset_t > 0:
                ibi = now - self._last_onset_t
                if 0.25 < ibi < 1.2:
                    self._bpm_hist.append(60.0 / ibi)
            self._last_onset_t = now

        bpm = float(np.median(self._bpm_hist)) if self._bpm_hist else 128.0
        intensity = float(np.clip(0.4 * kick + 0.3 * bass + 0.2 * loud + 0.1 * hat, 0.0, 1.0))
        self._intensity_hist.append(intensity)
        mean_i = float(np.mean(self._intensity_hist))
        rising = intensity > mean_i + 0.08
        drop_p = float(np.clip(0.5 * intensity + 0.5 * max(0.0, intensity - mean_i) * 4, 0, 1))

        section = self._infer_section(intensity, drop_p, rising, loud)
        action = self._arbitrate(section, onset, drop_p)

        snare = float(np.clip(mid * (0.5 + onset), 0.0, 1.0))
        brightness = float(np.clip(0.35 * hat + 0.65 * mid, 0.0, 1.0))

        return LiveState(
            t=t,
            bpm=round(bpm, 2),
            section=section.value,
            intensity=intensity,
            intensity_band=intensity_band(intensity).value,
            kick_energy=kick,
            bass_energy=bass,
            snare_energy=snare,
            hat_energy=hat,
            vocal_energy=float(np.clip(mid * 0.6, 0.0, 1.0)),
            spectral_brightness=brightness,
            loudness=loud,
            drop_probability=drop_p,
            onset=float(onset),
            action=action,
            seed=self.seed,
            style=self.style,
        )

    def _infer_section(
        self, intensity: float, drop_p: float, rising: bool, loud: float
    ) -> SectionLabel:
        if loud < 0.04 and intensity < 0.08:
            self._section = SectionLabel.SILENCE
        elif intensity >= 0.82 or (drop_p >= 0.72 and intensity >= 0.7):
            self._section = SectionLabel.SECOND_DROP if self._drop_latched else SectionLabel.DROP
            self._drop_latched = True
        elif rising and intensity >= 0.45:
            self._section = SectionLabel.PRE_DROP if intensity >= 0.65 else SectionLabel.BUILD
        elif intensity < 0.22:
            self._section = SectionLabel.INTRO
        elif intensity < 0.35 and not rising:
            self._section = SectionLabel.BREAKDOWN
        else:
            self._section = SectionLabel.VERSE
        return self._section

    def _arbitrate(self, section: SectionLabel, onset: float, drop_p: float) -> str:
        if section in (SectionLabel.DROP, SectionLabel.SECOND_DROP) and onset > 0.2:
            return "trigger_drop"
        if section == SectionLabel.PRE_DROP:
            return "trigger_pre_drop"
        if section == SectionLabel.SILENCE:
            return "trigger_silence"
        if drop_p > 0.8 and onset > 0.15:
            return "trigger_shockwave"
        return "tick"
