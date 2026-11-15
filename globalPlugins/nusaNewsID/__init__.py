# -*- coding: utf-8 -*-
# __init__.py
#
# Documentation Compliance Notes:
# - Inherits from globalPluginHandler.GlobalPlugin and registers keyboard gestures.
# - Audits secure screens via globalVars.appArgs.secure and disables network operations inside lock screen profiles.
# Threading Notes:
# - Spawns a background MonitorThread to carry out blocking network operations (polling).
# - Dispatches parsed items to the main thread via wx.CallAfter to guarantee database writes occur on the main thread.
# Lifecycle Notes:
# - GlobalPlugin startup initializes the schema database, loads configurations, and starts the thread.
# - terminate() sets the stop event, safely joins the thread within 1.0s, and cleans up database handles.
# Design Explanation:
# - Exposes Alt/Shift gestures to summon the reader GUI.
# - Uses a dynamic reload configuration strategy by recreating the MonitorThread when intervals are updated.

import threading
import wx
import globalPluginHandler
import globalVars
import logHandler
from scriptHandler import script

from . import config
from . import cache
from .notificationManager import NotificationManager
from .providers.sourceManager import SourceManager

# Global pointer to the active addon instance for GUI access
addon_instance = None

class MonitorThread(threading.Thread):
	"""Background daemon thread executing Indonesian news aggregation loop."""
	def __init__(self, stop_event: threading.Event):
		super().__init__()
		self.stop_event = stop_event
		self.source_manager = SourceManager()
		self.notification_manager = NotificationManager()
		self.daemon = True

	def run(self):
		logHandler.log.info("NusaNews: MonitorThread background polling thread started.")
		
		# Pause briefly on startup to let NVDA finish loaded operations
		self.stop_event.wait(5.0)
		
		while not self.stop_event.is_set():
			try:
				# Load configuration states synchronously
				refresh_interval = config.get_config_val("refresh_interval")
				enabled_sources = config.get_config_val("enabled_sources")
				enabled_categories = config.get_config_val("category_filter")
				bypass_ssl = config.get_config_val("bypass_ssl_verification")
				
				if enabled_sources and enabled_categories:
					# Network requests (blocking) are allowed inside background thread
					items = self.source_manager.poll_sources(
						enabled_sources=enabled_sources,
						enabled_categories=enabled_categories,
						bypass_ssl=bypass_ssl
					)
					
					# Confirm execution states before database dispatching
					if items and not self.stop_event.is_set():
						# Option A: database operations occur strictly on the main thread
						wx.CallAfter(self._main_thread_db_dispatch, items)
			except Exception as e:
				logHandler.log.error(f"NusaNews: MonitorThread encountered unhandled exception: {e}")
				
			# Convert minutes to seconds for interval sleep
			interval_seconds = refresh_interval * 60
			# Sleep via interruptible wait event
			if self.stop_event.wait(interval_seconds):
				break

	def _main_thread_db_dispatch(self, items):
		"""Callback executed on the main thread via wx.CallAfter to save and notify."""
		try:
			# Cache items and check for duplicates (returns list of new, unseen items)
			new_items = cache.save_news_items(items)
			
			if new_items:
				# Process alerts, sound tones, and speeches
				self.notification_manager.notify_new_items(new_items)
				
				# If reader dialog is open, trigger UI list refresh
				from .gui import refresh_active_dialog
				refresh_active_dialog()
		except Exception as e:
			logHandler.log.error(f"NusaNews: Main thread callback news insertion failed: {e}")


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	"""Main NusaNews addon controller."""
	scriptCategory = "nusaNewsID"

	def __init__(self):
		super().__init__()
		global addon_instance
		addon_instance = self

		# Initialize native configurations
		config.initialize_config()
		
		# Restrict network operations inside secure locks
		self.secure_mode = globalVars.appArgs.secure
		if self.secure_mode:
			logHandler.log.warning("NusaNews: Locked in secure mode. Background monitoring disabled.")
			return
			
		# Initialize local database tables and indexes
		cache.init_db()

		# Thread components
		self.monitor_thread = None
		self.stop_event = None
		self.start_monitor()

		# Run initial pruning to clear historical expired caches
		retention_days = config.get_config_val("cache_duration")
		cache.prune_cache(retention_days)

		# Append settings categories in NVDA
		from .gui import NusaNewsSettingsPanel
		try:
			import gui
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(NusaNewsSettingsPanel)
		except Exception as e:
			logHandler.log.error(f"NusaNews: Failed to append Settings categories: {e}")

	def terminate(self):
		"""Executes cleanup, joins threads, and unregisters widgets."""
		self.stop_monitor()

		# Remove Settings panel
		from .gui import NusaNewsSettingsPanel
		try:
			import gui
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(NusaNewsSettingsPanel)
		except Exception as e:
			logHandler.log.debug(f"NusaNews: Failed to remove Settings categories on terminate: {e}")

		global addon_instance
		addon_instance = None
		super().terminate()

	def start_monitor(self):
		"""Instantiates and starts the background MonitorThread."""
		if self.secure_mode:
			return
		self.stop_event = threading.Event()
		self.monitor_thread = MonitorThread(self.stop_event)
		self.monitor_thread.start()
		logHandler.log.info("NusaNews: Background news monitor started.")

	def stop_monitor(self):
		"""Sets the exit event and joins the thread."""
		if self.stop_event:
			self.stop_event.set()
		if self.monitor_thread:
			# Enforce 1.0s timeout to prevent locking NVDA exits
			self.monitor_thread.join(timeout=1.0)
			self.monitor_thread = None
			self.stop_event = None
			logHandler.log.info("NusaNews: Background news monitor stopped.")

	def reload_monitor(self):
		"""Restarts the monitoring thread immediately with updated configs."""
		logHandler.log.info("NusaNews: Reloading background monitoring thread configs.")
		self.stop_monitor()
		self.start_monitor()

	@script(
		gesture="kb:NVDA+Shift+/",
		description="Membuka pembaca berita NusaNews",
		category="nusaNewsID"
	)
	def script_openNewsReader(self, gesture):
		"""Keyboard gesture script showing the accessible listbox dialog."""
		from .gui import open_news_dialog
		# Marshal GUI creation to the main thread safely
		wx.CallAfter(open_news_dialog)
