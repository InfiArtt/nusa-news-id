# models.py
#
# NewsItem, one story from a news site.

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
	published_at: str | None = None  # Expected ISO format string
	is_breaking: bool = False
	seen: bool = field(default=False, compare=False)

	def format_announcement(self) -> str:
		"""Formats the news item for consistent screen reader speech and braille announcements."""
		prefix = "BREAKING NEWS: " if self.is_breaking else ""
		return f"{prefix}{self.source}, Kategori {self.category}: {self.title}"
