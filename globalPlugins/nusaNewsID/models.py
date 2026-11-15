# -*- coding: utf-8 -*-
# models.py
#
# Documentation Compliance Notes:
# - Implemented using standard Python 3.13 libraries (dataclasses), ensuring full compatibility with NVDA 2026.1+.
# - Defines a clean, typed model containing all requested news properties.
# Threading Notes:
# - Dataclass is marked as frozen=True to enforce immutability, making it safe to pass between the background MonitorThread and the main thread.
# Lifecycle Notes:
# - Instantiated inside background source providers during fetch parsing.
# - Pushed to the queue, verified against SQLite on the main thread, and consumed by the notification manager and dialog list.
# Design Explanation:
# - Standardizes Indonesian news articles into consistent NewsItem objects. Includes a helper method to format announcements for consistent speech/braille output.

from dataclasses import dataclass, field
from typing import Optional

@dataclass(frozen=True)
class NewsItem:
	title: str
	source: str
	url: str
	guid: str
	category: str
	summary: Optional[str] = None
	content: Optional[str] = None
	published_at: Optional[str] = None  # Expected ISO format string
	is_breaking: bool = False
	seen: bool = field(default=False, compare=False)

	def format_announcement(self) -> str:
		"""Formats the news item for consistent screen reader speech and braille announcements."""
		prefix = "BREAKING NEWS: " if self.is_breaking else ""
		return f"{prefix}{self.source}, Kategori {self.category}: {self.title}"
