# winpoin.py
#
# WinPoin (winpoin.com), news about Windows and Microsoft. Technology only.

from .baseProvider import BaseProvider, CategorySource


class WinPoinProvider(BaseProvider):
	source_name = "WinPoin"
	base_url = "https://winpoin.com"
	# Articles are one slug below the root: https://winpoin.com/microsoft-365-down-berjam-jam/
	article_pattern = r"winpoin\.com/[a-z0-9]+(?:-[a-z0-9]+){2,}/?$"
	categories = {
		"Teknologi": CategorySource(rss="https://winpoin.com/feed/", html="https://winpoin.com/"),
	}
