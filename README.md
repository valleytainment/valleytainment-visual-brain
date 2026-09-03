# Valleytainment Visual Brain

AI **visual performance instrument** for EDM — not an AI video generator.

```text
MUSIC → UNDERSTANDS → FEELS → DIRECTS → PERFORMS (Godot)
```

Software/API cost target: **$0/month**. Compute hardware is the only real cost.

## Status

| Layer | Status |
| ----- | ------ |
| Music analyzer (BPM, bands, sections, drop heuristic) | **Working** |
| Intensity engine + cue map | **Working** |
| Visual director (rule-based + optional Ollama/Qwen) | **Working** |
| Show pack + `runtime.json` contract | **Working** |
| Godot 4 **Valleytainment logo hero** (kick/bass/snare/hat/drop) | **Working** |
| CI (Ruff + pytest on 3.11/3.13 + Godot asset smoke) | **Working** |
| Demucs stems | Optional (`pip install .[stems]`) |
| ComfyUI / FLUX / Wan / Hunyuan factory | Phase 3 |

## Quick start

```bash
cd valleytainment-visual-brain
# Prefer Python 3.11–3.13 (3.14 lacks some audio wheels on macOS)
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Analyze a track → shows/<id>/
vbrain analyze /path/to/track.wav --seed 926183

# Or rebuild the compact demo fixture used by Godot + CI:
python scripts/make_demo_track.py
python scripts/build_demo_fixture.py
```

Open `apps/visual-engine` in **Godot 4.3+** and press Play.  
It loads the canonical fixture at `assets/fixtures/demo_runtime.json` (not the large generated show packs under `shows/`).

Controls: `Space` play/pause · `R` restart · `[` `]` seek ±4s

### Optional local LLM director

```bash
ollama pull qwen3:8b
vbrain analyze track.wav --ollama --ollama-model qwen3:8b
```

## Hero scene map

```text
VALLEYTAINMENT LOGO
      │
      ├── kick → ~1–2% pulse
      ├── bass → dimensional breathing / parallax
      ├── snare → gold/teeth flash
      ├── hats → glitter emission
      ├── synth/brightness → rainbow plasma flow
      ├── buildup → portal charge
      ├── pre-drop → vacuum/blackout
      └── drop → radial cosmic eruption
```

## Architecture

1. **Prepared show** — analyze → direct → show pack → Godot performs  
2. **Live / unknown set** — FFT bands + prebuilt worlds (Godot `audio_bus.gd`)  
3. **AI factory** (Phase 3) — ComfyUI generates worlds offline; performance PC never needs the GPU models

## Repo map

```text
packages/vbrain/     Python brain (analyzer, director, showpack, CLI)
apps/visual-engine/  Godot 4 performance instrument (logo hero)
tests/fixtures/      Compact deterministic demo_runtime.json
shows/               Compiled show packs (gitignored)
configs/             Defaults / GPU tiers
ai/                  Future ComfyUI workflow hooks
.github/workflows/   CI
```

## Show pack files

```text
shows/SHOW_ID/
  analysis.json
  visual_story.json
  show_seed.json
  cue_map.json
  show_pack.json
  runtime.json      ← copy to user://runtime.json for custom shows
```

Godot’s checked-in fixture is intentionally small and contract-validated:

```text
apps/visual-engine/assets/fixtures/demo_runtime.json
tests/fixtures/demo_runtime.json
```

## License

MIT — Valleytainment Visual Brain application code.  
Third-party models (FLUX, Wan, Demucs, etc.) keep their own licenses; check before commercial shipping of generated assets.  
Brand logo artwork © Valleytainment.
