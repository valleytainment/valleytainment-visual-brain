shader_type canvas_item;

uniform float intensity : hint_range(0.0, 1.0) = 0.2;
uniform float kick : hint_range(0.0, 1.0) = 0.0;
uniform float bass : hint_range(0.0, 1.0) = 0.0;
uniform float hat : hint_range(0.0, 1.0) = 0.0;
uniform float time_scale : hint_range(0.1, 4.0) = 1.0;
uniform float glitch : hint_range(0.0, 1.0) = 0.0;
uniform float chromatic : hint_range(0.0, 1.0) = 0.0;
uniform vec4 color_a : source_color = vec4(0.04, 0.04, 0.08, 1.0);
uniform vec4 color_b : source_color = vec4(1.0, 0.0, 0.235, 1.0);
uniform vec4 color_c : source_color = vec4(0.302, 0.933, 0.918, 1.0);

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	vec2 uv = UV * 2.0 - 1.0;
	uv.x *= SCREEN_PIXEL_SIZE.y / max(SCREEN_PIXEL_SIZE.x, 0.0001);

	float t = TIME * time_scale;
	float r = length(uv);
	float a = atan(uv.y, uv.x);

	// Kick punch scales tunnel
	float zoom = 1.0 + kick * 0.35 + bass * 0.15;
	float tunnel = fract(1.0 / max(r * zoom, 0.05) + t * (0.35 + intensity));
	float ribs = smoothstep(0.15, 0.0, abs(fract(a / 6.28318 * (6.0 + intensity * 10.0) + t * 0.2) - 0.5));

	float pulse = smoothstep(0.8, 0.0, abs(tunnel - (0.5 + bass * 0.2)));
	float sparks = step(0.97 - hat * 0.08, hash(floor(uv * 40.0 + t)));

	vec3 col = mix(color_a.rgb, color_b.rgb, pulse * (0.4 + intensity * 0.6));
	col = mix(col, color_c.rgb, ribs * 0.35 + sparks * 0.5);
	col *= 0.35 + intensity * 0.9;

	// Chromatic / glitch on high intensity
	float gx = (hash(vec2(t, floor(uv.y * 80.0))) - 0.5) * glitch * 0.08;
	col.r += chromatic * 0.15 * sin(t * 20.0 + r * 10.0);
	col.b += chromatic * 0.12 * cos(t * 17.0 + a * 3.0);
	col = mix(col, col.bgr, glitch * 0.35 + abs(gx) * 4.0);

	// Vignette
	col *= smoothstep(1.3, 0.2, r + kick * 0.1);

	COLOR = vec4(col, 1.0);
}
