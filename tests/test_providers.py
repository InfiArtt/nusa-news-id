"""The rules every provider shares: feed or page, sections, age, disability and breaking news."""

from datetime import datetime

import pytest
from nusaNewsID.providers import baseProvider, textUtils
from nusaNewsID.providers.baseProvider import BaseProvider, CategorySource
from nusaNewsID.providers.textUtils import WIB

NOW = datetime(2026, 11, 15, 8, 0, tzinfo=WIB)


@pytest.fixture(autouse=True)
def fixedNow(monkeypatch):
	monkeypatch.setattr(textUtils, "now", lambda: NOW)
	monkeypatch.setattr(baseProvider, "now", lambda: NOW)


def _rss(*items: tuple[str, str, str]) -> bytes:
	body = "".join(
		f"<item><title>{title}</title><link>{link}</link><pubDate>{date}</pubDate></item>"
		for title, link, date in items
	)
	return f"<rss><channel>{body}</channel></rss>".encode()


FRESH = "Sun, 15 Nov 2026 07:00:00 +0700"
OLD = "Mon, 01 Jan 2024 07:00:00 +0700"


class FakeSite(BaseProvider):
	source_name = "Fake"
	base_url = "https://fake.example"
	article_pattern = r"fake\.example/(?:news|sport)/read/\d+"
	url_date_pattern = r"/read/(\d{4})(\d{2})(\d{2})"
	categories = {
		"Nasional": CategorySource(
			rss="https://fake.example/rss", html="https://fake.example/news", sections=r"/news/"
		),
		"Disabilitas": CategorySource(html="https://fake.example/tag/disabilitas"),
	}

	def __init__(self, pages: dict[str, bytes]):
		self.pages = pages
		self.requested: list[str] = []

	def _request_http(self, url, bypass_ssl=False, timeout=10):
		self.requested.append(url)
		return self.pages.get(url)


def _manyFresh(count: int) -> bytes:
	return _rss(
		*[
			(f"Berita nasional nomor {i} hari ini", f"https://fake.example/news/read/{i}", FRESH)
			for i in range(count)
		]
	)


def test_a_fresh_feed_is_enough():
	site = FakeSite({"https://fake.example/rss": _manyFresh(6)})
	items = site.fetch_news("Nasional")
	assert len(items) == 6
	assert site.requested == ["https://fake.example/rss"]
	assert items[0].published_at == "2026-11-15T07:00:00+07:00"
	assert items[0].source == "Fake" and items[0].category == "Nasional"


def test_an_old_feed_falls_back_to_the_page():
	site = FakeSite(
		{
			"https://fake.example/rss": _rss(
				("Berita lama dari tahun lalu", "https://fake.example/news/read/1", OLD)
			),
			"https://fake.example/news": b'<a href="/news/read/20261115">Berita baru dari halaman kategori</a>',
		}
	)
	items = site.fetch_news("Nasional")
	assert [item.title for item in items] == ["Berita baru dari halaman kategori"]
	assert items[0].published_at == "2026-11-15T00:00:00+07:00"


def test_a_thin_feed_is_topped_up_without_duplicates():
	site = FakeSite(
		{
			"https://fake.example/rss": _manyFresh(2),
			"https://fake.example/news": b'<a href="/news/read/0">Berita nasional nomor 0 hari ini</a>'
			b'<a href="/news/read/9">Berita tambahan dari halaman</a>',
		}
	)
	titles = [item.title for item in site.fetch_news("Nasional")]
	assert titles == [
		"Berita nasional nomor 0 hari ini",
		"Berita nasional nomor 1 hari ini",
		"Berita tambahan dari halaman",
	]


def test_links_to_other_sections_are_left_out():
	site = FakeSite(
		{
			"https://fake.example/news": b'<a href="/news/read/1">Berita nasional yang benar</a>'
			b'<a href="/sport/read/2">Berita olahraga di samping</a>',
		}
	)
	assert [item.title for item in site.fetch_news("Nasional")] == ["Berita nasional yang benar"]


def test_short_titles_and_old_stories_are_dropped():
	site = FakeSite(
		{
			"https://fake.example/rss": _rss(
				("Menu", "https://fake.example/news/read/1", FRESH),
				("Berita lama yang sudah lewat", "https://fake.example/news/read/2", OLD),
			),
		}
	)
	assert site.fetch_news("Nasional") == []


def test_disability_page_keeps_only_disability_stories():
	site = FakeSite(
		{
			"https://fake.example/tag/disabilitas": b'<a href="/news/read/1">Komunitas Tuli gelar festival film</a>'
			b'<a href="/news/read/2">Warga menulis surat untuk wali kota</a>',
		}
	)
	assert [item.title for item in site.fetch_news("Disabilitas")] == ["Komunitas Tuli gelar festival film"]


def test_breaking_flag():
	site = FakeSite(
		{
			"https://fake.example/rss": _rss(
				("Gempa magnitudo 6 guncang Maluku", "https://fake.example/news/read/1", FRESH),
				("Presiden resmikan jalan tol baru", "https://fake.example/news/read/2", FRESH),
			),
		}
	)
	assert [item.is_breaking for item in site.fetch_news("Nasional")] == [True, False]


def test_unknown_category_makes_no_request():
	site = FakeSite({})
	assert site.fetch_news("Olahraga") == []
	assert site.requested == []


def test_every_real_provider_is_well_formed():
	from nusaNewsID.providers.sourceManager import PROVIDER_CLASSES

	categories = {
		"Nasional",
		"Internasional",
		"Teknologi",
		"Politik",
		"Ekonomi",
		"Olahraga",
		"Entertainment",
		"Disabilitas",
	}
	for provider in PROVIDER_CLASSES:
		assert provider.source_name and provider.article_pattern and provider.categories
		assert set(provider.categories) <= categories
		for source in provider.categories.values():
			assert source.rss or source.pages
