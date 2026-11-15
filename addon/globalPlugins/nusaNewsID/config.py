# config.py
#
# The add-on's settings in NVDA's configuration, section nusaNewsID.

import config

CONFIG_SECTION = "nusaNewsID"

# Configuration schema defining NusaNews options, defaults, and bounds
config_spec = {
	"refresh_interval": "integer(default=5, min=2, max=1440)",
	"notification_mode": "string(default='digest')",
	"enabled_sources": (
		"string_list(default=list('Detik', 'Kompas', 'Antara', 'Republika', 'Liputan6', 'Merdeka', "
		"'CNN Indonesia', 'WinPoin'))"
	),
	"category_filter": (
		"string_list(default=list('Nasional', 'Internasional', 'Teknologi', 'Politik', 'Ekonomi', "
		"'Olahraga', 'Entertainment', 'Disabilitas'))"
	),
	"silent_hours_enabled": "boolean(default=false)",
	"silent_hours_start": "string(default='22:00')",
	"silent_hours_end": "string(default='06:00')",
	"verbosity_mode": "string(default='full')",
	"cache_duration": "integer(default=7, min=1, max=30)",
	"notification_tone": "boolean(default=true)",
	"breaking_news_preference": "boolean(default=true)",
	"bypass_ssl_verification": "boolean(default=false)",
	"max_display_count": "integer(default=50, min=20, max=100)",
}


def initialize_config():
	"""Registers the NusaNews configuration specification dynamically in NVDA's core confspec."""
	try:
		# Update global configuration schema
		config.conf.spec[CONFIG_SECTION] = config_spec
	except Exception as e:
		import logHandler

		logHandler.log.error(f"NusaNews: Failed to register configuration spec: {e}")


def get_config_val(key):
	"""Reads a value from the core configuration system with fallback handling."""
	try:
		# Access config.conf dictionary structure
		val = config.conf[CONFIG_SECTION][key]
		# Explicitly cast to prevent type issues (e.g. unvalidated string configs)
		if key in {"refresh_interval", "cache_duration", "max_display_count"}:
			return int(val)
		if key in {
			"silent_hours_enabled",
			"notification_tone",
			"breaking_news_preference",
			"bypass_ssl_verification",
		}:
			if isinstance(val, str):
				return val.lower() == "true"
			return bool(val)
		return val
	except Exception:
		# Fallback defaults in case the spec is not loaded or registry fails
		fallbacks = {
			"refresh_interval": 5,
			"notification_mode": "digest",
			"enabled_sources": [
				"Detik",
				"Kompas",
				"Antara",
				"Republika",
				"Liputan6",
				"Merdeka",
				"CNN Indonesia",
				"WinPoin",
			],
			"category_filter": [
				"Nasional",
				"Internasional",
				"Teknologi",
				"Politik",
				"Ekonomi",
				"Olahraga",
				"Entertainment",
				"Disabilitas",
			],
			"silent_hours_enabled": False,
			"silent_hours_start": "22:00",
			"silent_hours_end": "06:00",
			"verbosity_mode": "full",
			"cache_duration": 7,
			"notification_tone": True,
			"breaking_news_preference": True,
			"bypass_ssl_verification": False,
			"max_display_count": 50,
		}
		return fallbacks.get(key)


def read_settings() -> dict:
	"""Copy every setting into a plain dict, for the background thread. Call on the main thread only.

	Sources that no longer exist, such as Tempo from older versions, are left out.
	"""
	from .providers.sourceManager import SOURCE_NAMES

	settings = {key: get_config_val(key) for key in config_spec}
	settings["enabled_sources"] = [name for name in settings["enabled_sources"] if name in SOURCE_NAMES]
	settings["category_filter"] = list(settings["category_filter"])
	return settings


def set_config_val(key, val):
	"""Writes a value to the configuration system."""
	try:
		config.conf[CONFIG_SECTION][key] = val
	except Exception as e:
		import logHandler

		logHandler.log.error(f"NusaNews: Failed to save config key {key}: {e}")
