# -*- coding: utf-8 -*-
# sourceManager.py
#
# Documentation Compliance Notes:
# - Python 3.13 compliant typing.
# - Decouples provider modules from the background MonitorThread.
# Threading Notes:
# - poll_sources() is called exclusively from the background MonitorThread.
# - Aggregates outputs safely before returning them to the main thread queue.
# Lifecycle Notes:
# - Instantiated during GlobalPlugin startup or settings reloads.
# Design Explanation:
# - Serves as a registry mapping source names to their respective provider instances.
# - Iterates through active source-category combinations and fetches items defensively.

import logHandler
from typing import List
from ..models import NewsItem

# Registry of source providers
from .antara import AntaraProvider
from .kompas import KompasProvider
from .detik import DetikProvider
from .republika import RepublikaProvider
from .liputan6 import Liputan6Provider
from .merdeka import MerdekaProvider
from .cnn import CNNProvider
from .winpoin import WinPoinProvider
from .macpoin import MacPoinProvider

class SourceManager:
	"""Orchestrates news fetching across all configured Indonesian providers."""
	def __init__(self):
		self.providers = {
			"Antara": AntaraProvider(),
			"Kompas": KompasProvider(),
			"Detik": DetikProvider(),
			"Republika": RepublikaProvider(),
			"Liputan6": Liputan6Provider(),
			"Merdeka": MerdekaProvider(),
			"CNN Indonesia": CNNProvider(),
			"WinPoin": WinPoinProvider(),
			"MacPoin": MacPoinProvider(),
		}

	def poll_sources(self, enabled_sources: List[str], enabled_categories: List[str], bypass_ssl: bool = False) -> List[NewsItem]:
		"""
		Polls all enabled sources and categories sequentially.
		"""
		aggregated_news = []
		
		for source_name in enabled_sources:
			provider = self.providers.get(source_name)
			if not provider:
				logHandler.log.warning(f"NusaNews: Provider {source_name} is enabled but not registered.")
				continue
				
			for category in enabled_categories:
				try:
					logHandler.log.debug(f"NusaNews: Polling {source_name} for category {category}")
					items = provider.fetch_news(category, bypass_ssl=bypass_ssl)
					if items:
						aggregated_news.extend(items)
				except Exception as e:
					# Catch errors defensively so a failure in one provider doesn't stall the loop
					logHandler.log.error(
						f"NusaNews: Exception raised while polling {source_name} - {category}: {e}"
					)
					
		return aggregated_news
