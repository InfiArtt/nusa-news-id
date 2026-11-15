# cnn.py
#
# CNN Indonesia (cnnindonesia.com). Every section has a feed; politics and the disability tag use pages.

from .baseProvider import BaseProvider, CategorySource

_SITE = "https://www.cnnindonesia.com"


class CNNProvider(BaseProvider):
	source_name = "CNN Indonesia"
	base_url = _SITE
	# Example: https://www.cnnindonesia.com/nasional/20261114120533-32-1427140/gaduh-gibran-mundur
	article_pattern = r"cnnindonesia\.com/[a-z\-]+/\d{14}-\d+-\d+/"
	# The number after the section is the publication time: 20261114120533 is 14 November 2026, 12:05:33.
	url_date_pattern = r"cnnindonesia\.com/[a-z\-]+/(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})-"
	categories = {
		"Nasional": CategorySource(rss=f"{_SITE}/nasional/rss", html=f"{_SITE}/nasional"),
		"Internasional": CategorySource(rss=f"{_SITE}/internasional/rss", html=f"{_SITE}/internasional"),
		"Teknologi": CategorySource(rss=f"{_SITE}/teknologi/rss", html=f"{_SITE}/teknologi"),
		"Politik": CategorySource(html=f"{_SITE}/nasional/politik", sections=r"cnnindonesia\.com/nasional/"),
		"Ekonomi": CategorySource(rss=f"{_SITE}/ekonomi/rss", html=f"{_SITE}/ekonomi"),
		"Olahraga": CategorySource(rss=f"{_SITE}/olahraga/rss", html=f"{_SITE}/olahraga"),
		"Entertainment": CategorySource(rss=f"{_SITE}/hiburan/rss", html=f"{_SITE}/hiburan"),
		"Disabilitas": CategorySource(html=f"{_SITE}/tag/disabilitas"),
	}
