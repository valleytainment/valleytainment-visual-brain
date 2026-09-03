extends Node2D
## Procedural sentient-face overlay for the Valleytainment monster.
## Keeps the source logo untouched while adding deterministic blink, gaze,
## glow, and audio-reactive eye behavior above the wordmark.

var _rng := RandomNumberGenerator.new()
var _life_t: float = 0.0
var _next_blink_t: float = 2.0
var _blink_t: float = -1.0
var _eye_open: float = 1.0
var _next_gaze_t: float = 0.0
var _gaze := Vector2.ZERO
var _gaze_target := Vector2.ZERO

var _intensity: float = 0.2
var _kick: float = 0.0
var _bass: float = 0.0
var _snare: float = 0.0
var _hat: float = 0.0
var _drop: float = 0.0
var _section: String = "INTRO"
var _profile: String = "BALANCED"

const EYE_SPACING := 92.0
const EYE_RX := 25.0
const EYE_RY := 12.0
const BLINK_CLOSE_S := 0.075
const BLINK_OPEN_S := 0.095


func _ready() -> void:
	_rng.seed = 926183
	_schedule_blink()
	_schedule_gaze()
	queue_redraw()


func apply_audio(feat: Dictionary, section_label: String) -> void:
	_intensity = clampf(float(feat.get("intensity", 0.2)), 0.0, 1.0)
	_kick = clampf(float(feat.get("kick_energy", 0.0)), 0.0, 1.0)
	_bass = clampf(float(feat.get("bass_energy", 0.0)), 0.0, 1.0)
	_snare = clampf(float(feat.get("snare_energy", 0.0)), 0.0, 1.0)
	_hat = clampf(float(feat.get("hat_energy", 0.0)), 0.0, 1.0)
	_drop = clampf(float(feat.get("drop_probability", 0.0)), 0.0, 1.0)
	var requested := str(feat.get("creature_profile", _profile)).to_upper()
	if requested in ["BALANCED", "WET", "CREEPY", "AGGRESSIVE", "UNHINGED"]:
		_profile = requested
	if section_label != "" and section_label != "—":
		_section = section_label


func _process(delta: float) -> void:
	_life_t += delta
	_update_blink(delta)
	_update_gaze(delta)
	queue_redraw()


func _profile_value(kind: String) -> float:
	match _profile:
		"WET":
			return {"gaze_speed": 0.82, "gaze_range": 0.85, "blink_rate": 0.92, "awake": 0.98}.get(kind, 1.0)
		"CREEPY":
			return {"gaze_speed": 0.46, "gaze_range": 1.18, "blink_rate": 0.70, "awake": 0.88}.get(kind, 1.0)
		"AGGRESSIVE":
			return {"gaze_speed": 1.35, "gaze_range": 1.05, "blink_rate": 1.28, "awake": 1.14}.get(kind, 1.0)
		"UNHINGED":
			return {"gaze_speed": 2.05, "gaze_range": 1.45, "blink_rate": 1.65, "awake": 1.26}.get(kind, 1.0)
		_:
			return 1.0


func _update_blink(delta: float) -> void:
	if _blink_t < 0.0 and _life_t >= _next_blink_t:
		_blink_t = 0.0

	if _blink_t < 0.0:
		_eye_open = 1.0
		return

	var blink_speed := clampf(_profile_value("blink_rate"), 0.55, 1.8)
	_blink_t += delta * blink_speed
	if _blink_t <= BLINK_CLOSE_S:
		_eye_open = 1.0 - (_blink_t / BLINK_CLOSE_S)
	elif _blink_t <= BLINK_CLOSE_S + BLINK_OPEN_S:
		_eye_open = (_blink_t - BLINK_CLOSE_S) / BLINK_OPEN_S
	else:
		_eye_open = 1.0
		_blink_t = -1.0
		_schedule_blink()


func _update_gaze(delta: float) -> void:
	if _life_t >= _next_gaze_t:
		var gaze_range := _profile_value("gaze_range")
		_gaze_target = Vector2(
			_rng.randf_range(-1.0, 1.0) * gaze_range,
			_rng.randf_range(-0.6, 0.6) * gaze_range
		)
		_schedule_gaze()
	var gaze_speed := 2.2 * _profile_value("gaze_speed")
	_gaze = _gaze.lerp(_gaze_target, clampf(delta * gaze_speed, 0.0, 1.0))


func _schedule_blink() -> void:
	var wait := _rng.randf_range(2.2, 5.2) / maxf(_profile_value("blink_rate"), 0.55)
	if _section in ["BUILD", "PRE_DROP"]:
		wait *= 0.7
	_next_blink_t = _life_t + wait


func _schedule_gaze() -> void:
	var cadence := 1.0 / maxf(_profile_value("gaze_speed"), 0.35)
	_next_gaze_t = _life_t + _rng.randf_range(1.8, 4.2) * cadence


func _ellipse(center: Vector2, rx: float, ry: float, color: Color) -> void:
	var points := PackedVector2Array()
	for i in range(40):
		var a := TAU * float(i) / 40.0
		points.append(center + Vector2(cos(a) * rx, sin(a) * ry))
	draw_colored_polygon(points, color)


func _draw() -> void:
	var section_awake := 1.0
	if _section == "SILENCE":
		section_awake = 0.32
	elif _section == "PRE_DROP":
		section_awake = 0.62
	elif _section in ["DROP", "SECOND_DROP"]:
		section_awake = 1.2

	var profile_awake := _profile_value("awake")
	var awake := clampf(
		(0.5 + _intensity * 0.45 + _drop * 0.25) * section_awake * profile_awake,
		0.18,
		1.40
	)
	var eye_shape := 1.0
	if _profile == "CREEPY":
		eye_shape = 0.72
	elif _profile == "AGGRESSIVE":
		eye_shape = 1.08
	elif _profile == "UNHINGED":
		eye_shape = 1.18 + sin(_life_t * 6.0) * 0.05
	var open_y := maxf(0.65, EYE_RY * _eye_open * (0.9 + _bass * 0.12) * eye_shape)
	var gaze_px := _gaze * Vector2(5.5, 3.0)
	var kick_widen := _kick * 2.5 * (1.25 if _profile in ["AGGRESSIVE", "UNHINGED"] else 1.0)
	var snare_flash := _snare * _snare

	for side in [-1.0, 1.0]:
		var center := Vector2(side * (EYE_SPACING + kick_widen), 0.0)
		var edge_color := Color(1.0, 0.68 + _hat * 0.2, 0.18, 0.16 * awake)
		var iris_color := Color(
			0.22 + _drop * 0.45,
			0.82 + snare_flash * 0.18,
			1.0,
			0.78 * awake
		)
		if _profile == "CREEPY":
			iris_color = Color(0.42 + _drop * 0.28, 0.95, 0.70, 0.68 * awake)
		elif _profile == "AGGRESSIVE":
			iris_color = Color(1.0, 0.42 + snare_flash * 0.28, 0.18, 0.82 * awake)
		elif _profile == "UNHINGED":
			iris_color = Color(1.0, 0.22 + _hat * 0.35, 0.72 + _drop * 0.28, 0.90 * awake)

		_ellipse(center, EYE_RX * 1.95, maxf(1.0, open_y * 2.0), Color(0.2, 0.75, 1.0, 0.035 * awake))
		_ellipse(center, EYE_RX * 1.45, maxf(1.0, open_y * 1.5), edge_color)
		_ellipse(center, EYE_RX, open_y, iris_color)

		if _eye_open > 0.12:
			var pupil := center + gaze_px
			var pupil_scale := 0.82 if _profile == "CREEPY" else 1.0
			if _profile == "UNHINGED":
				pupil_scale = 1.15 + sin(_life_t * 7.0 + side) * 0.12
			_ellipse(
				pupil,
				(7.2 + _bass * 1.2) * pupil_scale,
				maxf(0.8, 7.8 * _eye_open * pupil_scale),
				Color(0.005, 0.008, 0.02, 0.92)
			)
			_ellipse(
				pupil + Vector2(-2.2, -2.0),
				2.2 + snare_flash * 1.6,
				maxf(0.6, 2.0 * _eye_open),
				Color(1.0, 1.0, 1.0, 0.9)
			)

		var ridge_y := -open_y - 3.0
		draw_line(
			center + Vector2(-EYE_RX, ridge_y),
			center + Vector2(EYE_RX, ridge_y + sin(_life_t * 1.7 + side) * 1.5),
			Color(1.0, 0.7, 0.2, 0.45 * awake),
			2.0,
			true
		)
