# antara.py
#
# Antara (antaranews.com). Its feeds per section are used when they are fresh; its category pages otherwise.

from .baseProvider import BaseProvider, CategorySource

_SITE = "https://www.antaranews.com"


class AntaraProvider(BaseProvider):
	source_name = "Antara"
	base_url = _SITE
	# Example: https://www.antaranews.com/berita/5854403/presiden-instruksikan-minimal-70-persen-hasil-iup
	article_pattern = r"antaranews\.com/berita/\d+/"
	# Links tagged with a utm_campaign are the "top news" and "popular" boxes, shown on every category page.
	deny_pattern = r"utm_campaign="
	categories = {
		"Nasional": CategorySource(html=f"{_SITE}/nasional"),
		"Internasional": CategorySource(rss=f"{_SITE}/rss/dunia.xml", html=f"{_SITE}/dunia"),
		"Teknologi": CategorySource(rss=f"{_SITE}/rss/tekno.xml", html=f"{_SITE}/tekno"),
		"Politik": CategorySource(rss=f"{_SITE}/rss/politik.xml", html=f"{_SITE}/politik"),
		"Ekonomi": CategorySource(rss=f"{_SITE}/rss/ekonomi.xml", html=f"{_SITE}/ekonomi"),
		"Olahraga": CategorySource(rss=f"{_SITE}/rss/olahraga.xml", html=f"{_SITE}/olahraga"),
		"Entertainment": CategorySource(rss=f"{_SITE}/rss/hiburan.xml", html=f"{_SITE}/hiburan"),
		"Disabilitas": CategorySource(html=f"{_SITE}/tag/disabilitas"),
	}
