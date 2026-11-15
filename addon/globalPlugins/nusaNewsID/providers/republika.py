# republika.py
#
# A news provider: the category pages of one site and the pattern of its article links.

from ..models import NewsItem
from .baseProvider import BaseProvider
from .htmlProvider import parse_html_feed


class RepublikaProvider(BaseProvider):
	"""Provider implementation for Republika News (republika.co.id)."""

	source_name = "Republika"

	# Endpoint URLs for HTML Fallbacks
	html_urls = {
		"Nasional": "https://www.republika.co.id/kanal/nasional",
		"Internasional": "https://www.republika.co.id/kanal/internasional",
		"Teknologi": "https://www.republika.co.id/kanal/tekno",
		"Politik": "https://www.republika.co.id/kanal/nasional/politik",
		"Ekonomi": "https://www.republika.co.id/kanal/ekonomi",
		"Olahraga": "https://www.republika.co.id/kanal/sepakbola",
		"Entertainment": "https://www.republika.co.id/kanal/senggang",
		"Disabilitas": "https://www.republika.co.id/tag/disabilitas",
	}

	# Regex matching absolute URLs of individual news articles (discarding menus/tags)
	# Example: https://news.republika.co.id/berita/nasional/politik/s12345/judul-berita
	html_regex = r"republika\.co\.id/berita/[a-zA-Z0-9\-_]+/[a-zA-Z0-9\-_]+"

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
