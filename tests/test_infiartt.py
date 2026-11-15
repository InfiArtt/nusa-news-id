"""InfiArtt: always on, read through its API, with articles and knowledge base guides."""

import json
import threading
from datetime import datetime

import pytest
from nusaNewsID.providers import baseProvider, infiartt, sourceManager, textUtils
from nusaNewsID.providers.textUtils import WIB

NOW = datetime(2026, 11, 15, 8, 0, tzinfo=WIB)


@pytest.fixture(autouse=True)
def fixedNow(monkeypatch):
	monkeypatch.setattr(textUtils, "now", lambda: NOW)
	monkeypatch.setattr(baseProvider, "now", lambda: NOW)


def _ok(data) -> bytes:
	return json.dumps({"ok": True, "data": data}).encode()


PAGES = {
	"https://infiartt.com/api/v1/posts?page=1": _ok(
		{
			"items": [
				{
					"title": "NVDA 2026.3 Resmi Rilis",
					"url": "https://infiartt.com/2026/11/14/nvda-2026-3-resmi-rilis/",
					"published_at": "2026-11-14 07:40:30",
					"excerpt": "Versi baru NVDA.",
				},
				{
					"title": "Artikel lama sekali",
					"url": "https://infiartt.com/2025/01/01/lama/",
					"published_at": "2025-01-01 07:00:00",
				},
			],
			"has_more": True,
		}
	),
	"https://infiartt.com/api/v1/kb": _ok(
		{
			"items": [
				{
					"id": 25,
					"title": "Aksesibilitas Digital",
					"is_folder": True,
					"children": [
						{
							"id": 33,
							"title": "Teks Tautan yang Deskriptif",
							"is_folder": False,
							"children": [],
						},
						{"id": 36, "title": "Panduan Lama", "is_folder": False, "children": []},
					],
				},
				{"id": 40, "title": "Panduan tanpa tanggal", "is_folder": False, "children": []},
			]
		}
	),
	"https://infiartt.com/sitemap.xml": b"""<urlset>
<url><loc>https://infiartt.com/kb/33/teks-tautan</loc><lastmod>2026-11-12</lastmod></url>
<url><loc>https://infiartt.com/kb/36/panduan-lama</loc><lastmod>2024-01-01</lastmod></url>
</urlset>""",
	"https://infiartt.com/api/v1/posts/nvda-2026-3-resmi-rilis": _ok(
		{
			"content_html": "<h2>Apa yang baru</h2><p>Lebih cepat.</p>",
			"locked": False,
			"excerpt": "Versi baru NVDA.",
		}
	),
	"https://infiartt.com/api/v1/kb/33": _ok(
		{"content_html": "<p>Tautan adalah pintu.</p>", "language": "id", "updated_at": "2026-11-12 10:00:00"}
	),
	"https://infiartt.com/api/v1/posts/khusus-anggota": _ok(
		{"content_html": None, "locked": True, "requirement": "member", "excerpt": "Ringkasan saja."}
	),
}


class FakeInfiArtt(infiartt.InfiArttProvider):
	def __init__(self):
		super().__init__()
		self.requested: list[str] = []

	def _request_http(self, url, bypass_ssl=False, timeout=10):
		self.requested.append(url)
		return PAGES.get(url)


def test_every_article_whatever_its_age():
	site = FakeInfiArtt()
	items = site.fetch_news(infiartt.ARTICLES, max_age_days=1)
	assert [item.title for item in items] == ["NVDA 2026.3 Resmi Rilis", "Artikel lama sekali"]
	assert items[0].source == "InfiArtt" and items[0].category == "Artikel InfiArtt"
	assert items[0].published_at == "2026-11-14T07:40:30+07:00"
	assert items[0].summary == "Versi baru NVDA."
	# The first check reads every page; page 2 is missing in the fake, which ends it.
	assert site.requested == [
		"https://infiartt.com/api/v1/posts?page=1",
		"https://infiartt.com/api/v1/posts?page=2",
	]


def test_later_checks_stop_at_a_known_article():
	site = FakeInfiArtt()
	site.fetch_news(infiartt.ARTICLES)
	site.requested.clear()
	site.fetch_news(infiartt.ARTICLES)
	assert site.requested == ["https://infiartt.com/api/v1/posts?page=1"]


def test_every_knowledge_base_guide_whatever_its_age():
	items = FakeInfiArtt().fetch_news(infiartt.KNOWLEDGE_BASE, max_age_days=1)
	assert [(item.title, item.published_at) for item in items] == [
		("Teks Tautan yang Deskriptif", "2026-11-12T00:00:00+07:00"),
		("Panduan Lama", "2024-01-01T00:00:00+07:00"),
		("Panduan tanpa tanggal", None),
	]
	assert items[0].url == "https://infiartt.com/kb/33/teks-tautan"


def test_article_and_guide_text_from_the_api():
	site = FakeInfiArtt()
	article = site.fetch_article("https://infiartt.com/2026/11/14/nvda-2026-3-resmi-rilis/")
	assert [block.kind for block in article.blocks] == ["h2", "p"]
	guide = site.fetch_article("https://infiartt.com/kb/33/teks-tautan")
	assert guide.text == "Tautan adalah pintu." and guide.language == "id"


def test_members_only_article_shows_its_summary():
	article = FakeInfiArtt().fetch_article("https://infiartt.com/2026/11/14/khusus-anggota/")
	assert article.locked_note and article.text == "Ringkasan saja."


def test_infiartt_is_always_checked_and_cannot_be_turned_off():
	assert "InfiArtt" not in sourceManager.SOURCE_NAMES
	assert sourceManager.ALWAYS_ON_SOURCES == ("InfiArtt",)
	assert {"Artikel InfiArtt", "Pusat Pengetahuan"} <= set(sourceManager.CATEGORIES)
	manager = sourceManager.SourceManager(threading.Event())
	asked = []
	for name, provider in manager.providers.items():
		provider.fetch_news = lambda category, name=name, **kwargs: asked.append((name, category)) or []
	manager.poll_sources([], ["Nasional"])
	assert asked == [("InfiArtt", "Artikel InfiArtt"), ("InfiArtt", "Pusat Pengetahuan")]


def test_provider_for_a_story():
	assert isinstance(sourceManager.provider_for("InfiArtt"), infiartt.InfiArttProvider)
	assert type(sourceManager.provider_for("Tempo")) is baseProvider.BaseProvider
