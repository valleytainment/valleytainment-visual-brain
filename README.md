# Valleytainment Visual Brain

AI **visual performance instrument** for EDM — not an AI video generator.

```text
MUSIC → UNDERSTANDS → FEELS → DIRECTS → LIVING MONSTER → PERFORMS
```

## v0.2 — Living Monster

The canonical Valleytainment logo remains the protected brand asset. The Godot renderer now makes it feel sentient without asking an image model to redraw the wordmark every frame:

- persistent asymmetric breathing, even in silence
- double-pulse heartbeat and throat/mouth dilation
- viscous tongue/slime UV motion
- wet pseudo-normal/specular material response
- deterministic blinking and wandering gaze
- audio-reactive glowing eyes
- life aura, breath mist, drool particles, glitter, and drop spit bursts
- true radial shockwave instead of a scaled rectangle
- bass depth ghosts and dimensional parallax
- pre-drop vacuum/blackout and drop eruption
- mipmapped post bloom with restrained chromatic optics
- operator HUD hidden from stage output by default

The live analyzer is also level-aware: silence can no longer be normalized into fake full-energy bands.

## Quick start

```bash
cd valleytainment-visual-brain
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# ONE COMMAND — live brain + panel + Godot
vbrain launch

# Prepared show pack
vbrain analyze /path/to/track.wav --seed 926183

# Local AI world plate through ComfyUI
vbrain factory generate-world
```

Set `GODOT_BIN=/path/to/Godot` if the launcher cannot discover Godot automatically.

### Stage keys

| Key | Action |
| --- | --- |
| `F1` | Show/hide operator HUD |
| `F11` | Fullscreen/windowed |
| `Space` | Play/pause prepared timeline |
| `L` | Live mode |
| `H` | Hybrid prepared + live mode |
| `R` | Restart prepared show |
| `[` / `]` | Seek ±4 seconds |

## Commands

| Command | Purpose |
| --- | --- |
| `vbrain launch` | Supervised one-command stack |
| `vbrain analyze TRACK` | Prepared show pack |
| `vbrain live` | Live FFT/beat brain + performer panel |
| `vbrain serve` | Panel only |
| `vbrain status` | GPU tier + Comfy + outputs |
| `vbrain factory status` | AI factory routing |
| `vbrain factory init-manifest` | Register protected logo hero asset |
| `vbrain factory queue WORKFLOW` | Submit ComfyUI workflow |
| `vbrain factory generate-world` | Generate/ingest world plate with graceful fallback |
| `vbrain list-styles` | Visual style presets |

## Architecture

```text
                     AUDIO / TRACK
                          │
              ┌───────────┴───────────┐
              │                       │
         PREPARED BRAIN          LIVE BRAIN
       sections + cue map     level-aware FFT
              │              onset/BPM/sections
              └───────────┬───────────┘
                          │
                    VISUAL STATE
                          │
              ┌───────────┴───────────┐
              │                       │
        PROTECTED LOGO          AI WORLD PLATES
              │                  ComfyUI/local
              │                       │
              └───────────┬───────────┘
                          │
                  GODOT 4.6 RUNTIME
                          │
        breath · eyes · slime · portal · particles
                          │
                  LED / OBS / PROJECTOR
```

## Validation

CI runs:

- Python 3.11 and 3.13
- Ruff lint + format checks
- full pytest suite
- static Godot asset contracts
- **real Godot 4.6.3 headless import and runtime boot**

The project intentionally targets the Godot 4.6 stable compatibility line.

## AI / GPU strategy

Heavy FLUX/Wan/Hunyuan weights are not bundled. The performance machine can remain CPU/low-GPU and play prebuilt assets, while a stronger workstation or free external compute prepares AI plates offline. ComfyUI is an optional factory, never a dependency in the 60 FPS stage path.

## Repo map

```text
packages/vbrain/             Python music brain, live engine, AI routing, CLI
apps/visual-engine/          Godot 4.6 living visual instrument
apps/control-panel/          Local performer controls
ai/comfyui/                  Workflow/API integration
assets/                      Generated asset manifest + world plates
shows/                       Compiled show packs (ignored by Git)
tests/                       Python + runtime contracts
```

## License

MIT — application code. Brand logo © Valleytainment. Third-party model licenses apply separately.
