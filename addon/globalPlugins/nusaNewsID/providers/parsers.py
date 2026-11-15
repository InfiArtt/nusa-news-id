# parsers.py
#
# Turn an RSS feed or a category page into a list of found stories.
# No NVDA imports, so the tests can use it directly.

import re
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urlunsplit

from .textUtils import looks_like_date, parse_date


@dataclass
class FoundStory:
	"""A story as found on a page or in a feed, before the provider's rules are applied."""

	title: str
	url: str
	published: datetime | None = None
	summary: str | None = None


def normalize_url(url: str) -> str:
	"""Drop the query and fragment, which sites use for tracking (Antara's utm_campaign)."""
	parts = urlsplit(url.strip())
	return urlunsplit((parts.scheme or "https", parts.netloc.lower(), parts.path, "", ""))


def _decode(data: bytes) -> str:
	try:
		return data.decode("utf-8")
	except UnicodeDecodeError:
		return data.decode("cp1252", errors="replace")


def parse_rss(data: bytes, reference: datetime | None = None) -> list[FoundStory]:
	"""Read the items of an RSS 2.0 feed. A broken feed gives an empty list."""
	try:
		root = ElementTree.fromstring(data)
	except ElementTree.ParseError:
		return []
	stories: list[FoundStory] = []
	for item in root.iter("item"):
		title = (item.findtext("title") or "").strip()
		link = (item.findtext("link") or item.findtext("guid") or "").strip()
		if not title or not link.startswith("http"):
			continue
		summary = re.sub(r"<[^>]+>", " ", item.findtext("description") or "")
		stories.append(
			FoundStory(
				title=title,
				url=normalize_url(link),
				published=parse_date(item.findtext("pubDate"), reference),
				summary=re.sub(r"\s+", " ", summary).strip() or None,
			)
		)
	return stories


# Elements that start a new piece of text inside a link, so a card's kanal name, date and title stay apart.
_BLOCK_TAGS = {
	"div",
	"p",
	"span",
	"li",
	"ul",
	"h1",
	"h2",
	"h3",
	"h4",
	"h5",
	"h6",
	"time",
	"br",
	"figure",
	"figcaption",
	"section",
	"article",
	"header",
}
_HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_SKIPPED = {"script", "style", "noscript", "template", "svg"}
# Sidebars, menus and footers list stories from other sections ("Terkini", "Populer"), not this category.
_OUTSIDE_CONTENT = {"aside", "nav", "footer"}


class _LinkCollector(HTMLParser):
	"""Collects article links in page order, with title candidates and the date markers between them."""

	def __init__(self, base_url: str, link_pattern: re.Pattern, deny_pattern: re.Pattern | None):
		super().__init__(convert_charrefs=True)
		self.base_url = base_url
		self.link_pattern = link_pattern
		self.deny_pattern = deny_pattern
		# Each event is ("link", url) when an article link opens, or ("date", text) for a date marker.
		self.events: list[tuple[str, str]] = []
		# Title candidates per url: (priority, text). Lower priority wins.
		self.titles: dict[str, list[tuple[int, str]]] = {}
		self._current_url: str | None = None
		self._chunks: list[str] = []
		self._chunk: list[str] = []
		self._heading_depth = 0
		self._heading: list[str] = []
		self._skip_depth = 0
		self._outside_depth = 0
		self._time_open = False

	def _add_title(self, url: str, priority: int, text: str) -> None:
		text = re.sub(r"\s+", " ", text).strip()
		if text:
			self.titles.setdefault(url, []).append((priority, text))

	def _end_chunk(self) -> None:
		text = "".join(self._chunk).strip()
		if text:
			self._chunks.append(text)
		self._chunk = []

	def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
		if tag in _SKIPPED:
			self._skip_depth += 1
			return
		if tag in _OUTSIDE_CONTENT:
			self._outside_depth += 1
			return
		attributes = {name: value or "" for name, value in attrs}
		for name in ("datetime", "d-time", "data-timestamp", "data-date", "data-publish-date"):
			if attributes.get(name):
				self.events.append(("date", attributes[name]))
		if tag == "time":
			self._time_open = True
		if tag == "a":
			href = attributes.get("href", "").strip()
			url = urljoin(self.base_url, href) if href else ""
			if (
				not self._outside_depth
				and url.startswith("http")
				and self.link_pattern.search(url)
				and not (self.deny_pattern and self.deny_pattern.search(url))
			):
				self._current_url = normalize_url(url)
				self._chunks = []
				self._chunk = []
				self.events.append(("link", self._current_url))
				for name in ("title", "dtr-ttl"):
					if attributes.get(name):
						self._add_title(self._current_url, 1, attributes[name])
			return
		if self._current_url is None:
			return
		if tag in _BLOCK_TAGS:
			self._end_chunk()
		if tag in _HEADINGS:
			self._heading_depth += 1
		if tag == "img" and attributes.get("alt"):
			self._add_title(self._current_url, 3, attributes["alt"])

	def handle_endtag(self, tag: str) -> None:
		if tag in _SKIPPED:
			self._skip_depth = max(0, self._skip_depth - 1)
			return
		if tag in _OUTSIDE_CONTENT:
			self._outside_depth = max(0, self._outside_depth - 1)
			return
		if tag == "time":
			self._time_open = False
		if self._current_url is None:
			return
		if tag in _HEADINGS and self._heading_depth:
			self._heading_depth -= 1
			if not self._heading_depth:
				self._add_title(self._current_url, 0, "".join(self._heading))
				self._heading = []
		if tag in _BLOCK_TAGS:
			self._end_chunk()
		if tag == "a":
			self._end_chunk()
			# The longest piece of text that is not a date is usually the title.
			pieces = [chunk for chunk in self._chunks if not looks_like_date(chunk)]
			if pieces:
				self._add_title(self._current_url, 2, max(pieces, key=len))
			self._current_url = None
			self._heading_depth = 0
			self._heading = []

	def handle_data(self, data: str) -> None:
		if self._skip_depth:
			return
		if self._time_open or (data.strip() and looks_like_date(data) and len(data.strip()) < 60):
			self.events.append(("date", data.strip()))
		if self._current_url is None:
			return
		self._chunk.append(data)
		if self._heading_depth:
			self._heading.append(data)


def parse_html_links(
	data: bytes,
	base_url: str,
	link_pattern: str,
	deny_pattern: str | None = None,
	reference: datetime | None = None,
) -> list[FoundStory]:
	"""Find the article links of a category page, in page order, each with its best title and date.

	A story's date is the first date marker after the story's first link and before the next story's
	first link, which is how the cards of every site are laid out.
	"""
	collector = _LinkCollector(
		base_url, re.compile(link_pattern), re.compile(deny_pattern) if deny_pattern else None
	)
	try:
		collector.feed(_decode(data))
		collector.close()
	except Exception:
		# HTMLParser rarely fails; keep what was found.
		pass
	order: list[str] = []
	dates: dict[str, datetime | None] = {}
	current: str | None = None
	for kind, value in collector.events:
		if kind == "link":
			if value not in dates:
				order.append(value)
				dates[value] = None
				current = value
			elif value != current:
				# A second link to an earlier story (a sidebar) must not take the next story's date.
				current = None
		elif current is not None and dates[current] is None:
			dates[current] = parse_date(value, reference)
	stories: list[FoundStory] = []
	for url in order:
		candidates = sorted(collector.titles.get(url, []), key=lambda candidate: candidate[0])
		if not candidates:
			continue
		stories.append(FoundStory(title=candidates[0][1], url=url, published=dates[url]))
	return stories
