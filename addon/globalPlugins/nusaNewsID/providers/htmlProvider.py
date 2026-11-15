# htmlProvider.py
#
# HTML parsers: links to stories on category pages, and the text of an article.

import re
from html.parser import HTMLParser

import logHandler

from ..models import NewsItem
from ..networkUtils import fetch_http_data


class NewsHTMLParser(HTMLParser):
	"""State-machine HTML parser that extracts news article links and clean text descriptions."""

	def __init__(self, source_name: str, category: str, url_filter_regex: str = "", base_url: str = ""):
		super().__init__()
		self.source_name = source_name
		self.category = category
		self.url_filter = re.compile(url_filter_regex) if url_filter_regex else None
		self.base_url = base_url

		# Parser state tracking
		self.in_anchor = False
		self.current_url = ""
		self.current_text = []
		self.articles_data = []
		self.date_regex = re.compile(
			r"(?:\d+\s+(?:menit|jam|hari|detik)(?:\s+yang)?\s+lalu|kemarin|\d{1,2}(?:\s*[-/]\s*\d{1,2}\s*[-/]\s*\d{4}|\s+(?:jan|feb|mar|apr|mei|jun|jul|agu|sep|okt|nov|des)[a-z]*\s+\d{4}))",
			re.IGNORECASE,
		)

	def handle_starttag(self, tag, attrs):
		if tag == "a":
			href = None
			for attr, value in attrs:
				if attr == "href":
					href = value
					break
			if href:
				href = href.strip()
				if href.startswith("/") and hasattr(self, "base_url") and self.base_url:
					href = self.base_url + href
				# Only capture links matching the source's news pattern
				if not self.url_filter or self.url_filter.search(href):
					self.in_anchor = True
					self.current_url = href
					self.current_text = []

	def handle_endtag(self, tag):
		if tag == "a" and self.in_anchor:
			self.in_anchor = False
			title = "".join(self.current_text).strip()
			# Clean up formatting, tabs, and duplicate spaces
			title = re.sub(r"\s+", " ", title)

			published_at = None
			if title:
				match = self.date_regex.search(title)
				if match:
					published_at = match.group()
					title = title[: match.start()].strip() + " " + title[match.end() :].strip()
					title = title.strip("-| ")

			# Validation rules (titles must be descriptive, URLs must be absolute)
			if title and len(title) >= 15 and self.current_url.startswith("http"):
				self.articles_data.append(
					{
						"title": title,
						"source": self.source_name,
						"url": self.current_url,
						"guid": self.current_url,
						"category": self.category,
						"published_at": published_at,
					}
				)
			self.current_url = ""
			self.current_text = []

	def handle_data(self, data):
		if self.in_anchor:
			self.current_text.append(data)
		elif self.articles_data and not self.articles_data[-1]["published_at"]:
			data_clean = data.strip()
			if data_clean:
				match = self.date_regex.search(data_clean)
				if match:
					self.articles_data[-1]["published_at"] = data_clean


def parse_html_feed(
	source_name: str, category: str, html_data: bytes, url_filter_regex: str = "", base_url: str = ""
) -> list[NewsItem]:
	"""
	Decodes raw HTML bytes and feeds them into the NewsHTMLParser.
	"""
	if not html_data:
		return []

	try:
		# Use ignore fallback to prevent decoder crashes on invalid byte characters
		html_text = html_data.decode("utf-8", errors="ignore")
		parser = NewsHTMLParser(source_name, category, url_filter_regex, base_url=base_url)
		parser.feed(html_text)

		items = []
		for data in parser.articles_data:
			items.append(
				NewsItem(
					title=data["title"],
					source=data["source"],
					url=data["url"],
					guid=data["guid"],
					category=data["category"],
					published_at=data["published_at"],
				)
			)
		return items
	except Exception as e:
		logHandler.log.error(f"NusaNews: HTML Parser exception on source {source_name}: {e}")
		return []


def _is_boilerplate_text(text: str) -> bool:
	"""Checks if a paragraph is unwanted boilerplate text."""
	text_lower = text.lower()
	return (
		"advertisement" in text_lower
		or "scroll to resume content" in text_lower
		or "scroll to continue with content" in text_lower
		or text_lower.startswith("baca juga")
		or text_lower.startswith("simak juga")
		or text_lower.startswith("tonton video")
		or "halaman selanjutnya" in text_lower
		or "baca selengkapnya" in text_lower
		or "window.adsbygoogle" in text_lower
		or "copyright" in text_lower
	)


def _rewrite_url_for_full_article(url: str) -> str:
	"""Rewrites the URL to single-page/all-pages versions if supported to handle pagination."""
	if "detik.com" in url:
		return url + ("&single=1" if "?" in url else "?single=1")
	elif "kompas.com" in url:
		return url + ("&page=all" if "?" in url else "?page=all")
	return url


class ArticleContentParser(HTMLParser):
	"""Parses article content pages, extracting clean text from target divs."""

	TARGET_CLASSES = {
		"detail__body-text",
		"article__body",
		"detail_text",
		"detail__body",
		"read__content",
		"read-content",
		"post-content",
		"article__entry",
		"wrap__article-detail-content",
		"artikel-desc",
		"artikel-body",
		"article-content-body__item-content",
		"article-content-body__item",
		"article-content-body",
		"mdk-body-news",
		"mdk-body-paragraph",
		"detail-news",
		"text-neutral-1100",
		"detail-text",
		"entry-content",
		"article--version2",
		"article-content",
	}

	def __init__(self):
		super().__init__()
		self.in_content = False
		self.content_depth = -1
		self.depth = 0
		self.in_p = False
		self.ignore_stack = []
		self.current_p = []
		self.paragraphs = []
		self.seen_paragraphs = set()

	def handle_starttag(self, tag, attrs):
		self.depth += 1
		attrs_dict = dict(attrs)
		classes = set(attrs_dict.get("class", "").split())

		is_ignored = (
			tag in {"script", "style", "iframe", "noscript"}
			or "article-desc" in classes
			or "article-paragraph" in classes
			or "article-desc-text" in classes
		)
		self.ignore_stack.append(is_ignored)

		# If we are not inside the content wrapper yet, check if this element is a wrapper
		if not self.in_content and self.TARGET_CLASSES.intersection(classes):
			self.in_content = True
			self.content_depth = self.depth

		if self.in_content and tag == "p":
			self.in_p = True
			self.current_p = []

	def handle_endtag(self, tag):
		is_ignored = self.ignore_stack.pop() if self.ignore_stack else False

		if self.in_content and tag == "p" and self.in_p:
			self.in_p = False
			if not any(self.ignore_stack) and not is_ignored:
				text = "".join(self.current_p).strip()
				text = re.sub(r"\s+", " ", text)
				if text and not _is_boilerplate_text(text) and text not in self.seen_paragraphs:
					self.paragraphs.append(text)
					self.seen_paragraphs.add(text)
			self.current_p = []

		if self.in_content and self.depth == self.content_depth:
			self.in_content = False
			self.content_depth = -1

		self.depth -= 1

	def handle_data(self, data):
		if self.in_p and not any(self.ignore_stack):
			self.current_p.append(data)


class GenericPParser(HTMLParser):
	"""Fallback generic paragraph parser."""

	def __init__(self):
		super().__init__()
		self.in_p = False
		self.ignored_depth = 0
		self.current_p = []
		self.paragraphs = []
		self.seen_paragraphs = set()

	def handle_starttag(self, tag, attrs):
		if tag in {"script", "style", "iframe", "noscript"}:
			self.ignored_depth += 1
		if tag == "p":
			self.in_p = True
			self.current_p = []

	def handle_endtag(self, tag):
		if tag in {"script", "style", "iframe", "noscript"}:
			self.ignored_depth = max(0, self.ignored_depth - 1)
		if tag == "p" and self.in_p:
			self.in_p = False
			text = "".join(self.current_p).strip()
			text = re.sub(r"\s+", " ", text)
			if (
				text
				and len(text) > 40
				and not _is_boilerplate_text(text)
				and text not in self.seen_paragraphs
			):
				self.paragraphs.append(text)
				self.seen_paragraphs.add(text)
			self.current_p = []

	def handle_data(self, data):
		if self.in_p and self.ignored_depth == 0:
			self.current_p.append(data)


def fetch_article_content(url: str, bypass_ssl: bool = False) -> str:
	"""
	Downloads the article HTML from the given URL and parses it to extract body text.
	Rewrites the URL to single-page/all-pages versions if supported.
	Returns the joined paragraph texts or an empty string if failed.
	"""
	url = _rewrite_url_for_full_article(url)

	try:
		html_bytes = fetch_http_data(url, bypass_ssl=bypass_ssl)
		if not html_bytes:
			return ""

		try:
			html_text = html_bytes.decode("utf-8")
		except UnicodeDecodeError:
			html_text = html_bytes.decode("latin-1", errors="replace")

		parser = ArticleContentParser()
		parser.feed(html_text)

		if parser.paragraphs:
			return "\n\n".join(parser.paragraphs)

		# Generic fallback
		generic_parser = GenericPParser()
		generic_parser.feed(html_text)
		if generic_parser.paragraphs:
			return "\n\n".join(generic_parser.paragraphs)

		return ""
	except Exception as e:
		logHandler.log.error(f"NusaNews: Error fetching article content from {url}: {e}")
		return ""
