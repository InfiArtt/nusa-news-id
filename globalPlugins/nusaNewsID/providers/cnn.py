# -*- coding: utf-8 -*-
# cnn.py
#
# Documentation Compliance Notes:
# - Inherits from BaseProvider and integrates with standard python packages.
# Threading Notes:
# - fetch_news() executes completely within the background MonitorThread context.
# Lifecycle Notes:
# - Executed sequentially during background news aggregation polls.
# Design Explanation:
# - Maps CNN Indonesia news categories to their respective HTML endpoints.
# - Parses feeds using htmlProvider, updating breaking news parameters and filtering disabilitas tag.

import logHandler
from typing import List
from .baseProvider import BaseProvider
from .htmlProvider import parse_html_feed
from ..models import NewsItem

class CNNProvider(BaseProvider):
	"""Provider implementation for CNN Indonesia (cnnindonesia.com)."""
	source_name = "CNN Indonesia"

	# Endpoint URLs for HTML Fallbacks
	html_urls = {
		"Nasional": "https://www.cnnindonesia.com/nasional",
		"Internasional": "https://www.cnnindonesia.com/internasional",
		"Teknologi": "https://www.cnnindonesia.com/teknologi",
		"Politik": "https://www.cnnindonesia.com/nasional/politik",
		"Ekonomi": "https://www.cnnindonesia.com/ekonomi",
		"Olahraga": "https://www.cnnindonesia.com/olahraga",
		"Entertainment": "https://www.cnnindonesia.com/hiburan",
		"Disabilitas": "https://www.cnnindonesia.com/tag/disabilitas"
	}

	# Regex matching absolute URLs of individual news articles (discarding menus/tags)
	# Example: https://www.cnnindonesia.com/nasional/20260525124723-20-1362117/botol-miras-pesta-juara-persib-capai-satu-mobil-pikap-2-orang-tewas
	html_regex = r"cnnindonesia\.com/[a-zA-Z0-9\-]+/\d+-\d+-\d+/"

	def fetch_news(self, category: str, bypass_ssl: bool = False) -> List[NewsItem]:
		items = []
		
		# Trigger HTML Scraping
		html_url = self.html_urls.get(category)
		if html_url:
			html_payload = self._request_http(html_url, bypass_ssl=bypass_ssl)
			if html_payload:
				items = parse_html_feed(self.source_name, category, html_payload, self.html_regex)

		# Post-process breaking news flags and filter off-topic disabilitas items
		final_items = []
		for item in items:
			if category == "Disabilitas" and not self._is_disabilitas_relevant(item.title):
				continue
			
			# Clean up title trailing suffixes if they have "Nasional" or other category names
			title = item.title.strip()
			if title.endswith(" Nasional"):
				title = title[:-9].strip()
			elif title.endswith(" Internasional"):
				title = title[:-14].strip()
			elif title.endswith(" Teknologi"):
				title = title[:-10].strip()
			elif title.endswith(" Ekonomi"):
				title = title[:-8].strip()
			elif title.endswith(" Olahraga"):
				title = title[:-9].strip()
			elif title.endswith(" Hiburan"):
				title = title[:-8].strip()
				
			is_breaking = self._check_breaking(title)
			final_items.append(NewsItem(
				title=title,
				source=item.source,
				url=item.url,
				guid=item.guid,
				category=item.category,
				summary=item.summary,
				content=item.content,
				published_at=item.published_at,
				is_breaking=is_breaking
			))
			
		return final_items
