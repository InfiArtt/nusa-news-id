# -*- coding: utf-8 -*-
# detik.py
#
# Documentation Compliance Notes:
# - Inherits from BaseProvider and integrates with standard python packages.
# Threading Notes:
# - fetch_news() executes completely within the background MonitorThread context.
# Lifecycle Notes:
# - Executed sequentially during background news aggregation polls.
# Design Explanation:
# - Maps Detik Indonesian news categories to their respective HTML endpoints.
# - Parses feeds using htmlProvider, updating breaking news parameters.

import logHandler
from typing import List
from .baseProvider import BaseProvider
from .htmlProvider import parse_html_feed
from ..models import NewsItem

class DetikProvider(BaseProvider):
	"""Provider implementation for Detik News (detik.com)."""
	source_name = "Detik"

	# Endpoint URLs for HTML Fallbacks
	html_urls = {
		"Nasional": "https://news.detik.com",
		"Internasional": "https://news.detik.com/internasional",
		"Teknologi": "https://inet.detik.com",
		"Politik": "https://news.detik.com/indeks?tag=politik",
		"Ekonomi": "https://finance.detik.com",
		"Olahraga": "https://sport.detik.com",
		"Entertainment": "https://hot.detik.com",
		"Disabilitas": "https://www.detik.com/tag/disabilitas"
	}

	# Regex matching absolute URLs of individual news articles (discarding menus/tags)
	# Example: https://news.detik.com/berita/d-7356241/peringatan-dini-cuaca
	html_regex = r"detik\.com/[a-z\-/]+/d-\d+"

	def fetch_news(self, category: str, bypass_ssl: bool = False) -> List[NewsItem]:
		items = []
		
		# Trigger HTML Scraping
		html_url = self.html_urls.get(category)
		if html_url:
			html_payload = self._request_http(html_url, bypass_ssl=bypass_ssl)
			if html_payload:
				items = parse_html_feed(self.source_name, category, html_payload, self.html_regex)

		# 3. Post-process breaking news flags using parent helper
		final_items = []
		for item in items:
			if category == "Disabilitas" and not self._is_disabilitas_relevant(item.title):
				continue
			is_breaking = self._check_breaking(item.title)
			final_items.append(NewsItem(
				title=item.title,
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
