# baseProvider.py
#
# The base class of the news providers. It does all the work the same way for every site:
# download, read RSS or HTML, clean titles, read dates, check the category, drop old and duplicate stories,
# and mark breaking news. A provider only describes its site with data.

import re
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..models import NewsItem
from .parsers import FoundStory, parse_html_links, parse_rss
from .textUtils import WIB, clean_title, is_about_disability, is_breaking, now

# Shorter "titles" are menu entries or labels, not headlines.
MIN_TITLE_LENGTH = 15
# A feed with fewer recent stories than this is topped up from the category pages.
MIN_FEED_STORIES = 5
DISABILITY_CATEGORY = "Disabilitas"


@dataclass(frozen=True)
class CategorySource:
	"""Where a provider finds one category.

	rss: a feed URL, tried first.
	html: one category page or several, read when there is no feed, or the feed fails or gives fewer than
		MIN_FEED_STORIES recent stories (some feeds are only updated now and then).
	sections: a pattern the article URL must match for this category, so links to other sections
		on the same page (a sidebar of popular stories) are left out.
	curated: the source only lists stories about the category (a disability feed), so no keyword check.
	"""

	rss: str | None = None
	html: str | tuple[str, ...] | None = None
	sections: str | None = None
	curated: bool = False

	@property
	def pages(self) -> tuple[str, ...]:
		if not self.html:
			return ()
		return (self.html,) if isinstance(self.html, str) else self.html


class BaseProvider:
	"""A news site. Subclasses set the class attributes below and nothing else."""

	source_name: str = ""
	# The site's address, for links written without it.
	base_url: str = ""
	# A pattern every article link on the site's pages matches, and one for links to leave out.
	article_pattern: str = ""
	deny_pattern: str | None = None
	# A pattern that finds the publication time in an article URL, for sites that put it there.
	# Its groups are year, month, day and optionally hour, minute and second.
	url_date_pattern: str | None = None
	# Patterns for text the site puts around its titles, removed from every title.
	title_noise: tuple[str, ...] = ()
	categories: dict[str, CategorySource] = {}

	# Set by SourceManager: ends retries and waits when NVDA stops or the add-on is reloaded.
	stop_event: threading.Event | None = None

	def fetch_news(self, category: str, bypass_ssl: bool = False, max_age_days: int = 7) -> list[NewsItem]:
		"""The stories of one category, newest site order first. Empty when the site has no such category."""
		source = self.categories.get(category)
		if source is None:
			return []
		reference = now()
		oldest = reference - timedelta(days=max_age_days)
		found: list[FoundStory] = []
		if source.rss:
			data = self._request_http(source.rss, bypass_ssl)
			if data:
				found = parse_rss(data, reference)
		stories = self._accept(found, category, source, oldest)
		if len(stories) >= MIN_FEED_STORIES:
			return stories
		for page in source.pages:
			if self._stopped():
				break
			data = self._request_http(page, bypass_ssl)
			if data:
				found.extend(
					parse_html_links(
						data, self.base_url or page, self.article_pattern, self.deny_pattern, reference
					)
				)
		return self._accept(found, category, source, oldest)

	def _stopped(self) -> bool:
		return self.stop_event is not None and self.stop_event.is_set()

	def _accept(
		self,
		found: list[FoundStory],
		category: str,
		source: CategorySource,
		oldest: datetime,
	) -> list[NewsItem]:
		"""Apply the same rules to every source's stories."""
		sections = re.compile(source.sections) if source.sections else None
		seen: set[str] = set()
		items: list[NewsItem] = []
		for story in found:
			if story.url in seen:
				continue
			if sections and not sections.search(story.url):
				continue
			title = clean_title(story.title, self.title_noise)
			if len(title) < MIN_TITLE_LENGTH:
				continue
			published = self._date_from_url(story.url) or story.published
			if published is not None and published < oldest:
				continue
			if (
				category == DISABILITY_CATEGORY
				and not source.curated
				and not is_about_disability(f"{title} {story.summary or ''}")
			):
				continue
			seen.add(story.url)
			items.append(
				NewsItem(
					title=title,
					source=self.source_name,
					url=story.url,
					guid=story.url,
					category=category,
					summary=story.summary,
					published_at=published.isoformat(timespec="seconds") if published else None,
					is_breaking=is_breaking(title),
				)
			)
		return items

	def _date_from_url(self, url: str) -> datetime | None:
		if not self.url_date_pattern:
			return None
		match = re.search(self.url_date_pattern, url)
		if not match:
			return None
		parts = [int(part) for part in match.groups() if part]
		try:
			return datetime(*parts, tzinfo=WIB)
		except (TypeError, ValueError):
			return None

	def _request_http(self, url: str, bypass_ssl: bool = False, timeout: int = 10) -> bytes | None:
		from ..networkUtils import fetch_http_data

		return fetch_http_data(url, bypass_ssl, timeout, stop_event=self.stop_event)
