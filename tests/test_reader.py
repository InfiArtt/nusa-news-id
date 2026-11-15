"""The reader page follows the WCAG rules in readerHtml's header, whatever the article contains."""

import re
from html.parser import HTMLParser

import pytest
from nusaNewsID import readerHtml
from nusaNewsID.providers.articleContent import Article, parse_blocks

LABELS = {
	"browser": "Open in &browser",
	"link": "Copy &link",
	"copy": "Copy &story",
	"close": "&Close",
	"actions": "Actions",
	"image": "Photo: {description}",
	"video": "This story has a video. Press Open in browser to watch it.",
	"social": "Post on {network} by {handle}:",
	"social_no_handle": "Post on {network}:",
}

ARTICLE_HTML = """
<h1>Judul Artikel Diulang</h1>
<p>Paragraf pertama dengan <a href="/glosarium#nvda">NVDA</a> dan <kbd>Insert+F7</kbd>.</p>
<h2>Bagian Satu</h2>
<ul><li>Butir satu</li><li>Butir dua</li></ul>
<h4>Bagian yang melompat level</h4>
<p style="color:#999;font-size:9px" onclick="alert(1)">Teks dengan gaya yang harus hilang.</p>
<img src="/a.jpg" alt="Foto pengguna kursi roda">
<img src="/b.jpg">
<script>alert("xss")</script>
<iframe src="https://ads.example"></iframe>
"""


class _Page(HTMLParser):
	def __init__(self):
		super().__init__()
		self.tags: list[tuple[str, dict]] = []
		self.texts: list[str] = []

	def handle_starttag(self, tag, attrs):
		self.tags.append((tag, dict(attrs)))

	def handle_data(self, data):
		self.texts.append(data)


def _page(article: Article | None = None, message: str | None = None, **changes) -> tuple[str, _Page]:
	values = dict(
		title="Judul Artikel Diulang",
		details=["Detik, category National", "Published 15 November 2026, 06:09"],
		url="https://news.example/1",
		article=article,
		message=message,
		ui_language="en_GB",
		labels=LABELS,
	)
	values.update(changes)
	page = readerHtml.build_page(**values)
	parsed = _Page()
	parsed.feed(page)
	return page, parsed


@pytest.fixture
def article():
	return Article(
		blocks=parse_blocks(ARTICLE_HTML, "https://news.example", whole_document=True), language="id"
	)


def test_languages_are_marked(article):
	page, parsed = _page(article)
	html_tag = next(attrs for tag, attrs in parsed.tags if tag == "html")
	assert html_tag["lang"] == "en"
	assert any(tag == "div" and attrs.get("lang") == "id" for tag, attrs in parsed.tags)
	assert 'X-UA-Compatible" content="IE=edge"' in page


def test_one_h1_and_no_skipped_heading_levels(article):
	_, parsed = _page(article)
	levels = [int(tag[1]) for tag, _ in parsed.tags if re.fullmatch(r"h[1-6]", tag)]
	assert levels.count(1) == 1 and levels[0] == 1
	# The article's copy of the title is dropped, and its h2 and h4 become h2 and h3.
	assert levels == [1, 2, 3]


def test_article_structure_is_kept(article):
	page, parsed = _page(article)
	tags = [tag for tag, _ in parsed.tags]
	assert "ul" in tags and tags.count("li") == 2
	assert '<a href="https://news.example/glosarium#nvda">NVDA</a>' in page
	assert "<kbd>Insert+F7</kbd>" in page


def test_nothing_unsafe_or_styled_from_the_site(article):
	page, parsed = _page(article)
	body = page.split("<body>", 1)[1].split("<script>", 1)[0]
	assert "alert" not in body and "iframe" not in body and "onclick" not in body
	assert not any("style" in attrs for tag, attrs in parsed.tags if tag != "html")
	assert "#999" not in page and "9px" not in page


def test_images_need_a_text_alternative(article):
	_, parsed = _page(article)
	# The description is visible text after the image, read once, so the image itself has an empty alt.
	images = [attrs for tag, attrs in parsed.tags if tag == "img"]
	# The photo loads after the page (data-src), so the page and NVDA never wait for it.
	assert images == [{"data-src": "https://news.example/a.jpg", "alt": ""}]
	assert "Photo: Foto pengguna kursi roda" in parsed.texts


def test_videos_and_social_posts_are_introduced():
	blocks = parse_blocks(
		'<p>Isi berita.</p><video src="/v.mp4"></video>'
		'<blockquote class="twitter-tweet"><p>Peluncuran berhasil https://t.co/abc</p>'
		"&mdash; SpaceX (@SpaceX) November 14, 2026</blockquote>",
		"https://news.example",
		whole_document=True,
	)
	_, parsed = _page(Article(blocks=blocks))
	assert LABELS["video"] in parsed.texts
	assert "Post on X by @SpaceX:" in parsed.texts and "Peluncuran berhasil" in parsed.texts


def test_colors_and_sizes_follow_the_system():
	css = readerHtml.STYLE
	assert not re.search(r"#[0-9a-fA-F]{3,6}\b|rgb\(", css), "fixed colors"
	assert not re.search(r"\d+px", css), "fixed pixel sizes"
	assert (
		"Window;" in css and "WindowText;" in css and "line-height: 1.5" in css and "max-width: 70ch" in css
	)
	assert "outline" in css


@pytest.mark.parametrize(("zoom", "size"), [(100, "125%"), (200, "250%"), (400, "500%")])
def test_text_size_grows_with_zoom(zoom, size):
	page, _ = _page(zoom=zoom)
	assert f'style="font-size: {size}"' in page


def test_actions_are_buttons_with_labels(article):
	_, parsed = _page(article)
	buttons = [attrs["data-action"] for tag, attrs in parsed.tags if tag == "button"]
	assert buttons == list(readerHtml.ACTIONS)
	assert all(attrs.get("type") == "button" for tag, attrs in parsed.tags if tag == "button")
	assert "Open in browser" in parsed.texts and "&" not in "".join(parsed.texts)
	nav = next(attrs for tag, attrs in parsed.tags if attrs.get("role") == "navigation")
	assert nav["aria-label"] == "Actions"
	assert any(attrs.get("role") == "main" for tag, attrs in parsed.tags)


def test_message_while_downloading():
	page, _ = _page(None, message="Downloading the story...")
	assert 'role="status">Downloading the story...</p>' in page


def test_shortcut_key():
	assert readerHtml.shortcut_key("Open in &browser") == "b"
	assert readerHtml.shortcut_key("Close") is None
