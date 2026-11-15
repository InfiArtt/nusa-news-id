"""The global plugin: secure screens, refresh results and stale checks."""

import sys
from types import ModuleType

import nvda_mocks
import pytest

import nusaNewsID
from nusaNewsID import cache


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
	nvda_mocks.spoken.clear()
	return securePlugin


def test_manual_refresh_reports_new_stories(plugin, monkeypatch):
	monkeypatch.setattr(cache, "save_news_items", lambda items: items[:2])
	assert plugin.request_refresh()
	plugin.on_check_finished(plugin.monitor_thread, ["a", "b", "c"])
	assert nvda_mocks.spoken == ["Selesai, 2 berita baru."]
	assert plugin.refreshed == [True]


def test_manual_refresh_reports_nothing_new(plugin, monkeypatch):
	monkeypatch.setattr(cache, "save_news_items", lambda items: [])
	plugin.request_refresh()
	plugin.on_check_finished(plugin.monitor_thread, ["a"])
	assert nvda_mocks.spoken == ["Selesai, tidak ada berita baru."]


def test_check_from_a_stopped_thread_is_ignored(plugin, monkeypatch):
	saved = []
	monkeypatch.setattr(cache, "save_news_items", lambda items: saved.append(items) or items)
	oldThread = nusaNewsID.MonitorThread(plugin)
	plugin.on_check_finished(oldThread, ["a"])
	plugin.monitor_thread.stop()
	plugin.on_check_finished(plugin.monitor_thread, ["a"])
	assert saved == []
	assert nvda_mocks.spoken == []
