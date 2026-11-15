# -*- coding: utf-8 -*-
# __init__.py
#
# The global plugin: starts the background MonitorThread that checks the news sites,
# and opens the news reader with NVDA+Shift+/.
# Network requests run only in the thread. Settings are read on the main thread and handed to it,
# and everything that touches the cache, wx or speech runs on the main thread through wx.CallAfter.

import threading

import globalPluginHandler
import globalVars
import logHandler
import ui
import wx
from scriptHandler import script

from . import cache, config
from .notificationManager import NotificationManager
from .providers.sourceManager import SourceManager

# The running plugin, for the GUI. None while the add-on is not running.
addon_instance = None

STARTUP_DELAY_SECONDS = 5.0


class MonitorThread(threading.Thread):
	"""Background thread that checks the enabled sources every refresh interval."""

	def __init__(self, plugin: "GlobalPlugin"):
		super().__init__(name="NusaNewsMonitor", daemon=True)
		self._plugin = plugin
		self.stop_event = threading.Event()
		self._wake_event = threading.Event()
		self.source_manager = SourceManager(self.stop_event)

	def stop(self) -> None:
		"""Ask the thread to stop. It ends after the request that is running now, if any."""
		self.stop_event.set()
		self._wake_event.set()

	def wake(self) -> None:
		"""Start the next check now instead of at the end of the interval."""
		self._wake_event.set()

	def run(self) -> None:
		logHandler.log.info("NusaNews: Background news monitor started.")
		# Let NVDA finish starting before the first check.
		if self.stop_event.wait(STARTUP_DELAY_SECONDS):
			return
		while not self.stop_event.is_set():
			self._wake_event.clear()
			# A plain dict replaced as a whole on the main thread, so reading it here is safe.
			settings = self._plugin.settings
			try:
				items = self.source_manager.poll_sources(
					enabled_sources=settings["enabled_sources"],
					enabled_categories=settings["category_filter"],
					bypass_ssl=settings["bypass_ssl_verification"],
				)
			except Exception:
				logHandler.log.exception("NusaNews: News check failed.")
				items = []
			if self.stop_event.is_set():
				break
			wx.CallAfter(self._plugin.on_check_finished, self, items)
			self._wake_event.wait(settings["refresh_interval"] * 60)
		logHandler.log.info("NusaNews: Background news monitor stopped.")


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	"""Main NusaNews add-on controller."""

	scriptCategory = "nusaNewsID"

	def __init__(self):
		super().__init__()
		global addon_instance
		self.monitor_thread: MonitorThread | None = None
		self.notification_manager = NotificationManager()
		self._manual_refresh_pending = False
		self.settings: dict = {}
		# No network access, settings panel or reader on secure screens such as the sign-in screen.
		if globalVars.appArgs.secure:
			logHandler.log.debug("NusaNews: Secure screen, the add-on stays inactive.")
			return
		addon_instance = self

		config.initialize_config()
		self.settings = config.read_settings()
		cache.init_db()
		cache.prune_cache(self.settings["cache_duration"])

		from .gui import NusaNewsSettingsPanel
		import gui

		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(NusaNewsSettingsPanel)

		self.monitor_thread = MonitorThread(self)
		self.monitor_thread.start()

	def terminate(self, *args, **kwargs):
		"""Stop the thread without waiting for a request to finish, and remove the settings panel."""
		global addon_instance
		if self.monitor_thread is not None:
			self.monitor_thread.stop()
			self.monitor_thread.join(timeout=1.0)
			self.monitor_thread = None
		if addon_instance is self:
			from .gui import NusaNewsSettingsPanel
			import gui

			try:
				gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(NusaNewsSettingsPanel)
			except ValueError:
				pass
			addon_instance = None
		super().terminate(*args, **kwargs)

	def apply_settings(self) -> None:
		"""Read the saved settings again and start a new check with them. Main thread only."""
		self.settings = config.read_settings()
		if self.monitor_thread is not None:
			self.monitor_thread.wake()

	def request_refresh(self) -> bool:
		"""Check the news now. The result is announced when the check ends. Main thread only."""
		if self.monitor_thread is None:
			return False
		self._manual_refresh_pending = True
		self.monitor_thread.wake()
		return True

	def on_check_finished(self, thread: MonitorThread, items: list) -> None:
		"""Save the stories from a finished check and announce the new ones. Runs on the main thread."""
		if thread is not self.monitor_thread or thread.stop_event.is_set():
			# A check from a thread that was stopped meanwhile, for example while add-ons were reloaded.
			return
		try:
			new_items = cache.save_news_items(items) if items else []
		except Exception:
			logHandler.log.exception("NusaNews: Saving the stories failed.")
			return
		if self._manual_refresh_pending:
			self._manual_refresh_pending = False
			if new_items:
				ui.message(f"Selesai, {len(new_items)} berita baru.")
			else:
				ui.message("Selesai, tidak ada berita baru.")
		elif new_items:
			self.notification_manager.notify_new_items(new_items)
		if new_items:
			from .gui import refresh_active_dialog

			refresh_active_dialog()

	@script(
		gesture="kb:NVDA+Shift+/",
		description="Membuka pembaca berita NusaNews",
		category="nusaNewsID",
	)
	def script_openNewsReader(self, gesture):
		"""Open the news reader dialog."""
		if globalVars.appArgs.secure:
			return
		from .gui import open_news_dialog

		wx.CallAfter(open_news_dialog)
