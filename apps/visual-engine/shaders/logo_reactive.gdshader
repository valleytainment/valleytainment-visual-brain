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

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	vec2 uv = UV;
	// Bass breathing / dimensional warp
	vec2 center = vec2(0.5, 0.52);
	vec2 from_c = uv - center;
	float breathe = 1.0 + bass * 0.045 + kick * 0.02;
	uv = center + from_c / breathe + vec2(parallax, bass * 0.012);

	// Drop radial eruption distortion
	float r = length(from_c);
	float wave = abs(r - shockwave * 0.85);
	uv += normalize(from_c + 1e-5) * smoothstep(0.08, 0.0, wave) * shockwave * 0.04;

	vec4 tex = texture(TEXTURE, uv);
	if (tex.a < 0.04) {
		discard;
	}

	vec3 col = tex.rgb;

	// Rainbow plasma flow on saturated pixels (slime / tongue / letter fill)
	float sat = max(col.r, max(col.g, col.b)) - min(col.r, min(col.g, col.b));
	float hue_shift = TIME * (0.15 + plasma_flow * 0.55) + r * 2.0;
	vec3 plasma = 0.5 + 0.5 * cos(vec3(0.0, 2.0, 4.0) + hue_shift + col.r * 6.0);
	col = mix(col, clamp(col * 0.55 + plasma * 0.55, 0.0, 1.0), sat * plasma_flow * (0.35 + intensity * 0.5));

	// Snare → gold / teeth flash (boost warm channel)
	float gold_flash = snare * snare;
	col = mix(col, vec3(1.0, 0.85, 0.35), gold_flash * 0.55);

	// Hats → glitter emission
	float glitter = step(0.992 - hat * 0.05, hash(floor(uv * 180.0) + floor(TIME * 12.0)));
	col += vec3(glitter) * (0.35 + hat * 0.9);

	// Kick edge punch
	col *= 1.0 + kick * 0.12;

	// Drop cosmic boost
	col = mix(col, col * vec3(1.2, 0.9, 1.35) + plasma * 0.25, drop * 0.55);

	// Pre-drop vacuum / blackout
	col *= 1.0 - blackout * 0.92;

	COLOR = vec4(col, tex.a);
}
