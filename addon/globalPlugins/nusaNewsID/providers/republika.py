# republika.py
#
# Republika (republika.co.id). Feeds for the sections where they are kept up to date, pages for the rest.

from .baseProvider import BaseProvider, CategorySource

_SITE = "https://www.republika.co.id"


class RepublikaProvider(BaseProvider):
	source_name = "Republika"
	base_url = _SITE
	# Example: https://news.republika.co.id/berita/toiefa6030000/menlu-asean-bahas-percepatan
	article_pattern = r"republika\.co\.id/berita/[a-z0-9]+/"
	categories = {
		"Nasional": CategorySource(rss=f"{_SITE}/rss/news/nasional", html=f"{_SITE}/kanal/nasional"),
		"Internasional": CategorySource(
			rss=f"{_SITE}/rss/internasional", html=f"{_SITE}/kanal/internasional"
		),
		"Teknologi": CategorySource(rss=f"{_SITE}/rss/tekno"),
		"Ekonomi": CategorySource(rss=f"{_SITE}/rss/ekonomi", html=f"{_SITE}/kanal/ekonomi"),
		"Olahraga": CategorySource(rss=f"{_SITE}/rss/sport"),
		"Disabilitas": CategorySource(html=f"{_SITE}/tag/disabilitas"),
	}
	# Politics and entertainment are left out: their feeds and pages stopped in 2024 and 2023.
