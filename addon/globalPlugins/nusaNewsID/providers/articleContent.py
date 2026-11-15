# articleContent.py
#
# Downloads an article and keeps its readable structure: paragraphs, headings, lists, quotes, links and
# images with a text alternative. Everything else (scripts, ads, menus, "baca juga" boxes, addresses)
# is left out. The result is clean HTML built here from an allow list, never the site's own markup,
# plus a plain text version for copying and for the plain reader.
# No NVDA imports apart from the log, so the tests can use it directly. Runs in a background thread.

import html
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin

import logHandler

from ..networkUtils import fetch_http_data

# Elements whose whole content is left out.
_SKIPPED_TAGS = {
	"head",
	"title",
	"script",
	"style",
	"noscript",
	"template",
	"iframe",
	"svg",
	"form",
	"button",
	"select",
	"aside",
	"nav",
	"footer",
	"header",
	"video",
	"audio",
}
# Class names (or parts of them) of boxes inside articles that are not the article.
_SKIPPED_CLASS_PARTS = (
	"article-desc",
	"article-paragraph",
	"baca-juga",
	"bacajuga",
	"related",
	"terkait",
	"advert",
	"ads-",
	"iklan",
	"share",
	"social",
	"tags",
	"body-tag",
	"newsletter",
	"comment",
	"author-box",
	"video-",
	"parallax",
)
_BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "figcaption", "pre", "dd", "dt"}
_LIST_TAGS = {"ul", "ol"}
# Inline elements kept in the result, with the attributes they may keep.
_INLINE_TAGS = {"a", "strong", "b", "em", "i", "kbd", "code", "sub", "sup", "abbr"}

# Article containers of the sites the add-on reads.
TARGET_CLASSES = {
	"detail__body-text",
	"article__body",
	"detail_text",
	"detail__body",
	"read__content",
	"read-content",
	"post-content",
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
	"articles-content",
}
# Elements that hold a whole page; their class names never mark a box to leave out.
_STRUCTURAL_TAGS = {"html", "body", "main", "article"}

_BOILERPLATE = re.compile(
	r"advertisement|scroll to (?:resume|continue)|^baca juga|^simak juga|^tonton video|^lihat juga|"
	r"halaman selanjutnya|baca selengkapnya|window\.adsbygoogle|copyright|hak cipta|^©|"
	r"^ikuti (?:kami|berita|saluran)|^dapatkan (?:berita|update)|whatsapp channel|google news|"
	r"^dukung kompas\.com|gabung kompas\.com plus|^daftar isi$|^dilarang keras mengambil konten|"
	r"bergantung pada iklan|matikan (?:ad ?block|pemblokir iklan)|"
	r"^(?:jl|jln|jalan)\.?\s.*(?:no\.|rt\.|kec\.|kel\.|kota|jakarta)",
	re.IGNORECASE,
)


@dataclass
class Block:
	"""One part of an article: kind is p, h1 to h6, li-ul, li-ol, blockquote, pre or image."""

	kind: str
	html: str
	text: str


@dataclass
class Article:
	"""A downloaded article, ready for the reader."""

	blocks: list[Block] = field(default_factory=list)
	# The language of the article text, such as "id" or "en".
	language: str = "id"
	# For stories only members can read: a short explanation shown instead of the text.
	locked_note: str | None = None
	summary: str | None = None

	@property
	def text(self) -> str:
		return blocks_text(self.blocks)

	@property
	def html(self) -> str:
		return blocks_html(self.blocks)


def is_boilerplate(text: str) -> bool:
	return bool(_BOILERPLATE.search(text.strip()))


class BlockParser(HTMLParser):
	"""Turns HTML into Blocks.

	With whole_document, everything outside the skipped elements counts; otherwise only the inside of an
	element with one of TARGET_CLASSES. min_length drops short paragraphs, for the generic fallback.
	"""

	def __init__(self, base_url: str, whole_document: bool = False, min_length: int = 0):
		super().__init__(convert_charrefs=True)
		self.base_url = base_url
		self.whole_document = whole_document
		self.min_length = min_length
		self.blocks: list[Block] = []
		self._seen: set[str] = set()
		# One entry per open element: (tag, skipped, opens the article container).
		self._stack: list[tuple[str, bool, bool]] = []
		self._container_depth = 0
		self._skip_depth = 0
		self._lists: list[str] = []
		self._block: str | None = None
		self._html: list[str] = []
		self._text: list[str] = []
		self._open_inline: list[str] = []
		# A dateline such as "Jakarta -" written as its own paragraph, joined to the next paragraph.
		self._dateline: str | None = None
		# Only the first article container that held text counts; later ones are sidebars.
		self._container_done = False

	@property
	def _inside(self) -> bool:
		return (self.whole_document or self._container_depth > 0) and not self._skip_depth

	def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
		attributes = {name: value or "" for name, value in attrs}
		classes = attributes.get("class", "").lower()
		skipped = tag in _SKIPPED_TAGS or (
			tag not in _STRUCTURAL_TAGS
			and (self._inside or self.whole_document)
			and any(part in classes for part in _SKIPPED_CLASS_PARTS)
		)
		container = (
			not self.whole_document
			and not self._container_done
			and self._container_depth == 0
			and (bool(TARGET_CLASSES & set(classes.split())) or attributes.get("itemprop") == "articleBody")
		)
		if tag in ("br", "img", "hr", "input", "meta", "link", "source", "wbr"):
			# Elements without content.
			if self._inside:
				self._void(tag, attributes)
			return
		self._stack.append((tag, skipped, container))
		if skipped:
			self._skip_depth += 1
			return
		if container:
			self._container_depth += 1
		if not self._inside:
			return
		if tag in _LIST_TAGS:
			self._end_block()
			self._lists.append(tag)
		elif tag in _BLOCK_TAGS:
			self._start_block(tag)
		elif tag in _INLINE_TAGS and self._block:
			self._start_inline(tag, attributes)

	def handle_endtag(self, tag: str) -> None:
		if tag not in {entry[0] for entry in self._stack}:
			return
		while self._stack:
			open_tag, skipped, container = self._stack.pop()
			self._close(open_tag, skipped, container)
			if open_tag == tag:
				break

	def _close(self, tag: str, skipped: bool, container: bool) -> None:
		if skipped:
			self._skip_depth -= 1
			return
		if self._inside:
			if tag in _LIST_TAGS:
				self._end_block()
				if self._lists:
					self._lists.pop()
			elif tag in _BLOCK_TAGS:
				self._end_block()
			elif tag in _INLINE_TAGS and tag in self._open_inline:
				self._end_inline(tag)
		if container:
			self._end_block()
			self._container_depth -= 1
			if self.blocks:
				self._container_done = True

	def handle_data(self, data: str) -> None:
		if not self._inside or not data:
			return
		if self._block is None:
			if not data.strip():
				return
			# Text directly inside the container, as some sites write paragraphs without <p>.
			self._start_block("p")
		self._html.append(html.escape(data, quote=False))
		self._text.append(data)

	def close(self) -> None:
		super().close()
		self._end_block()

	def _void(self, tag: str, attributes: dict[str, str]) -> None:
		if tag == "br" and self._block:
			self._html.append("<br>")
			self._text.append("\n")
		elif tag == "img":
			alt = re.sub(r"\s+", " ", attributes.get("alt", "")).strip()
			src = attributes.get("src") or attributes.get("data-src") or attributes.get("data-original", "")
			# An image without a text alternative says nothing to a screen reader user, so it is left out.
			if alt and src and not src.startswith("data:"):
				self._end_block()
				url = html.escape(urljoin(self.base_url, src))
				self._add(Block("image", f'<img src="{url}" alt="{html.escape(alt)}">', alt))

	def _start_block(self, tag: str) -> None:
		self._end_block()
		if tag == "li":
			kind = "li-ol" if self._lists and self._lists[-1] == "ol" else "li-ul"
		elif tag in ("dd", "dt", "figcaption"):
			kind = "p"
		else:
			kind = tag
		self._block = kind
		self._html = []
		self._text = []
		self._open_inline = []

	def _start_inline(self, tag: str, attributes: dict[str, str]) -> None:
		if tag == "b":
			tag = "strong"
		elif tag == "i":
			tag = "em"
		if tag == "a":
			href = attributes.get("href", "").strip()
			if not href or href.startswith(("javascript:", "#", "mailto:", "tel:")):
				return
			self._html.append(f'<a href="{html.escape(urljoin(self.base_url, href))}">')
		elif tag == "abbr" and attributes.get("title"):
			self._html.append(f'<abbr title="{html.escape(attributes["title"])}">')
		else:
			self._html.append(f"<{tag}>")
		self._open_inline.append(tag)

	def _end_inline(self, tag: str) -> None:
		tag = {"b": "strong", "i": "em"}.get(tag, tag)
		if tag in self._open_inline:
			self._open_inline.remove(tag)
			self._html.append(f"</{tag}>")

	def _end_block(self) -> None:
		if self._block is None:
			return
		for tag in reversed(self._open_inline):
			self._html.append(f"</{tag}>")
		kind = self._block
		self._block = None
		text = re.sub(r"[ \t\r\f\v]+", " ", "".join(self._text))
		text = re.sub(r"\s*\n\s*", "\n", text).strip()
		body = re.sub(r"\s+", " ", "".join(self._html)).strip()
		if not text or is_boilerplate(text):
			return
		if kind == "p" and re.fullmatch(r"[A-Z][\w .,()]{1,40}\s(?:-{1,2}|\u2013|\u2014)", text):
			self._dateline = text
			return
		if self._dateline and kind == "p":
			text = f"{self._dateline} {text}"
			body = f"{html.escape(self._dateline, quote=False)} {body}"
			self._dateline = None
		if kind in ("p", "li-ul", "li-ol") and len(text) < self.min_length:
			return
		self._add(Block(kind, body, text))

	def _add(self, block: Block) -> None:
		if block.text in self._seen:
			return
		self._seen.add(block.text)
		self.blocks.append(block)


def parse_blocks(
	markup: str, base_url: str, whole_document: bool = False, min_length: int = 0
) -> list[Block]:
	parser = BlockParser(base_url, whole_document=whole_document, min_length=min_length)
	try:
		parser.feed(markup)
		parser.close()
	except Exception:
		logHandler.log.debugWarning("NusaNews: Parsing an article stopped early.", exc_info=True)
	return parser.blocks


def blocks_html(blocks: list[Block], heading_shift: int = 0) -> str:
	"""The blocks as HTML.

	heading_shift moves every heading down, so an article's h1 can sit below the page title.
	"""
	parts: list[str] = []
	open_list: str | None = None
	for block in blocks:
		list_tag = {"li-ul": "ul", "li-ol": "ol"}.get(block.kind)
		if list_tag != open_list:
			if open_list:
				parts.append(f"</{open_list}>")
			if list_tag:
				parts.append(f"<{list_tag}>")
			open_list = list_tag
		if list_tag:
			parts.append(f"<li>{block.html}</li>")
		elif block.kind == "image":
			parts.append(f"<figure>{block.html}</figure>")
		elif block.kind.startswith("h") and block.kind[1:].isdigit():
			level = min(6, int(block.kind[1:]) + heading_shift)
			parts.append(f"<h{level}>{block.html}</h{level}>")
		else:
			parts.append(f"<{block.kind}>{block.html}</{block.kind}>")
	if open_list:
		parts.append(f"</{open_list}>")
	return "\n".join(parts)


def blocks_text(blocks: list[Block]) -> str:
	"""The blocks as plain text, one paragraph per block, images described by their text alternative."""
	return "\n\n".join(block.text for block in blocks if block.kind != "image")


def blocks_from_text(text: str) -> list[Block]:
	"""Blocks from plain text saved by version 1.1.0 before this change: one paragraph per blank line."""
	return [
		Block("p", html.escape(part.strip(), quote=False), part.strip())
		for part in text.split("\n\n")
		if part.strip()
	]


def _rewrite_url_for_full_article(url: str) -> str:
	"""Ask for the whole article on one page, for sites that split articles."""
	if "detik.com" in url:
		return url + ("&single=1" if "?" in url else "?single=1")
	if "kompas.com" in url:
		return url + ("&page=all" if "?" in url else "?page=all")
	return url


def _decode(data: bytes) -> str:
	try:
		return data.decode("utf-8")
	except UnicodeDecodeError:
		return data.decode("cp1252", errors="replace")


def extract_article(markup: str, url: str) -> Article:
	"""The article inside a page: from its article container, or every long paragraph if none is found."""
	blocks = parse_blocks(markup, url)
	if not blocks:
		blocks = parse_blocks(markup, url, whole_document=True, min_length=40)
	language = "id"
	match = re.search(r"<html[^>]*\blang=[\"']?([A-Za-z]{2})", markup[:2000], re.IGNORECASE)
	if match:
		language = match.group(1).lower()
	return Article(blocks=blocks, language=language)


def fetch_article(url: str, bypass_ssl: bool = False) -> Article | None:
	"""Download a news page and extract its article. None when the download fails or finds no text."""
	data = fetch_http_data(_rewrite_url_for_full_article(url), bypass_ssl=bypass_ssl)
	if not data:
		return None
	article = extract_article(_decode(data), url)
	return article if article.blocks else None
