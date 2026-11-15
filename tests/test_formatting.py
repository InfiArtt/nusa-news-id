"""One reading format for the list, notifications and the article reader."""

from datetime import datetime, timedelta, timezone

import pytest
from nusaNewsID import cache, formatting
from nusaNewsID.models import NewsItem

WIB = timezone(timedelta(hours=7))
NOW = datetime(2026, 11, 15, 8, 0, tzinfo=WIB)


@pytest.fixture(autouse=True)
def wibComputer(monkeypatch):
	"""Format in WIB whatever the time zone of the computer running the tests."""
	realAstimezone = datetime.astimezone

	class WibDatetime(datetime):
		def astimezone(self, tz=None):
			return realAstimezone(self, tz or WIB)

	monkeypatch.setattr(formatting, "datetime", WibDatetime)
	monkeypatch.setattr(formatting, "local_now", lambda: NOW)


def _item(**changes) -> NewsItem:
	values = dict(
		title="Sapaan Prabowo ke Jenderal Suyudi",
		source="Detik",
		url="https://news.detik.com/berita/d-1/sapaan",
		guid="https://news.detik.com/berita/d-1/sapaan",
		category="Nasional",
		published_at=(NOW - timedelta(minutes=14)).isoformat(),
		seen=False,
	)
	values.update(changes)
	return NewsItem(**values)


@pytest.mark.parametrize(
	("age", "expected"),
	[
		(timedelta(seconds=20), "baru saja"),
		(timedelta(minutes=-3), "baru saja"),
		(timedelta(minutes=14), "14 menit lalu"),
		(timedelta(hours=3, minutes=59), "3 jam lalu"),
		(timedelta(days=1, hours=11, minutes=55), "13 November 2026 pukul 20.05"),
	],
)
def test_format_time(age, expected):
	assert formatting.format_time(NOW - age, NOW) == expected


def test_list_item_unread():
	assert (
		formatting.list_item_text(_item(), NOW)
		== "Sapaan Prabowo ke Jenderal Suyudi. Detik, Nasional, 14 menit lalu. Belum dibaca."
	)


def test_list_item_read_and_breaking():
	item = _item(title="Gempa magnitudo 6 guncang Maluku", source="Antara", is_breaking=True, seen=True)
	assert (
		formatting.list_item_text(item, NOW)
		== "Breaking. Gempa magnitudo 6 guncang Maluku. Antara, Nasional, 14 menit lalu."
	)


def test_list_item_without_a_publication_time_uses_when_it_was_found():
	item = _item(published_at=None, found_at=(NOW - timedelta(hours=2)).isoformat())
	assert formatting.list_item_text(item, NOW).endswith("Detik, Nasional, 2 jam lalu. Belum dibaca.")


def test_list_item_title_ending_in_a_question_mark_gets_no_extra_period():
	assert formatting.list_item_text(_item(title="Apakah Gibran Bisa Maju Lagi?"), NOW).startswith(
		"Apakah Gibran Bisa Maju Lagi? Detik"
	)


def test_no_symbols_that_depend_on_the_punctuation_level():
	for text in (
		formatting.list_item_text(_item(is_breaking=True), NOW),
		formatting.load_more_text(50),
		formatting.notification_text(_item()),
		formatting.article_header(_item()).replace(_item().url, ""),
	):
		assert not set(text) & set("[]|-")


def test_notifications():
	assert (
		formatting.notification_text(_item()) == "Berita baru dari Detik: Sapaan Prabowo ke Jenderal Suyudi."
	)
	assert (
		formatting.notification_text(_item(title="Gempa guncang Maluku", source="Antara", is_breaking=True))
		== "Breaking dari Antara: Gempa guncang Maluku."
	)
	assert (
		formatting.digest_text(5, "NVDA+shift+/")
		== "NusaNews: 5 berita baru. Tekan NVDA+shift+/ untuk membuka."
	)
	assert "Gestur Masukan" in formatting.digest_text(5, None)


def test_load_more():
	assert formatting.load_more_text(50) == "Muat 50 berita berikutnya"


def test_article_header_one_fact_per_line():
	item = _item(published_at="2026-11-15T06:09:00+07:00")
	assert formatting.article_header(item).split("\n") == [
		"Sapaan Prabowo ke Jenderal Suyudi",
		"Detik, kategori Nasional",
		"Terbit 15 November 2026 pukul 06.09",
		"https://news.detik.com/berita/d-1/sapaan",
	]


def test_article_header_without_publication_time():
	item = _item(published_at=None, found_at="2026-11-15T07:00:00+07:00")
	assert "Ditemukan 15 November 2026 pukul 07.00" in formatting.article_header(item)


def test_copy_has_title_and_body_only():
	assert (
		formatting.article_copy_text(_item(), "Isi berita.")
		== "Sapaan Prabowo ke Jenderal Suyudi\n\nIsi berita."
	)
	assert formatting.article_copy_text(_item(), "") == "Sapaan Prabowo ke Jenderal Suyudi"


def test_old_cached_dates_are_read_again():
	val = {"published_at": "10 jam lalu", "cached_at": "2026-11-15T08:00:00+07:00"}
	assert cache._published_iso(val) == "2026-11-14T22:00:00+07:00"
	assert cache._published_iso({"published_at": "2026-11-15T06:09:00+07:00"}) == "2026-11-15T06:09:00+07:00"
	assert cache._published_iso({"published_at": "Baca selengkapnya"}) is None
	assert cache._published_iso({}) is None


def test_old_cached_dates_from_the_story_text_are_dropped():
	val = {"published_at": "10 Januari 2027", "cached_at": "2026-11-12T15:25:39.299928"}
	assert cache._published_iso(val) is None
