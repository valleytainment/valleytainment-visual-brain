shader_type canvas_item;

uniform float intensity : hint_range(0.0, 1.0) = 0.2;
uniform float kick : hint_range(0.0, 1.0) = 0.0;
uniform float bass : hint_range(0.0, 1.0) = 0.0;
uniform float snare : hint_range(0.0, 1.0) = 0.0;
uniform float hat : hint_range(0.0, 1.0) = 0.0;
uniform float drop : hint_range(0.0, 1.0) = 0.0;
uniform float blackout : hint_range(0.0, 1.0) = 0.0;
uniform float plasma_flow : hint_range(0.0, 1.0) = 0.35;
uniform float parallax : hint_range(-0.05, 0.05) = 0.0;
uniform float shockwave : hint_range(0.0, 1.0) = 0.0;

// Life controls are intentionally independent from the music so the monster
// keeps breathing, glistening, and moving even during silence.
uniform float life : hint_range(0.0, 1.5) = 0.72;
uniform float breath_phase : hint_range(0.0, 1.0) = 0.5;
uniform float heartbeat : hint_range(0.0, 1.0) = 0.0;
uniform float mouth_pulse : hint_range(0.0, 1.0) = 0.5;
uniform float wetness : hint_range(0.0, 1.5) = 0.8;
uniform float goo_motion : hint_range(0.0, 1.5) = 0.75;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float luma(vec3 c) {
	return dot(c, vec3(0.299, 0.587, 0.114));
}

void fragment() {
	vec2 original_uv = UV;
	vec4 base = texture(TEXTURE, original_uv);
	if (base.a < 0.025) {
		discard;
	}

	float base_sat = max(base.r, max(base.g, base.b)) - min(base.r, min(base.g, base.b));
	float top_slime = (1.0 - smoothstep(0.28, 0.45, original_uv.y)) * smoothstep(0.12, 0.28, base_sat);
	float lower_slime = smoothstep(0.52, 0.82, original_uv.y) * smoothstep(0.10, 0.30, base_sat);
	float tongue = lower_slime
		* smoothstep(0.12, 0.30, original_uv.x)
		* (1.0 - smoothstep(0.78, 0.94, original_uv.x));
	float side_drips = lower_slime
		* (smoothstep(0.58, 0.86, abs(original_uv.x - 0.5) * 2.0));
	float organic_mask = clamp(top_slime * 0.55 + tongue + side_drips * 0.55, 0.0, 1.0);

	vec2 uv = original_uv;

	// Independent organic motion: slow viscous sway rather than generic scaling.
	float living_sway = sin(TIME * 1.05 + original_uv.y * 11.0 + original_uv.x * 4.0);
	float living_lift = cos(TIME * 0.82 + original_uv.x * 10.0);
	uv.x += living_sway * 0.0065 * goo_motion * organic_mask * life;
	uv.y += living_lift * 0.0040 * goo_motion * organic_mask * life;

	// Tongue gets its own heavier, lower-frequency motion.
	uv.x += sin(TIME * 1.36 + original_uv.y * 8.0) * 0.010 * tongue * goo_motion;
	uv.y += cos(TIME * 0.72 + original_uv.x * 7.0) * 0.004 * tongue * goo_motion;

	// Mouth/throat dilation gives the impression of breathing and swallowing.
	vec2 mouth_center = vec2(0.5, 0.575);
	vec2 mouth_delta = uv - mouth_center;
	float mouth_r = length(vec2(mouth_delta.x, mouth_delta.y * 1.65));
	float mouth_zone = (1.0 - smoothstep(0.16, 0.43, mouth_r))
		* smoothstep(0.40, 0.50, original_uv.y)
		* (1.0 - smoothstep(0.78, 0.90, original_uv.y));
	float throat = (mouth_pulse - 0.5) * 0.030 + heartbeat * 0.010 + bass * 0.012;
	uv = mouth_center + mouth_delta * (1.0 - throat * mouth_zone);

	// Whole-creature breath is deliberately subtle so the wordmark remains crisp.
	vec2 center = vec2(0.5, 0.52);
	vec2 from_c = uv - center;
	float breathe = 1.0 + bass * 0.030 + kick * 0.014 + (breath_phase - 0.5) * 0.010 + heartbeat * 0.006;
	uv = center + from_c / breathe + vec2(parallax, bass * 0.008);

	// Drop radial eruption distortion.
	float r = length(original_uv - center);
	float wave = abs(r - shockwave * 0.85);
	uv += normalize((original_uv - center) + vec2(0.00001))
		* smoothstep(0.075, 0.0, wave)
		* shockwave
		* 0.030;
	uv = clamp(uv, vec2(0.001), vec2(0.999));

	vec4 tex = texture(TEXTURE, uv);
	if (tex.a < 0.025) {
		discard;
	}

	vec3 col = tex.rgb;
	float sat = max(col.r, max(col.g, col.b)) - min(col.r, min(col.g, col.b));

	// Moving rainbow plasma stays inside saturated brand regions.
	float hue_shift = TIME * (0.13 + plasma_flow * 0.50) + r * 2.0 + living_sway * 0.12;
	vec3 plasma = 0.5 + 0.5 * cos(vec3(0.0, 2.0, 4.0) + hue_shift + col.r * 6.0);
	col = mix(
		col,
		clamp(col * 0.58 + plasma * 0.52, 0.0, 1.0),
		sat * plasma_flow * (0.30 + intensity * 0.45)
	);

	// Approximate material masks from the source art instead of requiring a
	// second segmentation texture. This keeps the canonical logo immutable.
	float gold_mask = smoothstep(0.62, 0.92, tex.r)
		* smoothstep(0.36, 0.72, tex.g)
		* (1.0 - smoothstep(0.36, 0.62, tex.b));
	float living_surface = clamp(sat * 0.72 + gold_mask * 0.65, 0.0, 1.0);

	// Cheap pseudo-normal from local luminance gradients. It makes the slime and
	// metallic trim catch a moving specular light like a wet 3D sculpture.
	vec2 px = TEXTURE_PIXEL_SIZE * 1.8;
	float ll = luma(texture(TEXTURE, clamp(uv - vec2(px.x, 0.0), vec2(0.001), vec2(0.999))).rgb);
	float lr = luma(texture(TEXTURE, clamp(uv + vec2(px.x, 0.0), vec2(0.001), vec2(0.999))).rgb);
	float lu = luma(texture(TEXTURE, clamp(uv - vec2(0.0, px.y), vec2(0.001), vec2(0.999))).rgb);
	float ld = luma(texture(TEXTURE, clamp(uv + vec2(0.0, px.y), vec2(0.001), vec2(0.999))).rgb);
	vec3 normal = normalize(vec3((ll - lr) * 2.2, (lu - ld) * 2.2, 1.0));
	vec3 light_dir = normalize(vec3(sin(TIME * 0.31) * 0.55, cos(TIME * 0.27) * 0.45, 0.85));
	float ndl = max(dot(normal, light_dir), 0.0);
	float specular = pow(ndl, 18.0) * wetness * living_surface;
	col += vec3(0.78, 0.92, 1.0) * specular * (0.10 + life * 0.18);

	// Wet travelling glints sell viscosity without destroying the original art.
	float wet_glint = pow(max(0.0, sin((uv.x * 1.2 + uv.y) * 34.0 - TIME * 1.7)), 24.0);
	col += vec3(1.0, 0.96, 0.84) * wet_glint * living_surface * wetness * 0.11;

	// Inner alpha edge catches light like a gel/metal bevel.
	float a_l = texture(TEXTURE, clamp(uv - vec2(px.x, 0.0), vec2(0.001), vec2(0.999))).a;
	float a_r = texture(TEXTURE, clamp(uv + vec2(px.x, 0.0), vec2(0.001), vec2(0.999))).a;
	float a_u = texture(TEXTURE, clamp(uv - vec2(0.0, px.y), vec2(0.001), vec2(0.999))).a;
	float a_d = texture(TEXTURE, clamp(uv + vec2(0.0, px.y), vec2(0.001), vec2(0.999))).a;
	float neighbor_alpha = min(min(a_l, a_r), min(a_u, a_d));
	float edge = clamp(tex.a - neighbor_alpha, 0.0, 1.0);
	col += (vec3(1.0, 0.72, 0.22) * gold_mask + plasma * (1.0 - gold_mask))
		* edge
		* (0.24 + intensity * 0.30);

	// Snare flashes the existing warm trim/teeth instead of whitening everything.
	float gold_flash = snare * snare;
	col = mix(col, vec3(1.0, 0.86, 0.38), gold_flash * (0.18 + gold_mask * 0.46));

	// Hats create microscopic living sparkle on the wet material.
	float glitter = step(0.993 - hat * 0.045, hash(floor(uv * 190.0) + floor(TIME * 12.0)));
	col += vec3(glitter) * (0.22 + hat * 0.82) * living_surface;

	// Heartbeat and kick are felt as internal light, not destructive geometry.
	col *= 1.0 + kick * 0.08 + heartbeat * 0.045;
	col += plasma * heartbeat * 0.045 * living_surface;

	// Drop cosmic boost.
	col = mix(col, col * vec3(1.14, 0.96, 1.24) + plasma * 0.20, drop * 0.48);

	// Pre-drop vacuum / blackout.
	col *= 1.0 - blackout * 0.92;

	COLOR = vec4(clamp(col, 0.0, 1.6), tex.a);
}
