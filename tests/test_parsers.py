"""Reading feeds and category pages. The HTML samples copy the card layouts of the real sites."""

from datetime import datetime

from nusaNewsID.providers.parsers import normalize_url, parse_html_links, parse_rss
from nusaNewsID.providers.textUtils import WIB

NOW = datetime(2026, 11, 15, 8, 0, tzinfo=WIB)

RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Feed</title>
<item>
	<title><![CDATA[Gempa Magnitudo 5,2 Guncang Maluku]]></title>
	<link>https://www.antaranews.com/berita/5854403/gempa?utm_source=rss</link>
	<pubDate>Sun, 15 Nov 2026 07:39:34 +0700</pubDate>
	<description><![CDATA[<p>BMKG mencatat gempa.</p>]]></description>
</item>
<item><title>Tanpa tautan</title></item>
</channel></rss>"""


def test_rss_items():
	(story,) = parse_rss(RSS, NOW)
	assert story.title == "Gempa Magnitudo 5,2 Guncang Maluku"
	assert story.url == "https://www.antaranews.com/berita/5854403/gempa"
	assert story.published == datetime(2026, 11, 15, 7, 39, 34, tzinfo=WIB)
	assert story.summary == "BMKG mencatat gempa."


def test_broken_rss_gives_nothing():
	assert parse_rss(b"<html>not a feed", NOW) == []


def test_normalize_url_drops_tracking():
	assert (
		normalize_url("https://News.Detik.com/berita/d-1/x?utm=1#top")
		== "https://news.detik.com/berita/d-1/x"
	)


KOMPAS = """
<div class="articleItem"><a href="https://nasional.kompas.com/read/2026/11/15/07000081/dalang-penyadapan">
	<div class="articleItem-img"><img alt="Foto penyadapan"></div>
	<div class="articleItem-box"><div class="articleLabel">Headline</div>
	<h2 class="articleTitle">Dalang di Balik Penyadapan terhadap Presiden</h2>
	<div class="articlePost"><div class="articlePost-subtitle">Nasional</div>
	<div class="articlePost-date">15 November 2026</div></div></div></a></div>
<div class="articleItem"><a href="https://bandung.kompas.com/read/2026/11/14/10000011/foto-gibran">
	<div class="articleItem-box"><h2 class="articleTitle">Koalisi Klarifikasi Penurunan Foto Gibran</h2>
	<div class="articlePost-date">14 November 2026</div></div></a></div>
"""


def test_kompas_cards_take_the_heading_and_their_own_date():
	stories = parse_html_links(KOMPAS.encode(), "https://www.kompas.com", r"kompas\.com/read/", reference=NOW)
	assert [story.title for story in stories] == [
		"Dalang di Balik Penyadapan terhadap Presiden",
		"Koalisi Klarifikasi Penurunan Foto Gibran",
	]
	assert [story.published.day for story in stories] == [15, 14]


REPUBLIKA = """
<li class="list-group-item" data-timestamp="1794690000">
<a href="https://news.republika.co.id/berita/toid056/asean-tunda"><div class="image"><img alt="Caption foto"></div>
<div class="date"><span class="kanal-info">Nasional</span> - 15 November 2026, 03:02</div>
<h3><span>Kursi Panas Wapres</span></h3></a></li>
<li class="list-group-item" data-timestamp="1794600000">
<a href="https://news.republika.co.id/berita/toicb3/kominfo-sulbar"><div class="date">14 November 2026, 02:47</div>
<h3><span>Kominfo Sulbar Minta Orang Tua Perkuat Pengawasan Gadget Anak</span></h3></a></li>
"""


def test_republika_short_title_beats_the_longer_kanal_and_date_line():
	stories = parse_html_links(
		REPUBLIKA.encode(), "https://www.republika.co.id", r"republika\.co\.id/berita/"
	)
	assert stories[0].title == "Kursi Panas Wapres"
	assert stories[0].published == datetime(2026, 11, 15, 3, 2, tzinfo=WIB)
	assert stories[1].published == datetime(2026, 11, 14, 2, 47, tzinfo=WIB)


ANTARA = """
<div class="card__post"><a href="https://www.antaranews.com/berita/1/politik-sepekan" title="Politik sepekan, Gibran mundur">
<img alt="x"></a><h2><a href="https://www.antaranews.com/berita/1/politik-sepekan">Politik sepekan, Gibran mundur</a></h2>
<span>3 jam lalu</span></div>
<a href="https://www.antaranews.com/berita/2/top?utm_campaign=top_news">Berita pilihan dari kanal lain</a>
<aside class="wrapper__list__article"><h4>Terkini</h4>
<a href="https://www.antaranews.com/berita/3/portugal-kalah">Portugal kalah 1-4 dari Denmark</a><span>1 jam lalu</span>
</aside>
"""


def test_antara_leaves_out_sidebars_and_campaign_links():
	stories = parse_html_links(
		ANTARA.encode(), "https://www.antaranews.com", r"antaranews\.com/berita/\d+/", r"utm_campaign=", NOW
	)
	assert [story.title for story in stories] == ["Politik sepekan, Gibran mundur"]
	assert stories[0].published == datetime(2026, 11, 15, 5, 0, tzinfo=WIB)


DETIK = """
<article><h2 class="media__title"><a dtr-ttl="PKS Tak Usulkan Nama Cawapres" href="https://news.detik.com/berita/d-8753509/pks">
 PKS Tak Usulkan Nama Cawapres </a></h2>
<div class="media__date"><span d-time="1794702609" title="Minggu, 15 Nov 2026 07:30 WIB">10 menit yang lalu</span></div>
</article>
<article><a href="/berita/d-8753510/relatif">Judul Dengan Tautan Relatif Tanpa Tanggal</a></article>
"""


def test_detik_unix_time_and_relative_links():
	stories = parse_html_links(
		DETIK.encode(), "https://news.detik.com", r"detik\.com/[a-z\-/]+/d-\d+", reference=NOW
	)
	assert stories[0].title == "PKS Tak Usulkan Nama Cawapres"
	assert stories[0].published == datetime.fromtimestamp(1794702609, WIB)
	assert stories[1].url == "https://news.detik.com/berita/d-8753510/relatif"
	assert stories[1].published is None
