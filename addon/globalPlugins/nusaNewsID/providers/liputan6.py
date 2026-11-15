# liputan6.py
#
# Liputan6 (liputan6.com). Every section has a feed, including one for disability news.

from .baseProvider import BaseProvider, CategorySource

_SITE = "https://www.liputan6.com"
_FEEDS = "https://feed.liputan6.com/rss"


class Liputan6Provider(BaseProvider):
	source_name = "Liputan6"
	base_url = _SITE
	# Example: https://www.liputan6.com/tekno/read/8334617/bocoran-spesifikasi-vivo-x500s
	article_pattern = r"liputan6\.com/[a-z0-9\-]+/read/\d+/"
	categories = {
		"Nasional": CategorySource(
			rss=f"{_FEEDS}/news", html=f"{_SITE}/news", sections=r"liputan6\.com/news/"
		),
		"Internasional": CategorySource(
			rss=f"{_FEEDS}/global", html=f"{_SITE}/global", sections=r"liputan6\.com/global/"
		),
		"Teknologi": CategorySource(
			rss=f"{_FEEDS}/tekno", html=f"{_SITE}/tekno", sections=r"liputan6\.com/tekno/"
		),
		"Politik": CategorySource(
			rss=f"{_FEEDS}/news/politik", html=f"{_SITE}/news/politik", sections=r"liputan6\.com/news/"
		),
		"Ekonomi": CategorySource(
			rss=f"{_FEEDS}/bisnis", html=f"{_SITE}/bisnis", sections=r"liputan6\.com/bisnis/"
		),
		"Olahraga": CategorySource(
			rss=f"{_FEEDS}/bola", html=f"{_SITE}/bola", sections=r"liputan6\.com/bola/"
		),
		"Entertainment": CategorySource(
			rss=f"{_FEEDS}/showbiz", html=f"{_SITE}/showbiz", sections=r"liputan6\.com/showbiz/"
		),
		"Disabilitas": CategorySource(rss=f"{_FEEDS}/disabilitas", html=f"{_SITE}/disabilitas", curated=True),
	}
