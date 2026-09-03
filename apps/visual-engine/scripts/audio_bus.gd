extends Node
## Optional live HTTP bridge to vbrain performance API (Mode B).

var live_enabled: bool = false
var api_url: String = "http://127.0.0.1:8765/api/live"
var _http: HTTPRequest
var _bands: Dictionary = {
	"kick": 0.0,
	"bass": 0.0,
	"mid": 0.0,
	"hat": 0.0,
	"loudness": 0.0,
}
var _live_payload: Dictionary = {}
var _poll_accum: float = 0.0
var poll_hz: float = 20.0


func _ready() -> void:
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_request_completed)


func enable_live(enable: bool = true, url: String = "http://127.0.0.1:8765/api/live") -> void:
	live_enabled = enable
	api_url = url
	if enable:
		_request_once()


func is_live() -> bool:
	return live_enabled


func get_bands() -> Dictionary:
	return _bands


func get_live_payload() -> Dictionary:
	return _live_payload


func _process(delta: float) -> void:
	if not live_enabled:
		return
	_poll_accum += delta
	if _poll_accum >= 1.0 / maxf(poll_hz, 1.0):
		_poll_accum = 0.0
		_request_once()


func _request_once() -> void:
	if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		return
	_http.request(api_url)


func _on_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or response_code != 200:
		return
	var data = JSON.parse_string(body.get_string_from_utf8())
	if typeof(data) != TYPE_DICTIONARY:
		return
	_live_payload = data
	_bands = {
		"kick": float(data.get("kick_energy", 0.0)),
		"bass": float(data.get("bass_energy", 0.0)),
		"mid": float(data.get("snare_energy", 0.0)),
		"hat": float(data.get("hat_energy", 0.0)),
		"loudness": float(data.get("loudness", data.get("intensity", 0.0))),
	}
