# configSpec.py
#
# The specification of the add-on's settings, section nusaNewsID in NVDA's configuration.
# No imports, so installTasks.py can load it while the add-on is being installed.
# The section name and keys must not change: installed copies would lose their settings.

CONFIG_SECTION = "nusaNewsID"

# Version of the add-on's saved data. 1: version 1.1.0 marked the stories cached by older versions as read.
DATA_VERSION = 1

CONFIG_SPEC: dict[str, str] = {
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
	"data_version": "integer(default=0, min=0)",
	"reader_zoom": "integer(default=100, min=50, max=400)",
	# Where the news list and the reader were last: x, y, width, height and 1 when maximized.
	"list_window": "int_list(default=list())",
	"reader_window": "int_list(default=list())",
}
