# liputan6.py
#
# A news provider: the category pages of one site and the pattern of its article links.

from ..models import NewsItem
from .baseProvider import BaseProvider
from .htmlProvider import parse_html_feed


class Liputan6Provider(BaseProvider):
	"""Provider implementation for Liputan6 News (liputan6.com)."""

	source_name = "Liputan6"

	# Endpoint URLs for HTML Fallbacks
	html_urls = {
		"Nasional": "https://www.liputan6.com/news",
		"Internasional": "https://www.liputan6.com/global",
		"Teknologi": "https://www.liputan6.com/tekno",
		"Politik": "https://www.liputan6.com/news/politik",
		"Ekonomi": "https://www.liputan6.com/bisnis",
		"Olahraga": "https://www.liputan6.com/bola",
		"Entertainment": "https://www.liputan6.com/showbiz",
		"Disabilitas": "https://www.liputan6.com/tag/disabilitas",
	}

	# Regex matching absolute URLs of individual news articles (discarding menus/tags)
	# Example: https://www.liputan6.com/news/read/5600293/judul-berita
	html_regex = r"liputan6\.com/[a-zA-Z0-9\-]+/read/\d+/"

	def fetch_news(self, category: str, bypass_ssl: bool = False) -> list[NewsItem]:
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
