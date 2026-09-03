"""Live performance brain — level-aware FFT, adaptive onset, BPM, sections, cues."""

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
        data = self.as_features()
        data.update(
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
        return data


@dataclass
class LiveBrain:
    """Stateful low-latency analyzer for Mode B / HYBRID.

    The detector uses an adaptive kick baseline and a refractory period instead
    of a single-frame delta. Tempo candidates are folded into an EDM-useful
    range, intensity has attack/release smoothing, and section changes have a
    short hysteresis window to prevent visual thrashing.
    """

    sr: int = 44100
    seed: int = 926183
    style: str = "biomechanical_cyber_cathedral"
    _kick_hist: deque[float] = field(default_factory=lambda: deque(maxlen=32))
    _bpm_hist: deque[float] = field(default_factory=lambda: deque(maxlen=24))
    _intensity_hist: deque[float] = field(default_factory=lambda: deque(maxlen=48))
    _last_onset_t: float = 0.0
    _start_t: float = field(default_factory=monotonic)
    _section: SectionLabel = SectionLabel.INTRO
    _drop_latched: bool = False
    _smoothed_intensity: float = 0.0
    _section_changed_t: float = 0.0

    def process(self, samples: np.ndarray) -> LiveState:
        now = monotonic()
        t = now - self._start_t
        bands = live_bands(samples, sr=self.sr)

        kick = bands["kick"]
        bass = bands["bass"]
        snare_band = bands.get("snare", bands["mid"])
        mid = bands["mid"]
        vocal = bands.get("vocal", mid * 0.6)
        hat = bands["hat"]
        loud = bands["loudness"]

        onset, onset_hit = self._adaptive_onset(kick, now)
        bpm = float(np.median(self._bpm_hist)) if self._bpm_hist else 128.0

        raw_intensity = float(
            np.clip(
                0.30 * kick
                + 0.25 * bass
                + 0.20 * loud
                + 0.12 * snare_band
                + 0.08 * hat
                + 0.05 * mid,
                0.0,
                1.0,
            )
        )
        smoothing = 0.46 if raw_intensity >= self._smoothed_intensity else 0.18
        self._smoothed_intensity += (raw_intensity - self._smoothed_intensity) * smoothing
        intensity = float(np.clip(self._smoothed_intensity, 0.0, 1.0))

        mean_i = (
            float(np.mean(self._intensity_hist)) if self._intensity_hist else max(intensity, 0.01)
        )
        self._intensity_hist.append(intensity)
        rising = intensity > mean_i + 0.055
        energy_jump = max(0.0, intensity - mean_i)
        drop_p = float(
            np.clip(
                0.44 * intensity
                + 0.32 * min(1.0, energy_jump * 4.0)
                + 0.24 * min(1.0, onset * 4.0),
                0.0,
                1.0,
            )
        )
        if loud < 0.08:
            drop_p *= loud / 0.08

        section = self._infer_section(intensity, drop_p, rising, loud, t)
        action = self._arbitrate(section, onset_hit, drop_p)

        snare = float(np.clip(snare_band * (0.82 + onset * 0.55), 0.0, 1.0))
        brightness = float(np.clip(0.55 * hat + 0.45 * mid, 0.0, 1.0))

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
            vocal_energy=float(np.clip(vocal, 0.0, 1.0)),
            spectral_brightness=brightness,
            loudness=loud,
            drop_probability=drop_p,
            onset=float(onset),
            action=action,
            seed=self.seed,
            style=self.style,
        )

    def _adaptive_onset(self, kick: float, now: float) -> tuple[float, bool]:
        history = list(self._kick_hist)[-10:]
        baseline = float(np.median(history)) if history else 0.0
        spread = float(np.std(history)) if len(history) >= 4 else 0.0
        onset = max(0.0, kick - baseline)
        threshold = max(0.07, 0.045 + spread * 1.8)
        refractory_ok = self._last_onset_t <= 0.0 or (now - self._last_onset_t) >= 0.22
        hit = onset >= threshold and kick >= 0.12 and refractory_ok
        self._kick_hist.append(kick)

        if hit:
            if self._last_onset_t > 0.0:
                ibi = now - self._last_onset_t
                if 0.24 < ibi < 1.5:
                    candidate = 60.0 / ibi
                    while candidate < 70.0:
                        candidate *= 2.0
                    while candidate > 180.0:
                        candidate /= 2.0
                    self._bpm_hist.append(candidate)
            self._last_onset_t = now

        return onset, hit

    def _infer_section(
        self,
        intensity: float,
        drop_p: float,
        rising: bool,
        loud: float,
        t: float,
    ) -> SectionLabel:
        if loud < 0.045 and intensity < 0.065:
            candidate = SectionLabel.SILENCE
        elif intensity >= 0.77 or (drop_p >= 0.70 and intensity >= 0.62):
            candidate = SectionLabel.SECOND_DROP if self._drop_latched else SectionLabel.DROP
        elif rising and intensity >= 0.40:
            candidate = SectionLabel.PRE_DROP if intensity >= 0.61 else SectionLabel.BUILD
        elif intensity < 0.18:
            candidate = SectionLabel.INTRO
        elif intensity < 0.31 and not rising:
            candidate = SectionLabel.BREAKDOWN
        else:
            candidate = SectionLabel.VERSE

        urgent = candidate in {
            SectionLabel.DROP,
            SectionLabel.SECOND_DROP,
            SectionLabel.SILENCE,
        }
        if candidate != self._section and (urgent or t - self._section_changed_t >= 0.45):
            self._section = candidate
            self._section_changed_t = t
            if candidate in {SectionLabel.DROP, SectionLabel.SECOND_DROP}:
                self._drop_latched = True
        return self._section

    def _arbitrate(self, section: SectionLabel, onset_hit: bool, drop_p: float) -> str:
        if section in (SectionLabel.DROP, SectionLabel.SECOND_DROP) and onset_hit:
            return "trigger_drop"
        if section == SectionLabel.PRE_DROP:
            return "trigger_pre_drop"
        if section == SectionLabel.SILENCE:
            return "trigger_silence"
        if drop_p > 0.82 and onset_hit:
            return "trigger_shockwave"
        return "tick"
