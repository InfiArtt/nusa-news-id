# detik.py
#
# Detik (detik.com). Each subsite has a feed; international news and the disability tag use pages.

from .baseProvider import BaseProvider, CategorySource


class DetikProvider(BaseProvider):
	source_name = "Detik"
	base_url = "https://www.detik.com"
	# Example: https://news.detik.com/berita/d-8750894/2-nama-cawapres-pengganti-gibran
	article_pattern = r"detik\.com/[a-z0-9\-/]+/d-\d+"
	categories = {
		"Nasional": CategorySource(
			rss="https://news.detik.com/berita/rss",
			html="https://news.detik.com/berita",
			sections=r"news\.detik\.com/berita/",
		),
		"Internasional": CategorySource(
			html="https://news.detik.com/internasional", sections=r"news\.detik\.com/internasional/"
		),
		"Teknologi": CategorySource(rss="https://inet.detik.com/rss", html="https://inet.detik.com"),
		"Ekonomi": CategorySource(rss="https://finance.detik.com/rss", html="https://finance.detik.com"),
		"Olahraga": CategorySource(rss="https://sport.detik.com/rss", html="https://sport.detik.com"),
		"Entertainment": CategorySource(rss="https://hot.detik.com/rss", html="https://hot.detik.com"),
		"Disabilitas": CategorySource(html="https://www.detik.com/tag/disabilitas"),
	}
	# Politics is left out: Detik has no politics section, and its election feed is not kept up to date.
