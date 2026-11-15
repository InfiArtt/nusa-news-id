# models.py
#
# NewsItem, one story from a news site. How it is read out is in formatting.py.

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NewsItem:
	title: str
	source: str
	url: str
	guid: str
	category: str
	summary: str | None = None
	content: str | None = None
	# When the site published it, as an ISO 8601 time with its zone, or None when the site gives no time.
	published_at: str | None = None
	is_breaking: bool = False
	seen: bool = field(default=False, compare=False)
	# When the add-on first found it (the cache's cached_at), for stories without a publication time.
	found_at: str | None = field(default=None, compare=False)
	# Who wrote it, when the source says so (InfiArtt).
	author: str | None = field(default=None, compare=False)
