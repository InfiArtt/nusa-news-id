# macpoin.py
#
# A news provider: the category pages of one site and the pattern of its article links.

from ..models import NewsItem
from .baseProvider import BaseProvider
from .htmlProvider import parse_html_feed


class MacPoinProvider(BaseProvider):
	"""Provider implementation for MacPoin Tech News (macpoin.com)."""

	source_name = "MacPoin"

	# Endpoint URLs for HTML Fallbacks (only active for Teknologi/Disabilitas)
	html_urls = {"Teknologi": "https://macpoin.com/", "Disabilitas": "https://macpoin.com/"}

	# Regex matching absolute URLs of individual news articles (macpoin.com/slug/)
	html_regex = r"macpoin\.com/[a-zA-Z0-9\-]+/"

	def fetch_news(self, category: str, bypass_ssl: bool = False) -> list[NewsItem]:
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
			"/category/",
			"/tag/",
			"/page/",
			"/about",
			"/contact",
			"/feed",
			"/wp-content",
			"/wp-json",
			"/author/",
			"macpoin.com/privacy",
			"macpoin.com/redaksi",
			"macpoin.com/iklan",
			"macpoin.com/disclaimer",
			"macpoin.com/panduan",
		}

		for item in items:
			url_lower = item.url.lower()

			# Ensure it is a valid article link and not in exclusions
			if any(exc in url_lower for exc in exclusions):
				continue

			# Ensure it is not the homepage link
			if url_lower == "https://macpoin.com/" or url_lower == "https://macpoin.com":
				continue

			if category == "Disabilitas" and not self._is_disabilitas_relevant(item.title):
				continue

			if item.url not in seen_urls:
				seen_urls.add(item.url)
				is_breaking = self._check_breaking(item.title)
				final_items.append(
					NewsItem(
						title=item.title,
						source=item.source,
						url=item.url,
						guid=item.guid,
						category=item.category,
						summary=item.summary,
						content=item.content,
						published_at=item.published_at,
						is_breaking=is_breaking,
					)
				)

		return final_items
