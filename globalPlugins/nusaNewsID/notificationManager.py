# -*- coding: utf-8 -*-
# notificationManager.py
#
# Documentation Compliance Notes:
# - Written in standard Python 3.13, compatible with NVDA 2026.1+.
# - Uses standard ui.message() to announce news to speech and braille.
# Threading Notes:
# - Invoked strictly on the main thread via wx.CallAfter callbacks.
# Lifecycle Notes:
# - Runs on every fetch cycle where the database identifies new, unseen articles.
# Design Explanation:
# - Handles speech throttling to prevent screen reader flood.
# - Enforces DND quiet hours, triggers notification beeps, and processes breaking news overrides.

import datetime
import ui
import tones
import logHandler
from typing import List
from .models import NewsItem
from . import config

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
	
	def notify_new_items(self, new_items: List[NewsItem]):
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

	def _dispatch_notifications(self, items: List[NewsItem], mode: str, play_tone: bool):
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
		"""Speaks a summary digest message instead of flooding."""
		gesture_str = "NVDA+Shift+/"
		try:
			from . import addon_instance
			if addon_instance and hasattr(addon_instance, "_gestureMap"):
				for gesture, script_name in addon_instance._gestureMap.items():
					if script_name == "openNewsReader":
						clean = gesture
						if clean.startswith("kb:"):
							clean = clean[3:]
						parts = []
						for part in clean.split("+"):
							if part.lower() == "nvda":
								parts.append("NVDA")
							elif part.lower() == "shift":
								parts.append("Shift")
							elif part.lower() == "control":
								parts.append("Control")
							elif part.lower() == "alt":
								parts.append("Alt")
							else:
								parts.append(part.upper())
						gesture_str = "+".join(parts)
		except Exception:
			pass
		message = f"NusaNews: {count} berita baru tersedia. Tekan {gesture_str} untuk membuka."
		ui.message(message)

	def _speak_immediate(self, items: List[NewsItem]):
		"""Speaks each news item individually."""
		for item in items:
			ui.message(item.format_announcement())
