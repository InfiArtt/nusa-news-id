# sourceManager.py
#
# The registry of news providers, and the loop that asks each enabled provider for each enabled category.
# poll_sources() runs only in the background MonitorThread.

import threading

import logHandler

from ..models import NewsItem
from .antara import AntaraProvider
from .baseProvider import BaseProvider
from .cnn import CNNProvider
from .detik import DetikProvider
from .infiartt import InfiArttProvider
from .kompas import KompasProvider
from .liputan6 import Liputan6Provider
from .merdeka import MerdekaProvider
from .republika import RepublikaProvider
from .winpoin import WinPoinProvider

# Every provider, in the order the settings panel shows them.
PROVIDER_CLASSES: tuple[type[BaseProvider], ...] = (
	DetikProvider,
	KompasProvider,
	AntaraProvider,
	RepublikaProvider,
	Liputan6Provider,
	MerdekaProvider,
	CNNProvider,
	WinPoinProvider,
)

# Sources that are always checked and cannot be turned off: InfiArtt makes this add-on.
ALWAYS_ON_CLASSES: tuple[type[BaseProvider], ...] = (InfiArttProvider,)
ALWAYS_ON_SOURCES: tuple[str, ...] = tuple(provider.source_name for provider in ALWAYS_ON_CLASSES)

# The categories, in the order the news list offers them. Their names are stored in the cache.
CATEGORIES: tuple[str, ...] = (
	"Nasional",
	"Internasional",
	"Teknologi",
	"Politik",
	"Ekonomi",
	"Olahraga",
	"Entertainment",
	"Disabilitas",
	"Artikel InfiArtt",
	"Pusat Pengetahuan",
)

# The source names that can be turned on and off in the settings.
# Names saved by older versions that are not here, such as Tempo and MacPoin, are ignored.
SOURCE_NAMES: tuple[str, ...] = tuple(provider.source_name for provider in PROVIDER_CLASSES)


def provider_for(source_name: str) -> BaseProvider:
	"""A new provider for a source name, for downloading one article. Unknown names get the generic one."""
	for provider_class in PROVIDER_CLASSES + ALWAYS_ON_CLASSES:
		if provider_class.source_name == source_name:
			return provider_class()
	return BaseProvider()


class SourceManager:
	"""Asks every enabled provider for news, one request at a time."""

	def __init__(self, stop_event: threading.Event | None = None):
		self.stop_event = stop_event
		self.providers: dict[str, BaseProvider] = {}
		for provider_class in PROVIDER_CLASSES + ALWAYS_ON_CLASSES:
			provider = provider_class()
			provider.stop_event = stop_event
			self.providers[provider.source_name] = provider

	def poll_sources(
		self,
		enabled_sources: list[str],
		enabled_categories: list[str],
		bypass_ssl: bool = False,
		max_age_days: int = 7,
	) -> list[NewsItem]:
		"""Fetch every enabled source and category, and every category of the always-on sources.

		Stops early when the stop event is set.
		"""
		aggregated_news: list[NewsItem] = []
		jobs = [(name, enabled_categories) for name in enabled_sources if name not in ALWAYS_ON_SOURCES]
		jobs += [(name, list(self.providers[name].categories)) for name in ALWAYS_ON_SOURCES]
		for source_name, categories in jobs:
			provider = self.providers.get(source_name)
			if provider is None:
				continue
			for category in categories:
				if self.stop_event is not None and self.stop_event.is_set():
					return aggregated_news
				try:
					items = provider.fetch_news(category, bypass_ssl=bypass_ssl, max_age_days=max_age_days)
				except Exception:
					# One broken provider must not stop the others.
					logHandler.log.exception(f"NusaNews: Checking {source_name}, {category} failed.")
					continue
				aggregated_news.extend(items)
		return aggregated_news
