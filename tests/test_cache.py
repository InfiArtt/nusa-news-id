"""The cache: kept in memory, saved later, compatible with version 1.0.2 files."""

import json

import pytest
from nusaNewsID import cache
from nusaNewsID.models import NewsItem
from nusaNewsID.providers.articleContent import Article, blocks_from_text


@pytest.fixture
def folder(tmp_path, monkeypatch):
	monkeypatch.setattr(cache, "get_cache_dir", lambda: str(tmp_path))
	monkeypatch.setattr(cache, "SAVE_DELAY_SECONDS", 60)
	monkeypatch.setattr(cache, "_stories", None)
	yield tmp_path
	if cache._saveTimer is not None:
		cache._saveTimer.cancel()
	cache._saveTimer = None


def _item(number: int, category: str = "Nasional") -> NewsItem:
	url = f"https://news.example/{number}"
	return NewsItem(title=f"Berita nomor {number}", source="Detik", url=url, guid=url, category=category)


def _file(folder) -> dict:
	return json.loads((folder / cache.CACHE_FILE).read_text(encoding="utf-8"))


def test_new_stories_are_returned_once_and_saved_later(folder):
	cache.init_db()
	assert cache.save_news_items([_item(1), _item(2)]) == [_item(1), _item(2)]
	assert cache.save_news_items([_item(1)]) == []
	assert not (folder / cache.CACHE_FILE).exists()
	cache.flush()
	assert set(_file(folder)) == {"https://news.example/1", "https://news.example/2"}


def test_a_story_found_in_another_category_gets_both(folder):
	cache.init_db()
	cache.save_news_items([_item(1)])
	cache.save_news_items([_item(1, "Politik")])
	(item,) = cache.get_news_items(["Detik"], ["Politik"])
	assert item.category == "Politik"
	cache.flush()
	assert _file(folder)["https://news.example/1"]["category"] == "Nasional, Politik"


def test_first_fill_can_be_saved_as_read(folder):
	cache.init_db()
	assert cache.is_empty()
	cache.save_news_items([_item(1)], mark_seen=True)
	assert cache.get_unread_count() == 0


def test_marking_read(folder):
	cache.init_db()
	cache.save_news_items([_item(1), _item(2)])
	cache.mark_as_read("https://news.example/1")
	assert cache.get_unread_count() == 1
	cache.mark_all_as_read()
	assert cache.get_unread_count() == 0


def test_old_file_loads_and_moves_article_text_out(folder):
	(folder / cache.CACHE_FILE).write_text(
		json.dumps(
			{
				"https://news.example/1": {
					"title": "Berita lama dari versi 1.0.2",
					"source": "Detik",
					"url": "https://news.example/1",
					"category": "Nasional",
					"summary": None,
					"content": "Isi artikel lama.",
					"published_at": "10 jam lalu",
					"is_breaking": False,
					"seen": False,
					"cached_at": "2026-11-15T08:00:00+07:00",
				}
			}
		),
		encoding="utf-8",
	)
	cache.init_db()
	assert cache.get_article("https://news.example/1").text == "Isi artikel lama."
	(item,) = cache.get_news_items(["Detik"], ["Nasional"])
	assert item.published_at == "2026-11-14T22:00:00+07:00"
	cache.flush()
	saved = _file(folder)["https://news.example/1"]
	assert "content" not in saved
	assert saved["published_at"] == "2026-11-14T22:00:00+07:00"


def test_prune_removes_old_stories_and_their_articles(folder):
	cache.init_db()
	cache.save_news_items([_item(1), _item(2)])
	cache._stories["https://news.example/1"]["cached_at"] = "2020-01-01T00:00:00"
	cache.update_article("https://news.example/1", Article(blocks=blocks_from_text("Isi.")))
	cache.prune_cache(7)
	assert [item.guid for item in cache.get_news_items(["Detik"], ["Nasional"])] == ["https://news.example/2"]
	assert cache.get_article("https://news.example/1") is None


def test_clear_removes_everything(folder):
	cache.init_db()
	cache.save_news_items([_item(1)])
	cache.update_article("https://news.example/1", Article(blocks=blocks_from_text("Isi.")))
	cache.clear_cache()
	assert cache.is_empty()
	assert _file(folder) == {}
	assert cache.get_article("https://news.example/1") is None


def test_list_is_newest_first_without_a_500_limit(folder):
	cache.init_db()
	cache.save_news_items([_item(number) for number in range(600)])
	for number in range(600):
		cache._stories[f"https://news.example/{number}"]["published_at"] = (
			f"2026-11-15T{number // 60:02d}:{number % 60:02d}:00+07:00"
		)
	items = cache.get_news_items(["Detik"], ["Nasional"])
	assert len(items) == 600
	assert items[0].title == "Berita nomor 599"


def test_prune_keeps_the_always_on_sources(folder):
	cache.init_db()
	infiartt = NewsItem(
		title="Panduan lama InfiArtt",
		source="InfiArtt",
		url="https://infiartt.com/kb/1",
		guid="https://infiartt.com/kb/1",
		category="Pusat Pengetahuan",
	)
	cache.save_news_items([_item(1), infiartt])
	for val in cache._stories.values():
		val["cached_at"] = "2020-01-01T00:00:00"
	cache.prune_cache(7, keep_sources=("InfiArtt",))
	assert [
		item.guid for item in cache.get_news_items(["Detik", "InfiArtt"], ["Nasional", "Pusat Pengetahuan"])
	] == ["https://infiartt.com/kb/1"]


def test_a_new_source_is_saved_quietly(folder):
	cache.init_db()
	cache.save_news_items([_item(1)])
	infiartt = NewsItem(
		title="Artikel InfiArtt",
		source="InfiArtt",
		url="https://infiartt.com/a",
		guid="https://infiartt.com/a",
		category="Artikel InfiArtt",
	)
	assert cache.sources() == {"Detik"}
	cache.save_news_items([_item(2), infiartt], quiet_sources={"InfiArtt"})
	unread = {
		item.guid
		for item in cache.get_news_items(
			["Detik", "InfiArtt"], ["Nasional", "Artikel InfiArtt"], filter_unread_only=True
		)
	}
	assert unread == {"https://news.example/1", "https://news.example/2"}
