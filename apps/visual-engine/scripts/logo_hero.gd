extends Node2D
## Valleytainment monster-logo hero scene — canonical audio-reactive benchmark.

signal features_applied(features: Dictionary)

@onready var portal: ColorRect = $PortalLayer/Portal
@onready var logo: Sprite2D = $LogoLayer/Logo
@onready var glitter: GPUParticles2D = $LogoLayer/Glitter
@onready var shock_ring: Node2D = $FXLayer/ShockRing

var base_logo_scale: Vector2 = Vector2.ONE
var shock_t: float = 0.0
var last_kick: float = 0.0
var last_snare: float = 0.0
var section: String = "INTRO"


func _ready() -> void:
	base_logo_scale = logo.scale
	if glitter:
		glitter.emitting = true


func apply_audio(feat: Dictionary, section_label: String) -> void:
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
		blackout = lerpf(0.15, 0.75, clampf(intensity, 0.0, 1.0))

	var charge := 0.0
	if is_build:
		charge = clampf(intensity * 1.1, 0.0, 1.0)

	var drop_amt := 1.0 if is_drop else clampf(drop_p * intensity, 0.0, 1.0)

	# Kick onset → trigger shockwave on drop / heavy hits
	if is_drop and kick > 0.72 and last_kick < 0.55:
		shock_t = 0.001
	elif kick > 0.85 and last_kick < 0.5 and intensity > 0.7:
		shock_t = 0.001
	last_kick = kick

	var snare_hit := snare
	if snare > 0.55 and last_snare < 0.35:
		snare_hit = minf(1.0, snare + 0.45)
	last_snare = snare

	# Logo: ~1–2% kick pulse + bass breathing scale
	var pulse := 1.0 + kick * 0.018 + bass * 0.028
	if is_drop:
		pulse += kick * 0.012
	logo.scale = base_logo_scale * pulse
	logo.rotation = sin(Time.get_ticks_msec() * 0.0015) * bass * 0.015

	var logo_mat := logo.material as ShaderMaterial
	if logo_mat:
		logo_mat.set_shader_parameter("intensity", intensity)
		logo_mat.set_shader_parameter("kick", kick)
		logo_mat.set_shader_parameter("bass", bass)
		logo_mat.set_shader_parameter("snare", snare_hit)
		logo_mat.set_shader_parameter("hat", hat)
		logo_mat.set_shader_parameter("drop", drop_amt)
		logo_mat.set_shader_parameter("blackout", blackout)
		logo_mat.set_shader_parameter(
			"plasma_flow",
			clampf(0.25 + brightness * 0.6 + intensity * 0.35, 0.0, 1.0)
		)
		logo_mat.set_shader_parameter("parallax", bass * 0.012 - kick * 0.004)
		logo_mat.set_shader_parameter("shockwave", shock_t)

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

	if glitter:
		glitter.amount = int(lerpf(12.0, 64.0, hat))
		glitter.emitting = hat > 0.08 and blackout < 0.8
		var gp := glitter.process_material as ParticleProcessMaterial
		if gp:
			gp.color = Color(1.0, 0.85, 0.4, clampf(0.2 + hat, 0.0, 1.0))

	if shock_ring:
		shock_ring.visible = shock_t > 0.0 and shock_t < 1.0
		shock_ring.scale = Vector2.ONE * (0.4 + shock_t * 2.4)
		shock_ring.modulate.a = (1.0 - shock_t) * drop_amt

	features_applied.emit(feat)


func _process(delta: float) -> void:
	if shock_t > 0.0:
		var speed := 1.6
		if section in ["DROP", "SECOND_DROP"]:
			speed = 2.4
		shock_t = minf(1.0, shock_t + delta * speed)
		if shock_t >= 1.0:
			shock_t = 0.0
