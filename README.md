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

# ONE COMMAND — live brain + panel + Godot
vbrain launch

# Or generate a real AI world plate into Godot (uses your local ComfyUI / SD1.5)
vbrain factory generate-world
```

Godot keys: `Space` · `L` live · `H` hybrid · `R` restart · `[` `]` seek

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
