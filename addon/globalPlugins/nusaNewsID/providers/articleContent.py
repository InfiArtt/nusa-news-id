# articleContent.py
#
# Downloads an article and keeps its readable structure: paragraphs, headings, lists, quotes, links,
# photos with one description, notes where a video was, and posts embedded from social networks.
# Everything else (scripts, ads, menus, "baca juga" boxes, photo credits, buttons such as "Perbesar",
# editors' codes, addresses) is left out. The result is clean HTML built here from an allow list, never
# the site's own markup, plus a plain text version for copying and for the plain reader.
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
	"credit",
)
_BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "figcaption", "pre", "dd", "dt"}
_LIST_TAGS = {"ul", "ol"}
# Inline elements kept in the result, with the attributes they may keep.
_INLINE_TAGS = {"a", "strong", "b", "em", "i", "kbd", "code", "sub", "sup", "abbr"}
# Elements without content.
_VOID_TAGS = {"br", "img", "hr", "input", "meta", "link", "source", "wbr"}

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
	r"bergantung pada iklan|matikan (?:ad ?block|pemblokir iklan)|tampilkan semua$|"
	r"^baca berita terkini|^placeholder$|"
	r"^(?:jl|jln|jalan)\.?\s.*(?:no\.|rt\.|kec\.|kel\.|kota|jakarta)",
	re.IGNORECASE,
)
# Text a page puts in its photo boxes and players: buttons, not part of the story.
_CONTROL_WORDS = re.compile(
	r"^(?:perbesar|lihat foto|lihat galeri|zoom|klik untuk memperbesar|putar video|play|tutup|close|"
	r"placeholder|20d|20detik)$",
	re.IGNORECASE,
)
# A label that introduces a link to another story or video. The block goes, and so do the links and the
# video right after it.
_PROMO_LABEL = re.compile(
	r"^(?:(?:baca|simak|tonton|lihat)(?: juga)?|video(?: pilihan| terkait| top \d+)?|pilihan redaksi|"
	r"berita terkait|artikel terkait|rekomendasi)\s*:|"
	r"^(?:pilihan redaksi|berita terkait|artikel terkait|rekomendasi|terpopuler|video pilihan)$",
	re.IGNORECASE,
)
# Editors' initials at the end of a story, such as "(acd/acd)" or "(inh)".
_EDITOR_CODE = re.compile(r"^\(\s*[a-z]{2,5}(?:\s*/\s*[a-z]{2,5})*\s*\)[\s.]*$", re.IGNORECASE)
_EDITOR_LINE = re.compile(r"^(?:editor|penyunting|redaktur)\s*:", re.IGNORECASE)
# "Oleh Idris Rusadi Putra - Reporter", "Penulis: Nama", "Reporter: Nama".
# "Oleh" alone also starts ordinary sentences ("Oleh karena itu"), so it needs the role after the name.
_NAME = r"[A-Z][\w.']*(?: [A-Z][\w.']*){0,5}"
_BYLINE = re.compile(
	rf"^(?:[Oo]leh\s+(?P<a>{_NAME})\s*[-–—|]\s*(?i:reporter|penulis|kontributor|wartawan)\b.*|"
	rf"(?i:penulis|reporter)\s*:\s*(?P<b>{_NAME}))$"
)
# Photo credits inside captions.
_CREDITS = (
	re.compile(r"^(?:perbesar|lihat foto)\s+", re.IGNORECASE),
	re.compile(r"\s*\((?:foto|dok\.?|dokumentasi|sumber|ilustrasi|photo|istimewa)\b[^)]*\)", re.IGNORECASE),
	re.compile(r"\s*\([^()]*\.(?:com|co\.id|id|net)\b[^()]*\)", re.IGNORECASE),
	re.compile(r"(?:^|\s)(?:foto|dok\.?|dokumentasi|sumber foto|photo|credit|kredit)\s*:.*$", re.IGNORECASE),
	re.compile(r"\s*©.*$"),
)
# Class names of embedded social posts, and the network's name.
_SOCIAL_CLASSES = {
	"twitter-tweet": "X",
	"instagram-media": "Instagram",
	"tiktok-embed": "TikTok",
	"text-post-media": "Threads",
	"fb-post": "Facebook",
}
_VIDEO_SOURCE = re.compile(
	r"youtube|youtu\.be|vidio|dailymotion|vimeo|tiktok|20\.detik|/video|video\.|/tv/|kompas\.tv|player",
	re.IGNORECASE,
)
_VIDEO_BOX = re.compile(r"\bvideo[-_](?:player|embed|wrap|container|box)\b|\bembed[-_]video\b")


@dataclass
class Block:
	"""One part of an article.

	kind is p, h1 to h6, li-ul, li-ol, blockquote, pre, image, video or social.
	- image: html is the <img> with an empty alt; text is its one description (caption or alt), without
	the photo credit.
	- video: a video was here; html and text are empty, the reader says so in the user's language.
	- social: a post from a social network; text is the post, extra is "network|@handle".
	"""

	kind: str
	html: str
	text: str
	extra: str = ""


@dataclass
class Article:
	"""A downloaded article, ready for the reader."""

	blocks: list[Block] = field(default_factory=list)
	# The language of the article text, such as "id" or "en".
	language: str = "id"
	# For stories only members can read: a short explanation shown instead of the text.
	locked_note: str | None = None
	summary: str | None = None
	# The writer named in the article ("Oleh ... - Reporter"), taken out of the text.
	author: str | None = None

	@property
	def text(self) -> str:
		return blocks_text(self.blocks)

	@property
	def html(self) -> str:
		return blocks_html(self.blocks)


def strip_credits(text: str) -> str:
	"""A caption without its photo credit, such as "(Foto: Ady/Liputan6.com)" or a copyright line."""
	for pattern in _CREDITS:
		text = pattern.sub("", text)
	return text.strip(" -|")


def is_boilerplate(text: str) -> bool:
	text = text.strip()
	return bool(
		_BOILERPLATE.search(text)
		or _CONTROL_WORDS.match(text)
		or _EDITOR_CODE.match(text)
		or _EDITOR_LINE.match(text)
	)


def _clean(text: str) -> str:
	return re.sub(r"\s+", " ", text).strip()


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
		self.author: str | None = None
		self._seen: set[str] = set()
		# One entry per open element: (tag, skipped, opens the article container, kind of box it opens).
		self._stack: list[tuple[str, bool, bool, str]] = []
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
		# After a promotion label such as "Baca juga:", the links and the video that follow go too.
		self._after_promo = False
		# Inside a photo box (figure): its first image and its caption become one image block.
		self._figure_depth = 0
		self._figure_image: tuple[str, str] | None = None
		self._caption: list[str] | None = None
		# Inside an embedded social post: (network, collected text).
		self._social: tuple[str, list[str]] | None = None

	@property
	def _inside(self) -> bool:
		return (self.whole_document or self._container_depth > 0) and not self._skip_depth

	def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
		attributes = {name: value or "" for name, value in attrs}
		classes = attributes.get("class", "").lower()
		if self._inside and self._is_video(tag, attributes, classes):
			self._add_video()
		if tag in _VOID_TAGS:
			if self._inside:
				self._void(tag, attributes)
			return
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
		box = ""
		if self._inside and not skipped:
			network = next((name for key, name in _SOCIAL_CLASSES.items() if key in classes.split()), None)
			if tag == "blockquote" and network and self._social is None:
				self._end_block()
				self._social = (network, [])
				box = "social"
			elif tag == "figure":
				self._end_block()
				self._figure_depth += 1
				box = "figure"
			elif self._caption is None and (
				tag == "figcaption" or (self._figure_depth and "caption" in classes)
			):
				self._end_block()
				self._caption = []
				box = "caption"
		self._stack.append((tag, skipped, container, box))
		if skipped:
			self._skip_depth += 1
			return
		if container:
			self._container_depth += 1
		if (
			not self._inside
			or box
			or self._social is not None
			or self._figure_depth
			or self._caption is not None
		):
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
			open_tag, skipped, container, box = self._stack.pop()
			self._close(open_tag, skipped, container, box)
			if open_tag == tag:
				break

	def _close(self, tag: str, skipped: bool, container: bool, box: str) -> None:
		if skipped:
			self._skip_depth -= 1
			return
		if box == "social":
			self._end_social()
		elif box == "caption":
			if not self._figure_depth:
				# A caption outside a photo box describes the image just before it.
				self._caption_for_last_image(" ".join(self._caption or []))
				self._caption = None
		elif box == "figure":
			self._end_figure()
		elif self._inside and self._social is None and not self._figure_depth and self._caption is None:
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
		if self._social is not None:
			self._social[1].append(data)
			return
		if self._caption is not None:
			self._caption.append(data)
			return
		if self._figure_depth:
			# Other text in a photo box is its buttons ("Perbesar") and counters.
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

	@staticmethod
	def _is_video(tag: str, attributes: dict[str, str], classes: str) -> bool:
		if tag == "video":
			return True
		if tag == "iframe":
			return bool(_VIDEO_SOURCE.search(attributes.get("src") or attributes.get("data-src") or ""))
		return tag == "div" and bool(_VIDEO_BOX.search(classes))

	def _add_video(self) -> None:
		self._end_block()
		if self._after_promo or (self.blocks and self.blocks[-1].kind == "video"):
			return
		self.blocks.append(Block("video", "", ""))

	def _void(self, tag: str, attributes: dict[str, str]) -> None:
		if tag == "br" and self._block:
			self._html.append("<br>")
			self._text.append("\n")
		elif tag == "img":
			src = attributes.get("src") or attributes.get("data-src") or attributes.get("data-original", "")
			if not src or src.startswith("data:") or self._social is not None:
				return
			alt = strip_credits(_clean(attributes.get("alt", "")))
			url = html.escape(urljoin(self.base_url, src))
			if self._figure_depth:
				if self._figure_image is None:
					self._figure_image = (url, alt)
				return
			# An image without a description says nothing to a screen reader user, so it is left out.
			if alt and not _CONTROL_WORDS.match(alt):
				self._end_block()
				self._add(Block("image", f'<img src="{url}" alt="">', alt))

	def _end_figure(self) -> None:
		self._figure_depth -= 1
		if self._figure_depth:
			return
		caption = strip_credits(_clean(" ".join(self._caption or [])))
		self._caption = None
		image, self._figure_image = self._figure_image, None
		if not image:
			return
		url, alt = image
		description = caption if caption and not _CONTROL_WORDS.match(caption) else alt
		if description and not _CONTROL_WORDS.match(description):
			self._add(Block("image", f'<img src="{url}" alt="">', description))

	def _caption_for_last_image(self, caption: str) -> None:
		caption = strip_credits(_clean(caption))
		if not caption or _CONTROL_WORDS.match(caption):
			return
		if self.blocks and self.blocks[-1].kind == "image":
			self._seen.discard(self.blocks[-1].text)
			self.blocks[-1].text = caption
			self._seen.add(caption)

	def _end_social(self) -> None:
		network, parts = self._social
		self._social = None
		text = _clean(" ".join(parts))
		handle_match = re.search(r"\(@([\w.]+)\)", text)
		handle = f"@{handle_match.group(1)}" if handle_match else ""
		# The post itself, without its short links and its "- Name (@handle) date" signature.
		text = re.sub(r"\s*[-–—]\s*[^-–—]*\(@[\w.]+\).*$", "", text)
		text = re.sub(r"\s*(?:https?://|pic\.twitter\.com/)\S+", "", text)
		text = re.sub(
			r"^(?:a post shared by|sebuah kiriman dibagikan oleh)\b.*$", "", text, flags=re.IGNORECASE
		)
		text = _clean(text)
		if text:
			self._add(Block("social", html.escape(text, quote=False), text, f"{network}|{handle}"))

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
		body = _clean("".join(self._html))
		if not text:
			return
		if _PROMO_LABEL.match(text):
			self._after_promo = True
			return
		# A block that is one link and nothing else, as promotions after a label are.
		if self._after_promo and re.fullmatch(r"<a [^>]*>.*</a>[.:]?", body) and body.count("<a ") == 1:
			return
		self._after_promo = False
		if is_boilerplate(text):
			return
		byline = _BYLINE.match(text) if kind == "p" and len(text) < 100 else None
		if byline:
			if self.author is None:
				self.author = (byline.group("a") or byline.group("b")).strip()
			return
		if kind == "p" and re.fullmatch(r"[A-Z][\w .,()]{1,40}\s(?:-{1,2}|–|—)", text):
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


def _parse(markup: str, base_url: str, whole_document: bool = False, min_length: int = 0) -> BlockParser:
	parser = BlockParser(base_url, whole_document=whole_document, min_length=min_length)
	try:
		parser.feed(markup)
		parser.close()
	except Exception:
		logHandler.log.debugWarning("NusaNews: Parsing an article stopped early.", exc_info=True)
	return parser


def parse_blocks(
	markup: str, base_url: str, whole_document: bool = False, min_length: int = 0
) -> list[Block]:
	return _parse(markup, base_url, whole_document, min_length).blocks


def _social_label(block: Block, labels: dict[str, str]) -> str:
	network, _sep, handle = block.extra.partition("|")
	if handle:
		return labels["social"].format(network=network, handle=handle)
	return labels["social_no_handle"].format(network=network)


def blocks_html(blocks: list[Block], heading_shift: int = 0, labels: dict[str, str] | None = None) -> str:
	"""The blocks as HTML.

	heading_shift moves every heading down, so an article's h1 can sit below the page title.
	labels holds the reader's words: "image" ({description}), "video", "social" ({network}, {handle}) and
	"social_no_handle" ({network}). Without labels, photos show their description only and video notes
	are left out.
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
			# The image has an empty alt; its description is visible text below it, read once.
			description = labels["image"].format(description=block.text) if labels else block.text
			parts.append(
				f'<div class="figure">{block.html}'
				f'<p class="caption">{html.escape(description, quote=False)}</p></div>'
			)
		elif block.kind == "video":
			if labels:
				parts.append(f'<p class="notice">{html.escape(labels["video"], quote=False)}</p>')
		elif block.kind == "social":
			label = html.escape(_social_label(block, labels), quote=False) if labels else ""
			label_html = f'<p class="label">{label}</p>' if label else ""
			parts.append(f"<blockquote>{label_html}<p>{block.html}</p></blockquote>")
		elif block.kind.startswith("h") and block.kind[1:].isdigit():
			level = min(6, int(block.kind[1:]) + heading_shift)
			parts.append(f"<h{level}>{block.html}</h{level}>")
		else:
			parts.append(f"<{block.kind}>{block.html}</{block.kind}>")
	if open_list:
		parts.append(f"</{open_list}>")
	return "\n".join(parts)


def blocks_text(blocks: list[Block], labels: dict[str, str] | None = None) -> str:
	"""The blocks as plain text, one paragraph per block.

	With labels (see blocks_html), photos, videos and social posts are described; without them, photos
	and videos are left out.
	"""
	parts = []
	for block in blocks:
		if block.kind == "image":
			if labels:
				parts.append(labels["image"].format(description=block.text))
		elif block.kind == "video":
			if labels:
				parts.append(labels["video"])
		elif block.kind == "social" and labels:
			parts.append(f"{_social_label(block, labels)}\n{block.text}")
		else:
			parts.append(block.text)
	return "\n\n".join(parts)


def blocks_to_json(blocks: list[Block]) -> list[dict]:
	return [{"kind": b.kind, "html": b.html, "text": b.text, "extra": b.extra} for b in blocks]


def blocks_from_json(data: list) -> list[Block]:
	return [
		Block(
			str(b.get("kind") or "p"),
			str(b.get("html") or ""),
			str(b.get("text") or ""),
			str(b.get("extra") or ""),
		)
		for b in data
		if isinstance(b, dict)
	]


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


def _meta(markup: str, names: tuple[str, ...]) -> str | None:
	"""The content of the first of these meta tags (name or property) that the page has."""
	tags = re.findall(r"<meta\b[^>]*>", markup[:100000], re.IGNORECASE)
	for name in names:
		for tag in tags:
			key = re.search(r"\b(?:name|property)\s*=\s*[\"']([^\"']+)", tag, re.IGNORECASE)
			value = re.search(r"\bcontent\s*=\s*(?:\"([^\"]*)\"|'([^']*)')", tag, re.IGNORECASE)
			if key and value and key.group(1).lower() == name:
				content = _clean(html.unescape(value.group(1) or value.group(2) or ""))
				if content:
					return content
	return None


def _without_writer_photos(blocks: list[Block], author: str | None) -> list[Block]:
	"""The blocks without the writer's photo: an image described by the author's name, or by a name alone
	(letters only, at most four words) before the first paragraph."""
	result = []
	text_started = False
	for block in blocks:
		if block.kind == "image":
			name_only = re.fullmatch(r"[^\W\d_]+(?: [^\W\d_]+){0,3}", block.text) is not None
			if (author and block.text.casefold() == author.casefold()) or (name_only and not text_started):
				continue
		elif block.kind != "video":
			text_started = True
		result.append(block)
	return result


def extract_article(markup: str, url: str) -> Article:
	"""The article inside a page: from its article container, or every long paragraph if none is found.

	A video page without text gives the page's summary and a note that it holds a video.
	"""
	parser = _parse(markup, url)
	if not parser.blocks:
		parser = _parse(markup, url, whole_document=True, min_length=40)
	blocks = _without_writer_photos(parser.blocks, parser.author)
	if not any(block.kind not in ("image", "video") for block in blocks):
		page_type = (_meta(markup, ("dtk:custom-pagetype", "og:type")) or "").lower()
		has_video = "video" in page_type or any(block.kind == "video" for block in blocks)
		summary = _meta(markup, ("og:description", "description"))
		images = [block for block in blocks if block.kind == "image"]
		blocks = ([Block("p", html.escape(summary, quote=False), summary)] if summary else []) + images
		if has_video:
			blocks.append(Block("video", "", ""))
	language = "id"
	match = re.search(r"<html[^>]*\blang=[\"']?([A-Za-z]{2})", markup[:2000], re.IGNORECASE)
	if match:
		language = match.group(1).lower()
	return Article(blocks=blocks, language=language, author=parser.author)


def fetch_article(url: str, bypass_ssl: bool = False) -> Article | None:
	"""Download a news page and extract its article. None when the download fails or finds no text."""
	data = fetch_http_data(_rewrite_url_for_full_article(url), bypass_ssl=bypass_ssl)
	if not data:
		return None
	article = extract_article(_decode(data), url)
	return article if article.blocks else None
