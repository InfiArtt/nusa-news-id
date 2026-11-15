"""The global plugin: secure screens, refresh results and stale checks."""

import sys
from types import ModuleType, SimpleNamespace

import nusaNewsID
import nvda_mocks
import pytest
from nusaNewsID import cache
from poFile import translated


def _stories(count: int) -> list:
	"""Stand-ins for NewsItems from a source that already has saved stories."""
	return [SimpleNamespace(source="Detik") for _ in range(count)]


@pytest.fixture
def securePlugin(monkeypatch):
	monkeypatch.setattr(nvda_mocks.appArgs, "secure", True)
	return nusaNewsID.GlobalPlugin()


def test_secure_screen_starts_nothing_and_terminates_cleanly(securePlugin):
	assert securePlugin.monitor_thread is None
	assert nusaNewsID.addon_instance is None
	securePlugin.terminate()


def test_reader_does_not_open_on_secure_screen(securePlugin):
	nvda_mocks.calledAfter.clear()
	securePlugin.script_openNewsReader(None)
	assert nvda_mocks.calledAfter == []


@pytest.fixture
def plugin(monkeypatch, securePlugin):
	"""A plugin with a fake running thread, without touching the network or NVDA's settings."""
	thread = nusaNewsID.MonitorThread(securePlugin)
	securePlugin.monitor_thread = thread
	refreshed = []
	fakeGui = ModuleType("nusaNewsID.gui")
	fakeGui.refresh_active_dialog = lambda: refreshed.append(True)
	monkeypatch.setitem(sys.modules, "nusaNewsID.gui", fakeGui)
	securePlugin.refreshed = refreshed
	securePlugin.settings = {"cache_duration": 7}
	monkeypatch.setattr(cache, "prune_cache", lambda days, keep_sources=(): None)
	monkeypatch.setattr(cache, "is_empty", lambda: False)
	monkeypatch.setattr(cache, "sources", lambda: {"Detik", "InfiArtt"})
	nvda_mocks.spoken.clear()
	with translated("id"):
		yield securePlugin


def test_manual_refresh_reports_new_stories(plugin, monkeypatch):
	monkeypatch.setattr(
		cache,
		"save_news_items",
		lambda items, mark_seen=False, quiet_sources=None, refresh_sources=(): items[:2],
	)
	assert plugin.request_refresh()
	plugin.on_check_finished(plugin.monitor_thread, _stories(3))
	assert nvda_mocks.spoken == ["Selesai, 2 berita baru."]
	assert plugin.refreshed == [True]


def test_manual_refresh_reports_nothing_new(plugin, monkeypatch):
	monkeypatch.setattr(
		cache, "save_news_items", lambda items, mark_seen=False, quiet_sources=None, refresh_sources=(): []
	)
	plugin.request_refresh()
	plugin.on_check_finished(plugin.monitor_thread, _stories(1))
	assert nvda_mocks.spoken == ["Selesai, tidak ada berita baru."]


def test_check_from_a_stopped_thread_is_ignored(plugin, monkeypatch):
	saved = []
	monkeypatch.setattr(
		cache,
		"save_news_items",
		lambda items, mark_seen=False, quiet_sources=None, refresh_sources=(): saved.append(items) or items,
	)
	oldThread = nusaNewsID.MonitorThread(plugin)
	plugin.on_check_finished(oldThread, _stories(1))
	plugin.monitor_thread.stop()
	plugin.on_check_finished(plugin.monitor_thread, _stories(1))
	assert saved == []
	assert nvda_mocks.spoken == []


def test_first_fill_is_saved_as_read_and_announced_once(plugin, monkeypatch):
	calls = []
	monkeypatch.setattr(cache, "is_empty", lambda: True)
	monkeypatch.setattr(
		cache,
		"save_news_items",
		lambda items, mark_seen=False, quiet_sources=None, refresh_sources=(): (
			calls.append(mark_seen) or items
		),
	)
	plugin.request_refresh()
	plugin.on_check_finished(plugin.monitor_thread, _stories(3))
	assert calls == [True]
	assert nvda_mocks.spoken == ["NusaNews: 3 berita dimuat."]
