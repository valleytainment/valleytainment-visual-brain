shader_type canvas_item;

uniform float intensity : hint_range(0.0, 1.0) = 0.2;
uniform float kick : hint_range(0.0, 1.0) = 0.0;
uniform float bass : hint_range(0.0, 1.0) = 0.0;
uniform float hat : hint_range(0.0, 1.0) = 0.0;
uniform float drop : hint_range(0.0, 1.0) = 0.0;
uniform float charge : hint_range(0.0, 1.0) = 0.0;
uniform float blackout : hint_range(0.0, 1.0) = 0.0;
uniform float shockwave : hint_range(0.0, 1.0) = 0.0;
uniform float time_scale : hint_range(0.1, 4.0) = 1.0;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

void fragment() {
	vec2 uv = UV * 2.0 - 1.0;
	uv.x *= SCREEN_PIXEL_SIZE.y / max(SCREEN_PIXEL_SIZE.x, 1e-5);
	float t = TIME * time_scale;

	float r = length(uv);
	float a = atan(uv.y, uv.x);

	// Portal interior — forward tunnel through cosmic void
	float zoom = 0.55 + charge * 0.35 + drop * 0.5 + kick * 0.08;
	float tunnel = fract(1.2 / max(r * (1.15 - bass * 0.2), 0.08) + t * (0.2 + intensity * 0.7 + charge * 0.4));
	float rings = smoothstep(0.2, 0.0, abs(tunnel - 0.5));
	float spokes = pow(abs(sin(a * (5.0 + intensity * 8.0) + t)), 8.0);

	vec3 deep = vec3(0.01, 0.01, 0.04);
	vec3 gold = vec3(1.0, 0.78, 0.28);
	vec3 plasma = 0.5 + 0.5 * cos(vec3(0.0, 2.094, 4.188) + t + tunnel * 6.28 + drop);

	vec3 col = deep;
	col = mix(col, plasma * 0.55, rings * (0.25 + intensity * 0.55));
	col = mix(col, gold, spokes * 0.12 * (0.3 + kick));
	col += plasma * hat * 0.08 * step(0.97, hash(floor(uv * 60.0 + t)));

	// Build charge glow at rim
	float rim = smoothstep(0.35, 1.2, r);
	col += gold * rim * charge * 0.45;

	// Shockwave ring on drop
	float sw = abs(r - shockwave * 1.4);
	col += (gold * 0.7 + plasma * 0.5) * smoothstep(0.06, 0.0, sw) * shockwave;

	// Vignette + blackout
	col *= smoothstep(1.45, 0.25, r) * (1.0 - blackout * 0.95);
	col *= 0.55 + intensity * 0.7;

	COLOR = vec4(col, 1.0);
}
