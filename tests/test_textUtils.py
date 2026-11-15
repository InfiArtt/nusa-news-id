"""Dates, titles and keywords."""

from datetime import UTC, datetime, timedelta

import pytest
from nusaNewsID.providers import textUtils
from nusaNewsID.providers.textUtils import WIB, clean_title, is_about_disability, is_breaking, parse_date

NOW = datetime(2026, 11, 15, 8, 0, tzinfo=WIB)


@pytest.mark.parametrize(
	("text", "expected"),
	[
		("Sun, 15 Nov 2026 07:39:34 +0700", datetime(2026, 11, 15, 7, 39, 34, tzinfo=WIB)),
		("Fri, 13 Nov 2026 13:57:22 +0000", datetime(2026, 11, 13, 20, 57, 22, tzinfo=WIB)),
		("2026-11-14 21:42:38", datetime(2026, 11, 14, 21, 42, 38, tzinfo=WIB)),
		("2026-11-13", datetime(2026, 11, 13, tzinfo=WIB)),
		("1794702609", datetime.fromtimestamp(1794702609, WIB)),
		("15 November 2026", datetime(2026, 11, 15, tzinfo=WIB)),
		("Nasional - 15 November 2026, 03:02", datetime(2026, 11, 15, 3, 2, tzinfo=WIB)),
		("15 Nov 2026 06:09", datetime(2026, 11, 15, 6, 9, tzinfo=WIB)),
		("9 Agustus 2026", datetime(2026, 8, 9, tzinfo=WIB)),
		("15 October 2026, 19:35", datetime(2026, 10, 15, 19, 35, tzinfo=WIB)),
		("14/11/2026, 20:00 WIB", datetime(2026, 11, 14, 20, 0, tzinfo=WIB)),
		("10 jam lalu", NOW - timedelta(hours=10)),
		("13 menit yang lalu", NOW - timedelta(minutes=13)),
		("1 bulan yang lalu", NOW - timedelta(days=30)),
		("5 hours ago", NOW - timedelta(hours=5)),
		("kemarin, 20:15", datetime(2026, 11, 14, 20, 15, tzinfo=WIB)),
	],
)
def test_parse_date(text, expected):
	assert parse_date(text, NOW) == expected


@pytest.mark.parametrize("text", ["", None, "Nasional", "Baca selengkapnya"])
def test_parse_date_gives_none_for_other_text(text):
	assert parse_date(text, NOW) is None


def test_relative_dates_count_from_now(monkeypatch):
	monkeypatch.setattr(textUtils, "now", lambda: NOW)
	assert parse_date("2 jam lalu") == NOW - timedelta(hours=2)


def test_parsed_dates_keep_their_zone():
	assert parse_date("2026-11-15T01:00:00Z", NOW) == datetime(2026, 11, 15, 1, 0, tzinfo=UTC)


@pytest.mark.parametrize(
	("raw", "expected"),
	[
		("18:13Jangan Biarkan Google Terus Melacakmu", "Jangan Biarkan Google Terus Melacakmu"),
		("  Gempa &amp; Tsunami\n di Maluku ", "Gempa & Tsunami di Maluku"),
		("01:53 VIDEO: Aksi Sosial Hotel di Surabaya", "VIDEO: Aksi Sosial Hotel di Surabaya"),
		("Judul Berita - ", "Judul Berita"),
	],
)
def test_clean_title(raw, expected):
	assert clean_title(raw) == expected


def test_clean_title_removes_provider_noise():
	assert clean_title("Headline Judul Berita Penting", (r"^Headline\s+",)) == "Judul Berita Penting"


@pytest.mark.parametrize(
	"title",
	[
		"Gempa Magnitudo 6 Guncang Maluku",
		"BMKG keluarkan peringatan dini cuaca ekstrem",
		"Banjir bandang terjang Bireuen",
		"Polisi temukan bom rakitan di Medan",
	],
)
def test_breaking_titles(title):
	assert is_breaking(title)


@pytest.mark.parametrize(
	"title",
	[
		"Presiden Prabowo tiba di Manila, Filipina untuk hadiri KTT ke-49 ASEAN",
		"Waspada Kuis Hoaks di Medsos, Kenali Cirinya",
		"Bombardir serangan di final Piala Dunia",
		"Urgensi revisi UU Pemilu",
	],
)
def test_ordinary_titles_are_not_breaking(title):
	assert not is_breaking(title)


@pytest.mark.parametrize(
	"text",
	[
		"Pemkot Surabaya Dirikan PAUD Khusus untuk Anak Disabilitas",
		"Komunitas Tuli gelar festival film",
		"Siswa SLB raih medali",
		"Kursi roda gratis untuk warga",
	],
)
def test_disability_texts(text):
	assert is_about_disability(text)


@pytest.mark.parametrize(
	"text",
	[
		"Warga menulis surat untuk presiden",
		"Lalu lintas lumpuh akibat banjir",
		"OKI serukan kebijakan iklim yang inklusif",
		"Program pengentasan buta huruf",
		"Rekonstruksi aksesibilitas jalan tol",
	],
)
def test_texts_that_only_look_like_disability(text):
	assert not is_about_disability(text)
