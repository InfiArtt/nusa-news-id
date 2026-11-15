"""Announcements name the key that opens the news list, as NVDA keeps it."""

import sys
import types

import nusaNewsID
from nusaNewsID import notificationManager


def _script_openNewsReader(gesture):
	pass


_script_openNewsReader.__name__ = "script_openNewsReader"


def _fake_input_core(monkeypatch, user_bindings):
	module = types.SimpleNamespace(
		manager=types.SimpleNamespace(
			userGestureMap=types.SimpleNamespace(getScriptsForAllGestures=lambda: user_bindings)
		),
		getDisplayTextForGestureIdentifier=lambda gesture: ("keyboard", gesture.replace("kb:", "")),
	)
	monkeypatch.setitem(sys.modules, "inputCore", module)


def test_the_plugins_own_key_is_found(monkeypatch):
	# NVDA keeps the plugin's own keys as script functions, not names.
	plugin = types.SimpleNamespace(_gestureMap={"kb:nvda+shift+/": _script_openNewsReader})
	monkeypatch.setattr(nusaNewsID, "addon_instance", plugin)
	_fake_input_core(monkeypatch, [])
	assert notificationManager.reader_gesture_text() == "nvda+shift+/"


def test_keys_changed_in_input_gestures(monkeypatch):
	plugin = types.SimpleNamespace(_gestureMap={"kb:nvda+shift+/": _script_openNewsReader})
	monkeypatch.setattr(nusaNewsID, "addon_instance", plugin)
	removed = [(nusaNewsID.GlobalPlugin, "kb:nvda+shift+/", None)]
	_fake_input_core(monkeypatch, removed)
	assert notificationManager.reader_gesture_text() is None
	_fake_input_core(monkeypatch, [*removed, (nusaNewsID.GlobalPlugin, "kb:nvda+alt+n", "openNewsReader")])
	assert notificationManager.reader_gesture_text() == "nvda+alt+n"
