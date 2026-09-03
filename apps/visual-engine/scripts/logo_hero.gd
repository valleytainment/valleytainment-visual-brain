extends Node2D
## Valleytainment monster-logo hero — festival-grade audio-reactive benchmark.

signal features_applied(features: Dictionary)

@onready var portal: ColorRect = $PortalLayer/Portal
@onready var logo: Sprite2D = $LogoLayer/Logo
@onready var ghost_a: Sprite2D = $LogoLayer/LogoGhostA
@onready var ghost_b: Sprite2D = $LogoLayer/LogoGhostB
@onready var glitter: GPUParticles2D = $LogoLayer/Glitter
@onready var shock_ring: Node2D = $FXLayer/ShockRing
@onready var spit: GPUParticles2D = $FXLayer/SpitBurst

var base_logo_scale: Vector2 = Vector2.ONE
var shock_t: float = 0.0
var last_kick: float = 0.0
var last_snare: float = 0.0
var section: String = "INTRO"
var section_blend: float = 1.0
var prev_section: String = "INTRO"


func _ready() -> void:
	base_logo_scale = logo.scale
	if glitter:
		glitter.emitting = true
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
	if section_label != section and section_label != "—":
		prev_section = section
		section = section_label
		section_blend = 0.0
	elif section_label != "—":
		section = section_label

	var intensity := float(feat.get("intensity", 0.2))
	var kick := float(feat.get("kick_energy", 0.0))
	var bass := float(feat.get("bass_energy", 0.0))
	var snare := float(feat.get("snare_energy", 0.0))
	var hat := float(feat.get("hat_energy", 0.0))
	var drop_p := float(feat.get("drop_probability", 0.0))
	var brightness := float(feat.get("spectral_brightness", 0.0))

	var is_drop := section in ["DROP", "SECOND_DROP"]
	var is_build := section in ["BUILD", "PRE_DROP"]
	var blackout := 0.0
	if section == "SILENCE":
		blackout = 0.95
	elif section == "PRE_DROP":
		blackout = lerpf(0.15, 0.85, clampf(intensity, 0.0, 1.0))

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

	var pulse := 1.0 + kick * 0.02 + bass * 0.032
	if is_drop:
		pulse += kick * 0.015
	logo.scale = base_logo_scale * pulse
	logo.rotation = sin(Time.get_ticks_msec() * 0.0015) * bass * 0.018
	logo.modulate.a = lerpf(0.35, 1.0, section_blend)

	# Depth parallax ghosts (pseudo-3D)
	if ghost_a:
		ghost_a.scale = base_logo_scale * (pulse * 1.04 + bass * 0.02)
		ghost_a.position = logo.position + Vector2(-18.0 - bass * 10.0, 8.0 + kick * 4.0)
		ghost_a.modulate = Color(1.0, 0.55, 0.85, 0.18 + hat * 0.12)
		ghost_a.rotation = logo.rotation * 1.2
	if ghost_b:
		ghost_b.scale = base_logo_scale * (pulse * 0.96 - kick * 0.01)
		ghost_b.position = logo.position + Vector2(22.0 + bass * 8.0, -10.0 - bass * 6.0)
		ghost_b.modulate = Color(0.4, 0.95, 1.0, 0.14 + brightness * 0.1)
		ghost_b.rotation = -logo.rotation * 0.8

	_apply_logo_mat(logo, intensity, kick, bass, snare_hit, hat, drop_amt, blackout, brightness)
	if ghost_a:
		_apply_logo_mat(ghost_a, intensity * 0.7, kick, bass, snare_hit * 0.5, hat, drop_amt * 0.5, blackout, brightness)
	if ghost_b:
		_apply_logo_mat(ghost_b, intensity * 0.7, kick, bass, snare_hit * 0.5, hat, drop_amt * 0.5, blackout, brightness)

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
		portal_mat.set_shader_parameter("time_scale", 0.55 + intensity * 1.6 + charge * 0.8)
		portal_mat.set_shader_parameter("plate_mix", lerpf(0.35, 0.65, intensity))

	if glitter:
		glitter.amount = int(lerpf(16.0, 80.0, hat))
		glitter.emitting = hat > 0.06 and blackout < 0.8
		var gp := glitter.process_material as ParticleProcessMaterial
		if gp:
			gp.color = Color(1.0, 0.85, 0.4, clampf(0.25 + hat, 0.0, 1.0))

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
	brightness: float
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
		clampf(0.28 + brightness * 0.6 + intensity * 0.4, 0.0, 1.0)
	)
	logo_mat.set_shader_parameter("parallax", bass * 0.014 - kick * 0.005)
	logo_mat.set_shader_parameter("shockwave", shock_t)


func _burst_spit() -> void:
	if spit:
		spit.restart()
		spit.emitting = true


func _process(delta: float) -> void:
	section_blend = minf(1.0, section_blend + delta * 2.5)
	if shock_t > 0.0:
		var speed := 1.6
		if section in ["DROP", "SECOND_DROP"]:
			speed = 2.6
		shock_t = minf(1.0, shock_t + delta * speed)
		if shock_t >= 1.0:
			shock_t = 0.0
