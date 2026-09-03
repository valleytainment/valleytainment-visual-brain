shader_type canvas_item;
render_mode blend_add;

uniform float strength : hint_range(0.0, 2.0) = 1.0;

void fragment() {
	vec2 p = UV - vec2(0.5);
	float r = length(p);
	float ring = 1.0 - smoothstep(0.018, 0.065, abs(r - 0.39));
	float outer_glow = 1.0 - smoothstep(0.03, 0.16, abs(r - 0.39));
	float angle = atan(p.y, p.x);
	vec3 plasma = 0.5 + 0.5 * cos(vec3(0.0, 2.094, 4.188) + angle * 2.0 + TIME * 2.5);
	vec3 gold = vec3(1.0, 0.74, 0.22);
	vec3 color = mix(gold, plasma, 0.42);
	float alpha = (ring * 0.78 + outer_glow * 0.20) * strength;
	COLOR = vec4(color * (0.85 + ring * 0.65), alpha);
}
