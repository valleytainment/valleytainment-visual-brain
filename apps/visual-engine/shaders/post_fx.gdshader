shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, filter_linear_mipmap;
uniform float bloom : hint_range(0.0, 2.0) = 0.4;
uniform float chromatic : hint_range(0.0, 1.0) = 0.0;
uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform float vignette : hint_range(0.0, 1.0) = 0.35;
uniform float pulse : hint_range(0.0, 1.0) = 0.0;
uniform float drop : hint_range(0.0, 1.0) = 0.0;

void fragment() {
	vec2 uv = SCREEN_UV;
	vec2 center = uv - 0.5;
	float radial = length(center);

	// Very small lens breathing keeps the output cinematic without making the
	// logo unreadable. Drop distortion is capped aggressively for LED use.
	float lens = 1.0 - pulse * 0.0035 - drop * 0.0025;
	uv = 0.5 + center * lens;
	center = uv - 0.5;

	float aberr = chromatic * 0.0032;
	float r = textureLod(screen_texture, uv + center * aberr, 0.0).r;
	float g = textureLod(screen_texture, uv, 0.0).g;
	float b = textureLod(screen_texture, uv - center * aberr, 0.0).b;
	vec3 col = vec3(r, g, b);

	// Mipmap bloom is both smoother and cheaper than many full-resolution taps.
	vec3 blur_near = textureLod(screen_texture, uv, 2.0).rgb;
	vec3 blur_far = textureLod(screen_texture, uv, 4.0).rgb;
	vec3 blur = mix(blur_near, blur_far, 0.38);
	float lum = dot(blur, vec3(0.299, 0.587, 0.114));
	float bright = smoothstep(0.28, 0.92, lum);
	col += blur * bloom * bright * 0.72;

	// Warm impact flash; kept below clipping so gold and rainbow detail survives.
	col += vec3(1.0, 0.92, 0.74) * flash * 0.24;
	col *= 1.0 + pulse * 0.045;

	float v = smoothstep(0.98, 0.18, radial * (1.0 + vignette));
	col *= mix(1.0, v, vignette);

	COLOR = vec4(col, 1.0);
}
