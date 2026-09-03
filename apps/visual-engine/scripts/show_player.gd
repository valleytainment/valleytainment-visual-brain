extends Node
## Loads a compiled show pack (runtime.json) and drives the reactive shader.

@onready var viewport_root: ColorRect = $ViewportRoot
@onready var section_label: Label = $HUD/SectionLabel
@onready var info_label: Label = $HUD/Info
@onready var audio_bus: Node = $AudioBus

var runtime: Dictionary = {}
var playing: bool = false
var show_time: float = 0.0
var duration: float = 0.0
var bpm: float = 128.0
var sections: Array = []
var frames: Array = []
var frame_index: int = 0
var current_section: String = "—"

const DEFAULT_RUNTIME := "res://assets/runtime.json"
const USER_RUNTIME := "user://runtime.json"


func _ready() -> void:
	_load_runtime(_resolve_runtime_path())
	playing = true


func _resolve_runtime_path() -> String:
	if FileAccess.file_exists(USER_RUNTIME):
		return USER_RUNTIME
	if FileAccess.file_exists(DEFAULT_RUNTIME):
		return DEFAULT_RUNTIME
	# Also try absolute-ish project-relative shows folder copies
	var candidates := [
		"res://runtime.json",
		"res://assets/runtime.json",
	]
	for c in candidates:
		if FileAccess.file_exists(c):
			return c
	return ""


func _load_runtime(path: String) -> void:
	if path == "":
		info_label.text = "VALLEYTAINMENT VISUAL BRAIN\nNo runtime.json found — run: vbrain analyze track.wav"
		_apply_features(0.15, 0.1, 0.05, 0.0, 0.1)
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
	var title: String = str(runtime.get("story", {}).get("title", runtime.get("show_id", "SHOW")))
	info_label.text = "%s\nBPM %.1f  |  seed %s  |  %s\nSpace play/pause · R restart · [ ] seek" % [
		title,
		bpm,
		str(runtime.get("seed", 0)),
		str(runtime.get("style", "")),
	]


func _process(delta: float) -> void:
	if not playing:
		# Still allow live mic reactivity if enabled
		if audio_bus.has_method("is_live") and audio_bus.is_live():
			var live: Dictionary = audio_bus.get_bands()
			_apply_features(
				float(live.get("loudness", 0.2)),
				float(live.get("kick", 0.0)),
				float(live.get("bass", 0.0)),
				float(live.get("hat", 0.0)),
				float(live.get("loudness", 0.2)) * 0.5
			)
		return

	show_time += delta
	if duration > 0.0 and show_time > duration:
		show_time = fmod(show_time, duration)

	_update_section()
	var feat := _features_at(show_time)
	_apply_features(
		float(feat.get("intensity", 0.2)),
		float(feat.get("kick_energy", 0.0)),
		float(feat.get("bass_energy", 0.0)),
		float(feat.get("hat_energy", 0.0)),
		float(feat.get("drop_probability", 0.0))
	)
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
		return {"intensity": 0.2, "kick_energy": 0.0, "bass_energy": 0.0, "hat_energy": 0.0, "drop_probability": 0.0}
	# Frames are roughly sorted by t; advance pointer
	while frame_index + 1 < frames.size() and float(frames[frame_index + 1].get("t", 0.0)) <= t:
		frame_index += 1
	while frame_index > 0 and float(frames[frame_index].get("t", 0.0)) > t:
		frame_index -= 1
	return frames[frame_index]


func _apply_features(intensity: float, kick: float, bass: float, hat: float, drop_p: float) -> void:
	var mat := viewport_root.material as ShaderMaterial
	if mat == null:
		return
	mat.set_shader_parameter("intensity", intensity)
	mat.set_shader_parameter("kick", kick)
	mat.set_shader_parameter("bass", bass)
	mat.set_shader_parameter("hat", hat)
	mat.set_shader_parameter("glitch", clamp(drop_p * intensity, 0.0, 1.0))
	mat.set_shader_parameter("chromatic", clamp(intensity * 0.7, 0.0, 1.0))
	mat.set_shader_parameter("time_scale", 0.6 + intensity * 1.8)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept") or (event is InputEventKey and event.pressed and event.keycode == KEY_SPACE):
		playing = not playing
	elif event is InputEventKey and event.pressed and event.keycode == KEY_R:
		show_time = 0.0
		frame_index = 0
		playing = true
	elif event is InputEventKey and event.pressed and event.keycode == KEY_BRACKETLEFT:
		show_time = max(0.0, show_time - 4.0)
		frame_index = 0
	elif event is InputEventKey and event.pressed and event.keycode == KEY_BRACKETRIGHT:
		show_time += 4.0
		frame_index = 0
