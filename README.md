# Valleytainment Visual Brain

AI **visual performance instrument** for EDM — not an AI video generator.

```text
MUSIC → UNDERSTANDS → FEELS → DIRECTS → PERFORMS (Godot)
```

## Quick start (do-it-all)

```bash
cd valleytainment-visual-brain
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# System check
vbrain status

# Prepared show from a track
vbrain analyze /path/to/track.wav

# Live brain + control panel (demo audio if no track)
vbrain live --source file --seconds 0
# → http://127.0.0.1:8765/

# Godot 4.3+: open apps/visual-engine, Play
# Press L inside Godot to follow the live API
```

## Commands

| Command | Purpose |
| ------- | ------- |
| `vbrain analyze TRACK` | Prepared show pack |
| `vbrain live` | Live FFT brain + performer panel |
| `vbrain serve` | Panel only |
| `vbrain status` | GPU tier + Comfy + outputs |
| `vbrain factory status` | AI factory routing |
| `vbrain factory init-manifest` | Register logo hero asset |
| `vbrain factory queue WORKFLOW` | ComfyUI submit (dry-run safe) |
| `vbrain list-styles` | Visual style presets |

## Hero scene

```text
VALLEYTAINMENT LOGO
  kick pulse · bass breathe · snare gold flash · hat glitter
  plasma flow · portal charge · blackout · drop shockwave
```

Godot keys: `Space` play/pause · `L` live API · `R` restart · `[` `]` seek

## Phases

| Phase | Status |
| ----- | ------ |
| 1 Music brain + CI + fixtures | **Done** |
| 2 Logo hero visual engine | **Done** |
| 3 AI factory (Comfy client, GPU router, manifest) | **Done** (models optional/local) |
| 4 Live brain (FFT, BPM, sections, cues) | **Done** |
| 5 Performance panel / LED / OBS presets | **Done** |

Heavy FLUX/Wan/Hunyuan weights are **not** downloaded by this repo — wire ComfyUI when you have a GPU.

## License

MIT — application code. Brand logo © Valleytainment. Third-party model licenses apply separately.
