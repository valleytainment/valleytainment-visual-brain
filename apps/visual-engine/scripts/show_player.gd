extends Node
## Loads a compiled show pack (runtime.json) and drives the Valleytainment logo hero.
## Press L to toggle live API mode (vbrain live @ :8765).

@onready var section_label: Label = $HUD/SectionLabel
@onready var info_label: Label = $HUD/Info
@onready var audio_bus: Node = $AudioBus
@onready var hero: Node2D = $Hero
@onready var post_fx: ColorRect = $PostLayer/PostFX

var runtime: Dictionary = {}
var playing: bool = false
var live_mode: bool = false
var show_time: float = 0.0
var duration: float = 0.0
var bpm: float = 128.0
var sections: Array = []
var frames: Array = []
var frame_index: int = 0
var current_section: String = "—"

const DEFAULT_RUNTIME := "res://assets/fixtures/demo_runtime.json"
const USER_RUNTIME := "user://runtime.json"
const LIVE_API := "http://127.0.0.1:8765/api/live"


func _ready() -> void:
	_load_runtime(_resolve_runtime_path())
	playing = true


func _resolve_runtime_path() -> String:
	if FileAccess.file_exists(USER_RUNTIME):
		return USER_RUNTIME
	if FileAccess.file_exists(DEFAULT_RUNTIME):
		return DEFAULT_RUNTIME
	for c in ["res://runtime.json", "res://assets/runtime.json"]:
		if FileAccess.file_exists(c):
			return c
	return ""


func _load_runtime(path: String) -> void:
	if path == "":
		info_label.text = "VALLEYTAINMENT VISUAL BRAIN\nNo runtime.json — run: vbrain analyze track.wav"
		_drive_features({
			"intensity": 0.2,
			"kick_energy": 0.1,
			"bass_energy": 0.08,
			"snare_energy": 0.0,
			"hat_energy": 0.05,
			"drop_probability": 0.0,
			"spectral_brightness": 0.3,
		})
		return

	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		info_label.text = "Failed to open %s" % path
		return
	var data = JSON.parse_string(f.get_as_text())
	if typeof(data) != TYPE_DICTIONARY:
		info_label.text = "Invalid runtime JSON"
		return

	runtime = data
	duration = float(runtime.get("duration_s", 0.0))
	bpm = float(runtime.get("bpm", 128.0))
	sections = runtime.get("sections", [])
	frames = runtime.get("frames", [])
	_refresh_hud_title()


func _refresh_hud_title() -> void:
	var title: String = str(runtime.get("story", {}).get("title", runtime.get("show_id", "SHOW")))
	var mode := "LIVE API" if live_mode else "PREPARED"
	info_label.text = "%s\n%s · BPM %.1f · seed %s · hero logo\nSpace play/pause · L live · R restart · [ ] seek" % [
		title,
		mode,
		bpm,
		str(runtime.get("seed", 0)),
	]


func _process(delta: float) -> void:
	if live_mode and audio_bus.has_method("is_live") and audio_bus.is_live():
		var payload: Dictionary = {}
		if audio_bus.has_method("get_live_payload"):
			payload = audio_bus.get_live_payload()
		if payload.is_empty():
			var live: Dictionary = audio_bus.get_bands()
			payload = {
				"intensity": float(live.get("loudness", 0.2)),
				"kick_energy": float(live.get("kick", 0.0)),
				"bass_energy": float(live.get("bass", 0.0)),
				"snare_energy": float(live.get("mid", 0.0)),
				"hat_energy": float(live.get("hat", 0.0)),
				"drop_probability": float(live.get("loudness", 0.0)),
				"spectral_brightness": float(live.get("hat", 0.0)),
				"section": current_section,
			}
		current_section = str(payload.get("section", current_section))
		bpm = float(payload.get("bpm", bpm))
		_drive_features(payload)
		section_label.text = "%s  ·  LIVE  ·  I=%.2f" % [
			current_section,
			float(payload.get("intensity", 0.0)),
		]
		return

	if not playing:
		return

	show_time += delta
	if duration > 0.0 and show_time > duration:
		show_time = fmod(show_time, duration)
		frame_index = 0

	_update_section()
	var feat := _features_at(show_time)
	_drive_features(feat)
	section_label.text = "%s  ·  t=%.1fs  ·  I=%.2f" % [
		current_section,
		show_time,
		float(feat.get("intensity", 0.0)),
	]


func _update_section() -> void:
	current_section = "—"
	for s in sections:
		if show_time >= float(s.get("start_t", 0.0)) and show_time <= float(s.get("end_t", 0.0)):
			current_section = str(s.get("label", "—"))
			return


func _features_at(t: float) -> Dictionary:
	if frames.is_empty():
		return {
			"intensity": 0.2,
			"kick_energy": 0.0,
			"bass_energy": 0.0,
			"snare_energy": 0.0,
			"hat_energy": 0.0,
			"drop_probability": 0.0,
			"spectral_brightness": 0.2,
		}
	while frame_index + 1 < frames.size() and float(frames[frame_index + 1].get("t", 0.0)) <= t:
		frame_index += 1
	while frame_index > 0 and float(frames[frame_index].get("t", 0.0)) > t:
		frame_index -= 1
	return frames[frame_index]


func _drive_features(feat: Dictionary) -> void:
	if hero and hero.has_method("apply_audio"):
		hero.apply_audio(feat, current_section)

	var mat := post_fx.material as ShaderMaterial
	if mat:
		var intensity := float(feat.get("intensity", 0.2))
		var snare := float(feat.get("snare_energy", 0.0))
		var drop_p := float(feat.get("drop_probability", 0.0))
		mat.set_shader_parameter("bloom", 0.35 + intensity * 0.7)
		mat.set_shader_parameter("chromatic", clampf(intensity * 0.55 + drop_p * 0.25, 0.0, 1.0))
		mat.set_shader_parameter("flash", clampf(snare * snare, 0.0, 1.0))
		mat.set_shader_parameter("vignette", 0.3 + (0.25 if current_section == "PRE_DROP" else 0.0))


func _toggle_live() -> void:
	live_mode = not live_mode
	if audio_bus.has_method("enable_live"):
		audio_bus.enable_live(live_mode, LIVE_API)
	playing = not live_mode
	_refresh_hud_title()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_L:
		_toggle_live()
	elif event.is_action_pressed("ui_accept") or (event is InputEventKey and event.pressed and event.keycode == KEY_SPACE):
		if live_mode:
			return
		playing = not playing
	elif event is InputEventKey and event.pressed and event.keycode == KEY_R:
		show_time = 0.0
		frame_index = 0
		playing = true
		live_mode = false
		if audio_bus.has_method("enable_live"):
			audio_bus.enable_live(false)
		_refresh_hud_title()
	elif event is InputEventKey and event.pressed and event.keycode == KEY_BRACKETLEFT:
		show_time = maxf(0.0, show_time - 4.0)
		frame_index = 0
	elif event is InputEventKey and event.pressed and event.keycode == KEY_BRACKETRIGHT:
		show_time += 4.0
		frame_index = 0
