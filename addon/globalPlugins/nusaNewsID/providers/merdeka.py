# merdeka.py
#
# Merdeka (merdeka.com). It has no feed, so every category reads a page.
# The section is the first part of the article path.

from .baseProvider import BaseProvider, CategorySource

_SITE = "https://www.merdeka.com"


class MerdekaProvider(BaseProvider):
	source_name = "Merdeka"
	base_url = _SITE
	# Example: https://www.merdeka.com/peristiwa/read/8335388/anwar-hafid-tegaskan-dukungan-sulteng
	article_pattern = r"merdeka\.com/[a-z0-9\-]+/read/\d+/[a-z0-9\-]+"
	categories = {
		"Nasional": CategorySource(html=f"{_SITE}/peristiwa/", sections=r"merdeka\.com/peristiwa/"),
		"Internasional": CategorySource(html=f"{_SITE}/dunia/", sections=r"merdeka\.com/dunia/"),
		"Teknologi": CategorySource(html=f"{_SITE}/teknologi/", sections=r"merdeka\.com/teknologi/"),
		"Politik": CategorySource(html=f"{_SITE}/politik/", sections=r"merdeka\.com/politik/"),
		"Ekonomi": CategorySource(html=f"{_SITE}/uang/", sections=r"merdeka\.com/uang/"),
		# The older bolasport and olahraga sections are no longer updated.
		"Olahraga": CategorySource(
			html=(f"{_SITE}/sepakbola/", f"{_SITE}/sport/"), sections=r"merdeka\.com/(?:sepakbola|sport)/"
		),
		"Entertainment": CategorySource(html=f"{_SITE}/artis/", sections=r"merdeka\.com/artis/"),
		"Disabilitas": CategorySource(html=f"{_SITE}/tag/disabilitas/"),
	}
