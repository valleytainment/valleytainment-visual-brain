shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, filter_linear_mipmap;
uniform float bloom : hint_range(0.0, 2.0) = 0.4;
uniform float chromatic : hint_range(0.0, 1.0) = 0.0;
uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform float vignette : hint_range(0.0, 1.0) = 0.35;

void fragment() {
	vec2 uv = SCREEN_UV;
	vec2 center = uv - 0.5;
	float aberr = chromatic * 0.004;

	float r = texture(screen_texture, uv + center * aberr).r;
	float g = texture(screen_texture, uv).g;
	float b = texture(screen_texture, uv - center * aberr).b;
	vec3 col = vec3(r, g, b);

	// Cheap bloom: sample bright neighbors
	vec3 blur = texture(screen_texture, uv + vec2(0.002, 0.0)).rgb;
	blur += texture(screen_texture, uv + vec2(-0.002, 0.0)).rgb;
	blur += texture(screen_texture, uv + vec2(0.0, 0.002)).rgb;
	blur += texture(screen_texture, uv + vec2(0.0, -0.002)).rgb;
	blur *= 0.25;
	float lum = dot(blur, vec3(0.299, 0.587, 0.114));
	col += blur * bloom * smoothstep(0.35, 0.9, lum);

	col += vec3(1.0, 0.92, 0.75) * flash * 0.35;
	float v = smoothstep(0.95, 0.2, length(center) * (1.0 + vignette));
	col *= mix(1.0, v, vignette);

	COLOR = vec4(col, 1.0);
}
