extends Node2D
## Valleytainment monster-logo hero — festival-grade audio-reactive benchmark.
## The monster is always alive: music controls intensity, but breathing, wet
## material movement, blinking, gaze, throat motion, and aura persist in silence.

signal features_applied(features: Dictionary)

@onready var portal: ColorRect = $PortalLayer/Portal
@onready var logo: Sprite2D = $LogoLayer/Logo
@onready var ghost_a: Sprite2D = $LogoLayer/LogoGhostA
@onready var ghost_b: Sprite2D = $LogoLayer/LogoGhostB
@onready var aura: Sprite2D = $LogoLayer/LifeAura
@onready var living_face: Node2D = $LogoLayer/LivingFace
@onready var glitter: GPUParticles2D = $LogoLayer/Glitter
@onready var breath_mist: GPUParticles2D = $LogoLayer/BreathMist
@onready var drool_mist: GPUParticles2D = $LogoLayer/DroolMist
@onready var shock_ring: Node2D = $FXLayer/ShockRing
@onready var spit: GPUParticles2D = $FXLayer/SpitBurst

var base_logo_scale: Vector2 = Vector2.ONE
var shock_t: float = 0.0
var last_kick: float = 0.0
var last_snare: float = 0.0
var section: String = "INTRO"
var section_blend: float = 1.0
var prev_section: String = "INTRO"
var _life_time: float = 0.0
var _last_features: Dictionary = {}


func _ready() -> void:
	base_logo_scale = logo.scale
	if glitter:
		glitter.emitting = true
	if breath_mist:
		breath_mist.emitting = true
	if drool_mist:
		drool_mist.emitting = true
	_try_load_world_plate()


func _try_load_world_plate() -> void:
	var path := "res://assets/textures/cyber_cathedral_plate.png"
	if not ResourceLoader.exists(path):
		return
	var tex := load(path)
	var mat := portal.material as ShaderMaterial
	if mat and tex:
		mat.set_shader_parameter("world_tex", tex)
		mat.set_shader_parameter("has_world", 1.0)
		mat.set_shader_parameter("plate_mix", 0.5)


func apply_audio(feat: Dictionary, section_label: String) -> void:
	_last_features = feat.duplicate()
	if section_label != section and section_label != "—":
		prev_section = section
		section = section_label
		section_blend = 0.0
	elif section_label != "—":
		section = section_label

	var intensity := clampf(float(feat.get("intensity", 0.2)), 0.0, 1.0)
	var kick := clampf(float(feat.get("kick_energy", 0.0)), 0.0, 1.0)
	var bass := clampf(float(feat.get("bass_energy", 0.0)), 0.0, 1.0)
	var snare := clampf(float(feat.get("snare_energy", 0.0)), 0.0, 1.0)
	var hat := clampf(float(feat.get("hat_energy", 0.0)), 0.0, 1.0)
	var drop_p := clampf(float(feat.get("drop_probability", 0.0)), 0.0, 1.0)
	var brightness := clampf(float(feat.get("spectral_brightness", 0.0)), 0.0, 1.0)

	var is_drop := section in ["DROP", "SECOND_DROP"]
	var is_build := section in ["BUILD", "PRE_DROP"]
	var blackout := 0.0
	if section == "SILENCE":
		blackout = 0.72
	elif section == "PRE_DROP":
		blackout = lerpf(0.12, 0.82, intensity)

	var charge := 0.0
	if is_build:
		charge = clampf(intensity * 1.15, 0.0, 1.0)

	var drop_amt := 1.0 if is_drop else clampf(drop_p * intensity, 0.0, 1.0)

	if is_drop and kick > 0.72 and last_kick < 0.55:
		shock_t = 0.001
		_burst_spit()
	elif kick > 0.85 and last_kick < 0.5 and intensity > 0.7:
		shock_t = 0.001
	last_kick = kick

	var snare_hit := snare
	if snare > 0.55 and last_snare < 0.35:
		snare_hit = minf(1.0, snare + 0.45)
	last_snare = snare

	var breath_phase := 0.5 + 0.5 * sin(_life_time * 1.18)
	var heartbeat := _heartbeat_pulse(_life_time)
	var mouth_pulse := 0.5 + 0.5 * sin(_life_time * 0.84 + bass * 0.7)
	var life_amount := clampf(0.62 + intensity * 0.32 + drop_amt * 0.14, 0.48, 1.18)
	if section == "SILENCE":
		life_amount = 0.52
	var wetness := clampf(0.72 + brightness * 0.26 + bass * 0.14, 0.55, 1.15)
	var goo_motion := clampf(0.65 + bass * 0.28 + intensity * 0.14, 0.55, 1.15)

	# Persistent asymmetric breathing plus beat response. The source art stays readable.
	var scale_x := 1.0 + kick * 0.018 + bass * 0.020 + (breath_phase - 0.5) * 0.010 + heartbeat * 0.005
	var scale_y := 1.0 + kick * 0.014 + bass * 0.026 - (breath_phase - 0.5) * 0.007 + heartbeat * 0.008
	if is_drop:
		scale_x += kick * 0.010
		scale_y += kick * 0.012
	logo.scale = Vector2(base_logo_scale.x * scale_x, base_logo_scale.y * scale_y)
	logo.rotation = sin(_life_time * 0.43) * 0.004 + sin(_life_time * 1.5) * bass * 0.010
	logo.modulate.a = lerpf(0.38, 1.0, section_blend)

	# Depth parallax ghosts make the flat logo occupy real stage depth.
	if ghost_a:
		ghost_a.scale = Vector2(
			base_logo_scale.x * (scale_x * 1.035 + bass * 0.018),
			base_logo_scale.y * (scale_y * 1.035 + bass * 0.012)
		)
		ghost_a.position = logo.position + Vector2(-16.0 - bass * 10.0, 8.0 + kick * 4.0)
		ghost_a.modulate = Color(1.0, 0.55, 0.85, 0.14 + hat * 0.10)
		ghost_a.rotation = logo.rotation * 1.3
	if ghost_b:
		ghost_b.scale = Vector2(
			base_logo_scale.x * (scale_x * 0.965 - kick * 0.008),
			base_logo_scale.y * (scale_y * 0.965 - kick * 0.006)
		)
		ghost_b.position = logo.position + Vector2(20.0 + bass * 8.0, -9.0 - bass * 6.0)
		ghost_b.modulate = Color(0.4, 0.95, 1.0, 0.11 + brightness * 0.09)
		ghost_b.rotation = -logo.rotation * 0.8

	_apply_logo_mat(
		logo,
		intensity,
		kick,
		bass,
		snare_hit,
		hat,
		drop_amt,
		blackout,
		brightness,
		life_amount,
		breath_phase,
		heartbeat,
		mouth_pulse,
		wetness,
		goo_motion
	)
	if ghost_a:
		_apply_logo_mat(
			ghost_a,
			intensity * 0.65,
			kick,
			bass,
			snare_hit * 0.45,
			hat,
			drop_amt * 0.45,
			blackout,
			brightness,
			life_amount * 0.45,
			breath_phase,
			heartbeat * 0.4,
			mouth_pulse,
			wetness * 0.6,
			goo_motion * 0.5
		)
	if ghost_b:
		_apply_logo_mat(
			ghost_b,
			intensity * 0.65,
			kick,
			bass,
			snare_hit * 0.45,
			hat,
			drop_amt * 0.45,
			blackout,
			brightness,
			life_amount * 0.45,
			breath_phase,
			heartbeat * 0.4,
			mouth_pulse,
			wetness * 0.6,
			goo_motion * 0.5
		)

	if living_face and living_face.has_method("apply_audio"):
		living_face.apply_audio(feat, section)

	var portal_mat := portal.material as ShaderMaterial
	if portal_mat:
		portal_mat.set_shader_parameter("intensity", intensity)
		portal_mat.set_shader_parameter("kick", kick)
		portal_mat.set_shader_parameter("bass", bass)
		portal_mat.set_shader_parameter("hat", hat)
		portal_mat.set_shader_parameter("drop", drop_amt)
		portal_mat.set_shader_parameter("charge", charge)
		portal_mat.set_shader_parameter("blackout", blackout)
		portal_mat.set_shader_parameter("shockwave", shock_t)
		portal_mat.set_shader_parameter("time_scale", 0.48 + intensity * 1.45 + charge * 0.75)
		portal_mat.set_shader_parameter("plate_mix", lerpf(0.32, 0.62, intensity))

	# Aura is an independent "breath body" behind the logo.
	if aura:
		var aura_breathe := 1.0 + (breath_phase - 0.5) * 0.09 + bass * 0.08 + drop_amt * 0.12
		aura.scale = Vector2(10.2, 6.9) * aura_breathe
		var aura_alpha := clampf(0.06 + intensity * 0.10 + drop_amt * 0.10 + heartbeat * 0.025, 0.035, 0.24)
		aura.modulate = Color(
			0.28 + drop_amt * 0.28,
			0.70 + brightness * 0.18,
			1.0,
			aura_alpha * (1.0 - blackout * 0.65)
		)

	if glitter:
		glitter.amount_ratio = clampf(0.18 + hat * 0.82, 0.12, 1.0)
		glitter.speed_scale = 0.65 + intensity * 0.9
		glitter.emitting = hat > 0.035 and blackout < 0.86
		var gp := glitter.process_material as ParticleProcessMaterial
		if gp:
			gp.color = Color(1.0, 0.85, 0.4, clampf(0.20 + hat, 0.0, 1.0))

	if breath_mist:
		breath_mist.amount_ratio = clampf(0.22 + breath_phase * 0.28 + bass * 0.34, 0.12, 0.86)
		breath_mist.speed_scale = 0.55 + intensity * 0.65
		breath_mist.modulate.a = (0.34 + bass * 0.28) * (1.0 - blackout * 0.72)

	if drool_mist:
		drool_mist.amount_ratio = clampf(0.12 + mouth_pulse * 0.28 + intensity * 0.16, 0.08, 0.56)
		drool_mist.speed_scale = 0.7 + bass * 0.45
		drool_mist.modulate.a = (0.38 + wetness * 0.18) * (1.0 - blackout * 0.72)

	if shock_ring:
		shock_ring.visible = shock_t > 0.0 and shock_t < 1.0
		shock_ring.scale = Vector2.ONE * (0.35 + shock_t * 3.2)
		shock_ring.modulate.a = (1.0 - shock_t) * maxf(drop_amt, 0.35)

	features_applied.emit(feat)


func _apply_logo_mat(
	node: Sprite2D,
	intensity: float,
	kick: float,
	bass: float,
	snare_hit: float,
	hat: float,
	drop_amt: float,
	blackout: float,
	brightness: float,
	life_amount: float,
	breath_phase: float,
	heartbeat: float,
	mouth_pulse: float,
	wetness: float,
	goo_motion: float
) -> void:
	var logo_mat := node.material as ShaderMaterial
	if logo_mat == null:
		return
	logo_mat.set_shader_parameter("intensity", intensity)
	logo_mat.set_shader_parameter("kick", kick)
	logo_mat.set_shader_parameter("bass", bass)
	logo_mat.set_shader_parameter("snare", snare_hit)
	logo_mat.set_shader_parameter("hat", hat)
	logo_mat.set_shader_parameter("drop", drop_amt)
	logo_mat.set_shader_parameter("blackout", blackout)
	logo_mat.set_shader_parameter(
		"plasma_flow",
		clampf(0.26 + brightness * 0.58 + intensity * 0.36, 0.0, 1.0)
	)
	logo_mat.set_shader_parameter("parallax", bass * 0.011 - kick * 0.004)
	logo_mat.set_shader_parameter("shockwave", shock_t)
	logo_mat.set_shader_parameter("life", life_amount)
	logo_mat.set_shader_parameter("breath_phase", breath_phase)
	logo_mat.set_shader_parameter("heartbeat", heartbeat)
	logo_mat.set_shader_parameter("mouth_pulse", mouth_pulse)
	logo_mat.set_shader_parameter("wetness", wetness)
	logo_mat.set_shader_parameter("goo_motion", goo_motion)


func _heartbeat_pulse(t: float) -> float:
	# Two short pulses followed by a longer rest: subtle organic heartbeat.
	var phase := fmod(t, 1.48)
	var first := pow(maxf(0.0, 1.0 - absf(phase - 0.10) / 0.085), 3.0)
	var second := pow(maxf(0.0, 1.0 - absf(phase - 0.25) / 0.10), 3.0) * 0.62
	return clampf(maxf(first, second), 0.0, 1.0)


func _burst_spit() -> void:
	if spit:
		spit.restart()
		spit.emitting = true


func _process(delta: float) -> void:
	_life_time += delta
	section_blend = minf(1.0, section_blend + delta * 2.5)
	if shock_t > 0.0:
		var speed := 1.6
		if section in ["DROP", "SECOND_DROP"]:
			speed = 2.6
		shock_t = minf(1.0, shock_t + delta * speed)
		if shock_t >= 1.0:
			shock_t = 0.0

	# Keep the monster visibly alive before the first audio frame arrives.
	if _last_features.is_empty():
		apply_audio(
			{
				"intensity": 0.16,
				"kick_energy": 0.0,
				"bass_energy": 0.05,
				"snare_energy": 0.0,
				"hat_energy": 0.025,
				"drop_probability": 0.0,
				"spectral_brightness": 0.22,
			},
			section
		)
