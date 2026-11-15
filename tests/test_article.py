"""Extracting an article: its container, its structure, and what is left out."""

from nusaNewsID.providers import articleContent
from nusaNewsID.providers.articleContent import blocks_html, blocks_text, extract_article, is_boilerplate

PAGE = """
<html lang="id"><head><title>Judul halaman - situs</title></head><body>
<nav><a href="/">Beranda</a></nav>
<div class="detail__body-text">
	<p>Jakarta -</p>
	<p>Gubernur meresmikan taman baru untuk warga.</p>
	<div class="baca-juga"><p>Baca juga: Berita lain yang tidak perlu</p></div>
	<h2>Taman Ramah Disabilitas</h2>
	<p>Taman punya jalur pemandu untuk <strong>tunanetra</strong>.</p>
	<ol><li>Jalur pemandu</li><li>Toilet aksesibel</li></ol>
	<p>Advertisement</p>
	<p>Jl. KH Abdullah Syafei No.30, RT.4/RW.6, Kota Jakarta Selatan</p>
	<p>(abc/def)</p>
</div>
<div class="detail__body-text"><p>Kotak samping yang memakai kelas yang sama.</p></div>
<footer><p>Copyright 2026</p></footer>
</body></html>
"""


def test_article_container_structure_and_boilerplate():
	article = extract_article(PAGE, "https://news.example/a")
	assert article.language == "id"
	assert [block.kind for block in article.blocks] == ["p", "h2", "p", "li-ol", "li-ol"]
	assert article.blocks[0].text == "Jakarta - Gubernur meresmikan taman baru untuk warga."
	assert "Kotak samping" not in article.text and "abc/def" not in article.text
	assert "<ol>\n<li>Jalur pemandu</li>\n<li>Toilet aksesibel</li>\n</ol>" in blocks_html(article.blocks)
	assert "<strong>tunanetra</strong>" in article.html


def test_generic_fallback_takes_long_paragraphs():
	page = (
		"<html><body><p>Pendek.</p><p>" + "Paragraf panjang tanpa wadah artikel. " * 3 + "</p></body></html>"
	)
	article = extract_article(page, "https://news.example/b")
	assert len(article.blocks) == 1


def test_plain_text_has_one_paragraph_per_block():
	article = extract_article(PAGE, "https://news.example/a")
	assert blocks_text(article.blocks).split("\n\n")[1] == "Taman Ramah Disabilitas"


def test_boilerplate_rules():
	assert is_boilerplate("Baca juga: apa saja")
	assert is_boilerplate("Dilarang keras mengambil konten, melakukan crawling")
	assert is_boilerplate("Catatan Penulis : WinPoin sepenuhnya bergantung pada iklan untuk tetap hidup")
	assert not is_boilerplate("Jalan tol baru dibuka untuk umum.")


def _blocks(markup: str) -> list:
	return extract_article(f'<div class="detail__body-text">{markup}</div>', "https://news.example/a").blocks


def test_photo_has_one_description_without_credit_or_buttons():
	blocks = _blocks(
		'<figure><img src="/f.jpg" alt="foto"><span>Perbesar</span>'
		"<figcaption>Warga antre di halte. (Foto: Ady/Liputan6.com)</figcaption></figure>"
		"<p>Isi berita yang cukup panjang.</p>"
	)
	assert [(block.kind, block.text) for block in blocks] == [
		("image", "Warga antre di halte."),
		("p", "Isi berita yang cukup panjang."),
	]
	assert 'alt=""' in blocks[0].html


def test_caption_after_image_and_credit_lines():
	blocks = _blocks(
		'<img src="/f.jpg" alt="Gedung DPR"><figcaption>Gedung DPR. Foto: ANTARA/Hafidz</figcaption>'
	)
	assert [block.text for block in blocks] == ["Gedung DPR."]
	assert _blocks("<p>Perbesar</p><p>Teks berita.</p>")[0].text == "Teks berita."


def test_video_note_once_and_promoted_videos_dropped():
	blocks = _blocks(
		'<p>Pembuka berita.</p><div class="video-player"><iframe src="https://www.youtube.com/embed/x"></iframe></div>'
		'<p>Video: <a href="/v">Video promosi lain</a></p><iframe src="https://20.detik.com/embed/1"></iframe>'
		"<p>Penutup berita.</p>"
	)
	assert [block.kind for block in blocks] == ["p", "video", "p"]


def test_social_post_with_handle_and_without_links():
	blocks = _blocks(
		'<blockquote class="twitter-tweet"><p lang="en">Launch went well <a href="https://t.co/x">'
		"https://t.co/x</a></p>&mdash; SpaceX (@SpaceX) <a>November 14, 2026</a></blockquote>"
	)
	assert [(block.kind, block.text, block.extra) for block in blocks] == [
		("social", "Launch went well", "X|@SpaceX")
	]


def test_promotion_labels_and_their_links_are_dropped():
	blocks = _blocks(
		"<p>Isi pertama.</p><p>Baca:</p><p><a href='/x'>Judul berita lain</a></p>"
		"<p><strong>Pilihan Redaksi</strong></p><ul><li><a href='/y'>Berita pilihan</a></li></ul>"
		"<p>TONTON JUGA: <a href='/z'>Video lain</a></p><p>Isi kedua dengan <a href='/k'>tautan</a>.</p>"
		"<p>123Tampilkan Semua</p><p>(acd/acd)</p><p>placeholder</p>"
	)
	assert [block.text for block in blocks] == ["Isi pertama.", "Isi kedua dengan tautan."]


def test_byline_becomes_the_author():
	article = extract_article(
		'<div class="detail__body-text"><p>Oleh Idris Rusadi Putra - Reporter</p>'
		"<p>Oleh karena itu, pemerintah memutuskan hal ini.</p></div>",
		"https://news.example/a",
	)
	assert article.author == "Idris Rusadi Putra"
	assert [block.text for block in article.blocks] == ["Oleh karena itu, pemerintah memutuskan hal ini."]


def test_writer_photo_and_leftover_words_are_dropped():
	blocks = _blocks(
		'<img src="/w.jpg" alt="irwanto"><p>Isi berita yang cukup panjang.</p>'
		'<img src="/p.jpg" alt="placeholder"><img src="/d.jpg" alt="20D">'
		"<figure><img src='/f.jpg'><figcaption>Perbesar Wapres meninjau jembatan. (istimewa)</figcaption>"
		"</figure>"
		'<img src="/g.jpg" alt="Desain ponsel baru. Credit: @onleaks"><p>(sol/idn)<br>...</p>'
	)
	assert [block.text for block in blocks] == [
		"Isi berita yang cukup panjang.",
		"Wapres meninjau jembatan.",
		"Desain ponsel baru.",
	]


def test_video_page_without_text_gives_summary_and_video_note():
	page = (
		'<html><head><meta name="dtk:custom-pagetype" content="video">'
		'<meta property="og:description" content="Ringkasan video &amp; beritanya."></head>'
		"<body><div>Tidak ada isi.</div></body></html>"
	)
	article = extract_article(page, "https://news.example/v")
	assert [(block.kind, block.text) for block in article.blocks] == [
		("p", "Ringkasan video & beritanya."),
		("video", ""),
	]


ARTICLE_URL = "https://news.example/berita/1/judul"


def _paged(body: str, links: str = "") -> str:
	return f'<html><body><div class="detail__body-text">{body}</div>{links}</body></html>'


def test_links_to_further_pages_and_to_the_whole_article():
	page = _paged(
		"<p>Isi.</p>",
		f'<a href="{ARTICLE_URL}?page=1">1</a><a href="{ARTICLE_URL}?page=3">3</a>'
		f'<a href="{ARTICLE_URL}?page=2">2</a><a href="{ARTICLE_URL}?page=komentar">Komentar</a>'
		'<a href="https://news.example/indeks?page=2">Indeks</a>'
		f'<a href="{ARTICLE_URL}?page=all&amp;x=1">Semua</a>',
	)
	assert articleContent.next_page_urls(page, ARTICLE_URL) == [
		f"{ARTICLE_URL}?page=2",
		f"{ARTICLE_URL}?page=3",
	]
	assert articleContent.whole_article_url(page, ARTICLE_URL) == f"{ARTICLE_URL}?page=all&x=1"


def test_article_split_over_pages_is_read_page_by_page(monkeypatch):
	pages = {
		ARTICLE_URL: _paged(
			"<p>Halaman satu.</p><p>Diulang di tiap halaman.</p>", f'<a href="{ARTICLE_URL}?page=2">2</a>'
		),
		f"{ARTICLE_URL}?page=2": _paged("<p>Diulang di tiap halaman.</p><p>Halaman dua.</p>"),
	}
	monkeypatch.setattr(articleContent, "fetch_http_data", lambda url, bypass_ssl=False: pages[url].encode())
	article = articleContent.fetch_article(ARTICLE_URL)
	assert [block.text for block in article.blocks] == [
		"Halaman satu.",
		"Diulang di tiap halaman.",
		"Halaman dua.",
	]


def test_whole_article_link_is_used_when_there_are_pages(monkeypatch):
	requested = []
	pages = {
		ARTICLE_URL: _paged(
			"<p>Halaman satu.</p>",
			f'<a href="{ARTICLE_URL}?page=2">2</a><a href="{ARTICLE_URL}?page=all">Semua</a>',
		),
		f"{ARTICLE_URL}?page=all": _paged("<p>Halaman satu.</p><p>Halaman dua.</p>"),
	}

	def fetch(url, bypass_ssl=False):
		requested.append(url)
		return pages[url].encode()

	monkeypatch.setattr(articleContent, "fetch_http_data", fetch)
	article = articleContent.fetch_article(ARTICLE_URL)
	assert [block.text for block in article.blocks] == ["Halaman satu.", "Halaman dua."]
	assert requested == [ARTICLE_URL, f"{ARTICLE_URL}?page=all"]


def test_single_page_article_needs_one_request(monkeypatch):
	requested = []

	def fetch(url, bypass_ssl=False):
		requested.append(url)
		return _paged("<p>Satu halaman saja.</p>", f'<a href="{ARTICLE_URL}?show=all">Semua</a>').encode()

	monkeypatch.setattr(articleContent, "fetch_http_data", fetch)
	assert articleContent.fetch_article(ARTICLE_URL).blocks[0].text == "Satu halaman saja."
	assert requested == [ARTICLE_URL]
