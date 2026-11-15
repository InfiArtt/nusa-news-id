# detik.py
#
# A news provider: the category pages of one site and the pattern of its article links.

from ..models import NewsItem
from .baseProvider import BaseProvider
from .htmlProvider import parse_html_feed


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
		"Disabilitas": "https://www.detik.com/tag/disabilitas",
	}

	# Regex matching absolute URLs of individual news articles (discarding menus/tags)
	# Example: https://news.detik.com/berita/d-7356241/peringatan-dini-cuaca
	html_regex = r"detik\.com/[a-z\-/]+/d-\d+"

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
