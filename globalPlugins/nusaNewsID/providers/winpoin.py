# -*- coding: utf-8 -*-
# winpoin.py
#
# Documentation Compliance Notes:
# - Inherits from BaseProvider and integrates with standard python packages.
# Threading Notes:
# - fetch_news() executes completely within the background MonitorThread context.
# Lifecycle Notes:
# - Executed sequentially during background news aggregation polls.
# Design Explanation:
# - Maps WinPoin technology category to its respective WordPress HTML endpoint.
# - Skips general news categories entirely to keep list relevant.

import logHandler
from typing import List
from .baseProvider import BaseProvider
from .htmlProvider import parse_html_feed
from ..models import NewsItem

class WinPoinProvider(BaseProvider):
	"""Provider implementation for WinPoin Tech News (winpoin.com)."""
	source_name = "WinPoin"

	# Endpoint URLs for HTML Fallbacks (only active for Teknologi/Disabilitas)
	html_urls = {
		"Teknologi": "https://winpoin.com/",
		"Disabilitas": "https://winpoin.com/"
	}

	# Regex matching absolute URLs of individual news articles (winpoin.com/slug/)
	html_regex = r"winpoin\.com/[a-zA-Z0-9\-]+/"

	def fetch_news(self, category: str, bypass_ssl: bool = False) -> List[NewsItem]:
		# Restrict to Teknologi and Disabilitas categories only
		if category not in {"Teknologi", "Disabilitas"}:
			return []

		items = []
		html_url = self.html_urls.get(category)
		if html_url:
			html_payload = self._request_http(html_url, bypass_ssl=bypass_ssl)
			if html_payload:
				items = parse_html_feed(self.source_name, category, html_payload, self.html_regex)

		# Filter out non-article pages and duplicate links
		final_items = []
		seen_urls = set()
		
		# WordPress static page exclusions
		exclusions = {
			"/category/", "/tag/", "/page/", "/about", "/contact",
			"/feed", "/wp-content", "/wp-json", "/author/",
			"winpoin.com/privacy", "winpoin.com/redaksi", "winpoin.com/iklan",
			"winpoin.com/disclaimer", "winpoin.com/panduan"
		}
		
		for item in items:
			url_lower = item.url.lower()
			
			# Ensure it is a valid article link and not in exclusions
			if any(exc in url_lower for exc in exclusions):
				continue
				
			# Ensure it is not the homepage link
			if url_lower == "https://winpoin.com/" or url_lower == "https://winpoin.com":
				continue
				
			if category == "Disabilitas" and not self._is_disabilitas_relevant(item.title):
				continue

			if item.url not in seen_urls:
				seen_urls.add(item.url)
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
