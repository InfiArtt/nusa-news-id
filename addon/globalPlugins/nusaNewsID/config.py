# config.py
#
# The add-on's settings in NVDA's configuration, section nusaNewsID.

import config
import logHandler

from .configSpec import CONFIG_SECTION, CONFIG_SPEC

# Kept for the code that used the old name.
config_spec = CONFIG_SPEC


def initialize_config() -> None:
	"""Make the settings section known to NVDA.

	From NVDA 2026.3 the section is registered with config.configSections as base only: it is the same
	in every configuration profile, and NVDA loads it at start. installTasks registers it on install;
	this registers it too for copies installed before. Until NVDA restarts, and on older NVDA versions,
	the section is added to the running configuration as before.
	"""
	try:
		from config import configSections
	except ImportError:
		configSections = None
	registered = (
		getattr(configSections, "_customSections", {}).get(CONFIG_SECTION) if configSections else None
	)
	if configSections is not None and (registered or {}).get("spec") != CONFIG_SPEC:
		# Not registered yet, or registered by a version with other settings.
		try:
			configSections.registerSection(CONFIG_SECTION, CONFIG_SPEC, isBaseOnly=True)
		except Exception:
			logHandler.log.exception("NusaNews: Registering the settings section failed.")
	# The running configuration gets this version's specification, which may have new settings.
	try:
		config.conf.spec[CONFIG_SECTION] = CONFIG_SPEC
	except Exception:
		logHandler.log.exception("NusaNews: Adding the settings section failed.")


def get_config_val(key):
	"""Reads a value from the core configuration system with fallback handling."""
	try:
		# Access config.conf dictionary structure
		val = config.conf[CONFIG_SECTION][key]
		# Explicitly cast to prevent type issues (e.g. unvalidated string configs)
		if key in {"refresh_interval", "cache_duration", "max_display_count", "data_version", "reader_zoom"}:
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
			"data_version": 0,
			"reader_zoom": 100,
		}
		return fallbacks.get(key)


def read_settings() -> dict:
	"""Copy every setting into a plain dict, for the background thread. Call on the main thread only.

	Sources that no longer exist, such as Tempo from older versions, are left out.
	"""
	from .providers.sourceManager import SOURCE_NAMES

	settings = {key: get_config_val(key) for key in CONFIG_SPEC}
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
