# __init__.py
#
# The global plugin: starts the background MonitorThread that checks the news sites,
# and opens the news reader with NVDA+Shift+/.
# Network requests run only in the thread. Settings are read on the main thread and handed to it,
# and everything that touches the cache, wx or speech runs on the main thread through wx.CallAfter.

import contextlib
import threading

import addonHandler
import globalPluginHandler
import globalVars
import logHandler
import ui
import wx
from scriptHandler import script

from . import cache, config
from .configSpec import DATA_VERSION
from .notificationManager import NotificationManager
from .providers.sourceManager import ALWAYS_ON_SOURCES, SourceManager

addonHandler.initTranslation()

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
					max_age_days=settings["cache_duration"],
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

	# The add-on's name, the same in every language.
	scriptCategory = "NusaNewsID"

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
		self._upgrade_saved_data()
		cache.prune_cache(self.settings["cache_duration"], keep_sources=ALWAYS_ON_SOURCES)

		import gui

		from .gui import NusaNewsSettingsPanel

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
			cache.flush()
		if addon_instance is self:
			import gui

			from .gui import NusaNewsSettingsPanel

			with contextlib.suppress(ValueError):
				gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(NusaNewsSettingsPanel)
			addon_instance = None
		super().terminate(*args, **kwargs)

	def _upgrade_saved_data(self) -> None:
		"""Once per data version: bring the settings and cache of an older version up to date."""
		if config.get_config_val("data_version") >= DATA_VERSION:
			return
		# Version 1.0.2 never marked stories as read by itself, so thousands were "Belum dibaca".
		# Marking them read makes "Belum dibaca" mean new since this version.
		cache.mark_all_as_read()
		config.set_config_val("data_version", DATA_VERSION)
		logHandler.log.info("NusaNews: Marked the stories of the older version as read.")

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
			cache.prune_cache(self.settings["cache_duration"], keep_sources=ALWAYS_ON_SOURCES)
			# The first fill of an empty cache (new install, or after clearing it) is saved as read and
			# not announced story by story: all of them would be "new". The same goes for a source with no
			# saved story yet, such as one just turned on, or InfiArtt with its whole archive.
			first_fill = cache.is_empty()
			cached_sources = cache.sources()
			quiet_sources = {item.source for item in items} - cached_sources
			new_items = (
				cache.save_news_items(
					items,
					mark_seen=first_fill,
					quiet_sources=quiet_sources,
					refresh_sources=ALWAYS_ON_SOURCES,
				)
				if items
				else []
			)
		except Exception:
			logHandler.log.exception("NusaNews: Saving the stories failed.")
			return
		if first_fill and new_items:
			self._manual_refresh_pending = False
			count = len(new_items)
			# Translators: said once after the first check of an empty cache, which saves stories without
			# announcing each of them.
			ui.message(
				ngettext(
					"NusaNews: {count} story loaded.", "NusaNews: {count} stories loaded.", count
				).format(count=count)
			)
		elif self._manual_refresh_pending:
			self._manual_refresh_pending = False
			if new_items:
				count = len(new_items)
				# Translators: said when a check started with the Refresh button finds new stories.
				ui.message(
					ngettext("Done, {count} new story.", "Done, {count} new stories.", count).format(
						count=count
					)
				)
			else:
				# Translators: said when a check started with the Refresh button finds nothing new.
				ui.message(_("Done, no new stories."))
		elif new_items:
			announced = [item for item in new_items if item.source not in quiet_sources]
			if announced:
				self.notification_manager.notify_new_items(announced)
		if new_items:
			from .gui import refresh_active_dialog

			refresh_active_dialog()

	@script(
		gesture="kb:NVDA+Shift+/",
		# Translators: describes the command that opens the news list, in Input Gestures.
		description=_("Opens the NusaNews news list"),
		category="NusaNewsID",
	)
	def script_openNewsReader(self, gesture):
		"""Open the news reader dialog."""
		if globalVars.appArgs.secure:
			return
		from .gui import open_news_dialog

		wx.CallAfter(open_news_dialog)
