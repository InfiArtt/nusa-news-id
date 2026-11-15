"""The provider registry, Tempo's removal and the Merdeka address pattern."""

import re
import threading

from nusaNewsID import config
from nusaNewsID.providers import sourceManager
from nusaNewsID.providers.merdeka import MerdekaProvider


def test_sources_without_tempo_and_macpoin():
	assert sourceManager.SOURCE_NAMES == (
		"Detik",
		"Kompas",
		"Antara",
		"Republika",
		"Liputan6",
		"Merdeka",
		"CNN Indonesia",
		"WinPoin",
	)


def test_old_tempo_setting_is_ignored(monkeypatch):
	saved = {"enabled_sources": ["Detik", "Tempo", "Kompas"]}
	real = config.get_config_val
	monkeypatch.setattr(config, "get_config_val", lambda key: saved.get(key, real(key)))
	assert config.read_settings()["enabled_sources"] == ["Detik", "Kompas"]


def test_merdeka_pattern_matches_new_article_addresses():
	pattern = re.compile(MerdekaProvider.article_pattern)
	assert pattern.search(
		"https://www.merdeka.com/peristiwa/read/8335388/anwar-hafid-tegaskan-dukungan-sulteng-pada-pemerintahan"
	)
	assert pattern.search("https://www.merdeka.com/uang/read/8333835/bi-ungkap-faktor-penyebab-rupiah-anjlok")


def test_merdeka_pattern_skips_footer_and_section_links():
	pattern = re.compile(MerdekaProvider.article_pattern)
	assert not pattern.search("https://www.merdeka.com/pedoman-media-siber.html")
	assert not pattern.search("https://www.merdeka.com/peristiwa")
	assert not pattern.search("https://www.merdeka.com/special-content/menakar-fiskal-moneter")


def test_providers_share_the_stop_event():
	stopEvent = threading.Event()
	manager = sourceManager.SourceManager(stopEvent)
	assert all(provider.stop_event is stopEvent for provider in manager.providers.values())


def test_polling_stops_when_asked():
	stopEvent = threading.Event()
	manager = sourceManager.SourceManager(stopEvent)
	asked = []

	def fakeFetch(category, **kwargs):
		asked.append(category)
		stopEvent.set()
		return []

	manager.providers["Detik"].fetch_news = fakeFetch
	manager.poll_sources(["Detik", "Kompas"], ["Nasional", "Teknologi"])
	assert asked == ["Nasional"]
