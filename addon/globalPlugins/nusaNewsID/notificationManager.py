# notificationManager.py
#
# Announces new stories with speech and a tone, respecting quiet hours. Main thread only.

import datetime

import logHandler
import tones
import ui

from . import config
from .formatting import digest_text, notification_text
from .models import NewsItem


def is_in_silent_hours(start_str: str, end_str: str) -> bool:
	"""
	Calculates if the current local time falls within the configured DND range.
	Handles ranges that cross midnight (e.g. 22:00 to 06:00).
	"""
	try:
		now = datetime.datetime.now().time()
		start = datetime.datetime.strptime(start_str, "%H:%M").time()
		end = datetime.datetime.strptime(end_str, "%H:%M").time()

		if start <= end:
			return start <= now <= end
		else:
			return now >= start or now <= end
	except Exception as e:
		logHandler.log.error(f"NusaNews: Failed parsing quiet hours '{start_str}' to '{end_str}': {e}")
		return False


class NotificationManager:
	"""Manages accessible speech and audio notifications for NusaNews items."""

	def notify_new_items(self, new_items: list[NewsItem]):
		"""
		Main entry point. Evaluates incoming items and dispatches alerts on the main thread.
		"""
		if not new_items:
			return

		# Read configuration values from config.conf
		is_dnd_enabled = config.get_config_val("silent_hours_enabled")
		dnd_start = config.get_config_val("silent_hours_start")
		dnd_end = config.get_config_val("silent_hours_end")
		notification_mode = config.get_config_val("notification_mode")
		play_tone = config.get_config_val("notification_tone")
		breaking_override = config.get_config_val("breaking_news_preference")

		# Check if we are inside silent hours
		in_quiet_period = is_dnd_enabled and is_in_silent_hours(dnd_start, dnd_end)

		# Filter out breaking news items if we need to bypass DND
		breaking_items = [item for item in new_items if item.is_breaking]

		if in_quiet_period:
			if breaking_override and breaking_items:
				# Bypass DND only for breaking items
				self._dispatch_notifications(breaking_items, notification_mode, play_tone)
			else:
				# Suppress speech entirely. Items remain marked as unread in SQLite.
				logHandler.log.debug("NusaNews: Notification suppressed due to DND quiet hours.")
		else:
			self._dispatch_notifications(new_items, notification_mode, play_tone)

	def _dispatch_notifications(self, items: list[NewsItem], mode: str, play_tone: bool):
		"""Speaks the news based on settings and checks for speech floods."""
		if not items:
			return

		if play_tone:
			self._play_tone()

		# Handle speech flood prevention
		# If there are more than 5 items, consolidate them into a digest regardless of setting
		if len(items) > 5 or mode == "digest":
			self._speak_summary(len(items))
		else:
			self._speak_immediate(items)

	def _play_tone(self):
		"""Plays a short beep notification."""
		try:
			# Beep standard pitch for 100 milliseconds
			tones.beep(523, 100)  # High C beep
		except Exception as e:
			logHandler.log.warning(f"NusaNews: Failed to play notification beep: {e}")

	def _speak_summary(self, count: int):
		"""One message for several stories, naming the key that opens the reader."""
		ui.message(digest_text(count, reader_gesture_text()))

	def _speak_immediate(self, items: list[NewsItem]):
		"""Every story in one message, so a braille display shows them all, not only the last."""
		ui.message(" ".join(notification_text(item) for item in items))


SCRIPT_NAME = "openNewsReader"


def reader_gesture_text() -> str | None:
	"""The key that opens the reader now, as NVDA names it, including changes made in Input Gestures.

	None when the user removed every key for it.
	"""
	try:
		import inputCore

		from . import GlobalPlugin, addon_instance

		gestures = [
			gesture
			for gesture, script in (getattr(addon_instance, "_gestureMap", None) or {}).items()
			if script == SCRIPT_NAME
		]
		for cls, gesture, script in inputCore.manager.userGestureMap.getScriptsForAllGestures():
			if not issubclass(GlobalPlugin, cls) and cls is not GlobalPlugin:
				continue
			if script == SCRIPT_NAME:
				gestures.append(gesture)
			elif script is None and gesture in gestures:
				gestures.remove(gesture)
		for gesture in gestures:
			try:
				return inputCore.getDisplayTextForGestureIdentifier(gesture)[1]
			except LookupError:
				continue
	except Exception:
		logHandler.log.debugWarning("NusaNews: Could not find the reader's key.", exc_info=True)
	return None
