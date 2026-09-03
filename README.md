# Valleytainment Visual Brain

AI **visual performance instrument** for EDM — not an AI video generator.

```text
MUSIC → UNDERSTANDS → FEELS → DIRECTS → PERFORMS (Godot)
```

Software/API cost target: **$0/month**. Compute hardware is the only real cost.

## What's in Phase 1 (this repo)

| Layer | Status |
| ----- | ------ |
| Music analyzer (BPM, bands, sections, drop heuristic) | **Working** |
| Intensity engine + cue map | **Working** |
| Visual director (rule-based + optional Ollama/Qwen) | **Working** |
| Show pack writer (`runtime.json` for Godot) | **Working** |
| Godot 4 reactive tunnel engine | **Scaffolded** |
| Demucs stems | Optional (`pip install .[stems]`) |
| ComfyUI / FLUX / Wan / Hunyuan factory | Stubs / next phase |

## Quick start

```bash
cd "edm visual god"
# Prefer Python 3.11–3.13 (3.14 lacks some audio wheels on macOS)
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Analyze a track → shows/<id>/
vbrain analyze /path/to/track.wav --seed 926183

# Or generate a synthetic EDM-ish fixture and analyze it:
python scripts/make_demo_track.py
vbrain analyze assets/demo/demo_drop.wav --show-id _demo
```

Open `apps/visual-engine` in **Godot 4.3+**. Copy `shows/_demo/runtime.json` into the Godot project (or `user://runtime.json`) and press Play.

Controls: `Space` play/pause · `R` restart · `[` `]` seek ±4s

### Optional local LLM director

```bash
ollama pull qwen3:8b
vbrain analyze track.wav --ollama --ollama-model qwen3:8b
```

## Architecture

See the product brief you wrote — this repo implements the left half first:

1. **Prepared show** — analyze → direct → show pack → Godot performs  
2. **Live / unknown set** — FFT bands + prebuilt worlds (Godot `audio_bus.gd`)  
3. **AI factory** (later) — ComfyUI generates worlds offline; performance PC never needs the GPU models

## Repo map

```text
packages/vbrain/     Python brain (analyzer, director, showpack, CLI)
apps/visual-engine/  Godot 4 performance instrument
shows/               Compiled show packs
configs/             Defaults / GPU tiers
ai/                  Future ComfyUI workflow hooks
```

## Show pack files

```text
shows/SHOW_ID/
  analysis.json
  visual_story.json
  show_seed.json
  cue_map.json
  show_pack.json
  runtime.json      ← Godot reads this
```

## License

MIT — Valleytainment Visual Brain application code.  
Third-party models (FLUX, Wan, Demucs, etc.) keep their own licenses; check before commercial shipping of generated assets.
