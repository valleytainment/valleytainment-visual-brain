extends Node
## Optional live FFT bus for Mode B (unknown DJ set).
## Uses the microphone when enabled; otherwise returns silence bands.

var live_enabled: bool = false
var _spectrum: AudioEffectSpectrumAnalyzerInstance
var _bus_idx: int = 0


func _ready() -> void:
	# Safe no-op if mic / bus not configured — prepared-show mode still works.
	pass


func enable_live(enable: bool = true) -> void:
	live_enabled = enable
	if not enable:
		return
	# Expect an AudioEffectSpectrumAnalyzer on the Master bus (index 0) for live mode.
	var effect = AudioServer.get_bus_effect(0, 0)
	if effect is AudioEffectSpectrumAnalyzer:
		_spectrum = AudioServer.get_bus_effect_instance(0, 0)


func is_live() -> bool:
	return live_enabled


func get_bands() -> Dictionary:
	if _spectrum == null:
		return {"kick": 0.0, "bass": 0.0, "mid": 0.0, "hat": 0.0, "loudness": 0.0}
	var kick := _spectrum.get_magnitude_for_frequency_range(40.0, 120.0).length()
	var bass := _spectrum.get_magnitude_for_frequency_range(40.0, 250.0).length()
	var mid := _spectrum.get_magnitude_for_frequency_range(250.0, 4000.0).length()
	var hat := _spectrum.get_magnitude_for_frequency_range(5000.0, 12000.0).length()
	var loud := (kick + bass + mid + hat) * 0.25
	var peak := maxf(0.0001, maxf(kick, maxf(bass, maxf(mid, hat))))
	return {
		"kick": clampf(kick / peak, 0.0, 1.0),
		"bass": clampf(bass / peak, 0.0, 1.0),
		"mid": clampf(mid / peak, 0.0, 1.0),
		"hat": clampf(hat / peak, 0.0, 1.0),
		"loudness": clampf(loud * 8.0, 0.0, 1.0),
	}
