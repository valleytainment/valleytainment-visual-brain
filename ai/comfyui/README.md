# ComfyUI workflow hooks — Phase 3

Place exported **API-format** workflows in `workflows/`.

```bash
vbrain factory status
vbrain factory init-manifest
vbrain factory queue ai/comfyui/workflows/flux_schnell_hero_stub.json
# when ComfyUI is running:
vbrain factory queue ai/comfyui/workflows/flux_schnell_hero_stub.json --no-dry-run
```

GPU routing (`vbrain status`) picks high/low/none automatically.
Performance machines never need this folder loaded.
