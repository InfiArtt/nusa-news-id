# baseProvider.py
#
# The base class of the news providers.

from ..models import NewsItem


class BaseProvider:
	"""Abstract base class representing an Indonesian news source provider."""

	source_name: str = ""
	# Set by SourceManager: ends retries and waits when NVDA stops or the add-on is reloaded.
	stop_event = None

	def fetch_news(self, category: str, bypass_ssl: bool = False) -> list[NewsItem]:
		"""Abstract method to fetch and parse news items. Must be overridden by subclasses."""
		raise NotImplementedError("Subclasses must implement fetch_news")

	def _check_breaking(self, title: str) -> bool:
		"""Deterministically checks if a news headline is breaking based on standard Indonesian keywords."""
		breaking_keywords = [
			"gempa",
			"tsunami",
			"presiden",
			"darurat",
			"bencana",
			"breaking",
			"urgent",
			"waspada",
			"meletus",
			"teroris",
		]
		title_lower = title.lower()
		return any(word in title_lower for word in breaking_keywords)

	def _is_disabilitas_relevant(self, title: str) -> bool:
		"""Checks if a title is relevant to disabilities using a comprehensive keyword list."""
		keywords = [
			"disabilitas",
			"difabel",
			"tunanetra",
			"tunarungu",
			"tunadaksa",
			"tunawicara",
			"tunagrahita",
			"tunalaras",
			"autis",
			"autisme",
			"braille",
			"slb",
			"inklusi",
			"inklusif",
			"kursi roda",
			"penyandang disabilitas",
			"ramah disabilitas",
			"tuli",
			"bisu",
			"buta",
			"lumpuh",
			"cacat",
			"down syndrome",
			"asperger",
			"adhd",
			"cerebral palsy",
			"berkebutuhan khusus",
			"gangguan jiwa",
			"disabilitas fisik",
			"disabilitas intelektual",
			"disabilitas mental",
			"disabilitas sensorik",
			"alat bantu dengar",
			"kaki palsu",
			"tangan palsu",
			"ramah difabel",
			"aksesibilitas",
			"aksesibel",
			"bahasa isyarat",
			"panti sosial",
			"rehabilitasi sosial",
			"sekolah luar biasa",
			"disabilitas netra",
			"disabilitas rungu",
			"disabilitas daksa",
			"disabilitas wicara",
			"disabilitas grahita",
		]
		title_lower = title.lower()
		return any(word in title_lower for word in keywords)

	def _request_http(self, url: str, bypass_ssl: bool = False, timeout: int = 10) -> bytes | None:
		"""
		Helper method performing HTTP GET requests.
		Delegates to networkUtils.fetch_http_data to avoid circular dependencies.
		"""
		from ..networkUtils import fetch_http_data

		return fetch_http_data(url, bypass_ssl, timeout, stop_event=self.stop_event)
