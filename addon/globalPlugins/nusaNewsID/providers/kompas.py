# kompas.py
#
# A news provider: the category pages of one site and the pattern of its article links.

from ..models import NewsItem
from .baseProvider import BaseProvider
from .htmlProvider import parse_html_feed


class KompasProvider(BaseProvider):
	"""Provider implementation for Kompas News (kompas.com)."""

	source_name = "Kompas"

	# Endpoint URLs for HTML Fallbacks
	html_urls = {
		"Nasional": "https://news.kompas.com",
		"Internasional": "https://internasional.kompas.com",
		"Teknologi": "https://tekno.kompas.com",
		"Politik": "https://nasional.kompas.com",
		"Ekonomi": "https://money.kompas.com",
		"Olahraga": "https://bola.kompas.com",
		"Entertainment": "https://entertainment.kompas.com",
		"Disabilitas": "https://www.kompas.com/tag/disabilitas",
	}

	# Regex matching absolute URLs of individual news articles (discarding menus/tags)
	# Example: https://nasional.kompas.com/read/2026/05/24/221526312/peringatan-dini-cuaca
	html_regex = r"kompas\.com/read/\d+/\d+/\d+/\d+"

	def fetch_news(self, category: str, bypass_ssl: bool = False) -> list[NewsItem]:
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
