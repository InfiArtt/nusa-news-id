# articleContent.py
#
# Downloads an article page and extracts its text for the reader. Runs in a background thread.

import re
from html.parser import HTMLParser

import logHandler

from ..networkUtils import fetch_http_data


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
