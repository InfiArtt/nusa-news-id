"""Extracting an article: its container, its structure, and what is left out."""

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
	assert [block.kind for block in article.blocks] == ["p", "h2", "p", "li-ol", "li-ol", "p"]
	assert article.blocks[0].text == "Jakarta - Gubernur meresmikan taman baru untuk warga."
	assert "Kotak samping" not in article.text
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
