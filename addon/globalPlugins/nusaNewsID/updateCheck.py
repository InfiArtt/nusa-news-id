# updateCheck.py
#
# Asks about a new version from GitHub, shows what changed in it, and installs it with NVDA's own add-on
# installer. Taken from InfiArtt's WhatsApp Access add-on. Everything here runs on the main thread, except
# the work functions, which run in their own threads and come back with wx.CallAfter.

import os
import shutil
import tempfile
import threading
import time

import addonHandler
import gui
import logHandler
import ui
import wx
from gui import addonGui, guiHelper

from . import config, updates

addonHandler.initTranslation()

# Checked by itself at most once a day, a while after NVDA starts.
AUTO_CHECK_DELAY_MS = 30000
AUTO_CHECK_EVERY_SECONDS = 24 * 3600

_busy = False
"""Set from the start of a check until its offer is declined or its download is installed or fails, so two
checks never open two windows or download into the same file."""


def current_version() -> str:
	return addonHandler.getCodeAddon().version


def schedule_auto_check() -> wx.CallLater | None:
	"""Check by itself a while after NVDA starts, when the setting is on and the last check is a day old.

	:return: The timer, for the plugin to stop if it is stopped first.
	"""
	if not config.get_config_val("check_updates"):
		return None
	if time.time() - config.get_config_val("last_update_check") < AUTO_CHECK_EVERY_SECONDS:
		return None
	return wx.CallLater(AUTO_CHECK_DELAY_MS, check, False)


def _done() -> None:
	global _busy
	_busy = False


def check(manual: bool) -> None:
	"""Look for a newer release. manual says whether the user asked: only then is "no update" said."""
	global _busy
	if _busy:
		if manual:
			# Translators: said when the user checks for updates while a check or download is going on.
			ui.message(_("Already checking for updates. The answer comes in a moment."))
		return
	_busy = True
	if manual:
		# Translators: said while the add-on looks for a new version.
		ui.message(_("Checking for updates..."))
	current = current_version()

	def work() -> None:
		offered = False
		try:
			try:
				release = updates.latest_release()
			except updates.UpdateError as e:
				logHandler.log.info(f"NusaNews: Update check: {e}")
				if manual:
					wx.CallAfter(_failed, str(e))
				return
			wx.CallAfter(config.set_config_val, "last_update_check", int(time.time()))
			if updates.is_newer(release.version, current):
				wx.CallAfter(_offer, release)
				offered = True
			elif manual:
				wx.CallAfter(
					ui.message,
					# Translators: said when the user checked for a new version and has the newest one.
					_("You have the newest version, {version}.").format(version=current),
				)
		finally:
			# Once offered, the offer says when it is over.
			if not offered:
				_done()

	try:
		threading.Thread(target=work, name="NusaNewsUpdateCheck", daemon=True).start()
	except BaseException:
		_done()
		raise


def _failed(error: str) -> None:
	if error == "noRelease":
		# Translators: said when the add-on's GitHub page has no published version yet.
		message = _("No version has been published on GitHub yet.")
	else:
		# Translators: said when looking for a new version failed, such as with no internet connection.
		message = _("Could not check for updates. Check your internet connection and try again.")
	ui.message(message)


def _offer(release: updates.Release) -> None:
	answer = wx.ID_CANCEL
	try:
		dialog = UpdateDialog(gui.mainFrame, release)
		gui.mainFrame.prePopup()
		try:
			answer = dialog.ShowModal()
		finally:
			dialog.Destroy()
			gui.mainFrame.postPopup()
	finally:
		if answer != wx.ID_OK:
			_done()
	if answer == wx.ID_OK:
		_download(release)


def _remove_folder(folder: str) -> None:
	shutil.rmtree(folder, ignore_errors=True)


def _download(release: updates.Release) -> None:
	def work() -> None:
		# A folder of its own for each download: nobody else's file is used or replaced, and it is all
		# removed afterwards.
		folder = ""
		installing = False
		try:
			folder = tempfile.mkdtemp(prefix="nusaNewsID-update-")
			path = os.path.join(folder, release.file_name)
			updates.download(release, path)
			wx.CallAfter(_install, folder, path)
			installing = True
		except (updates.UpdateError, OSError) as e:
			logHandler.log.info(f"NusaNews: Update download: {e}")
			wx.CallAfter(
				ui.message,
				# Translators: said when the new version could not be downloaded or was damaged.
				_("The new version could not be downloaded. Try again later."),
			)
		finally:
			# Once handed to the installer, it removes the folder when done.
			if not installing:
				if folder:
					_remove_folder(folder)
				_done()

	try:
		# Translators: said while a new version of the add-on downloads, for example
		# "Downloading NusaNewsID 1.2.0...".
		ui.message(_("Downloading NusaNewsID {version}...").format(version=release.version))
		threading.Thread(target=work, name="NusaNewsUpdateDownload", daemon=True).start()
	except BaseException:
		_done()
		raise


def _install(folder: str, path: str) -> None:
	try:
		# NVDA's own installer checks the file, asks about compatibility, and copies the add-on for the
		# restart, so the downloaded file is no longer needed once it returns.
		installed = addonGui.installAddon(gui.mainFrame, path)
	finally:
		_remove_folder(folder)
		_done()
	if installed:
		addonGui.promptUserForRestart()


class UpdateDialog(wx.Dialog):
	"""A new version, what changed in it, and whether to install it now."""

	def __init__(self, parent: wx.Window, release: updates.Release) -> None:
		# Translators: the title of the window that offers a new version of the add-on.
		super().__init__(
			parent, title=_("NusaNewsID update"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
		)
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		intro = wx.StaticText(
			self,
			# Translators: the top of the window that offers a new version, with both version numbers.
			label=_("NusaNewsID {new} is available. You have version {current}.").format(
				new=release.version, current=current_version()
			),
		)
		intro.Wrap(self.FromDIP(560))
		sHelper.addItem(intro)
		self.notes = sHelper.addLabeledControl(
			# Translators: the label of the text that says what changed in the new version.
			_("&What's new:"),
			wx.TextCtrl,
			# Translators: shown when a new version has no description of its changes.
			value=release.notes or _("No description."),
			style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
			size=self.FromDIP(wx.Size(560, 320)),
		)
		buttons = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: a button that downloads and installs the new version.
		install = buttons.addButton(self, id=wx.ID_OK, label=_("&Download and install"))
		install.SetDefault()
		# Translators: a button that closes the update window; the add-on asks again another day.
		buttons.addButton(self, id=wx.ID_CANCEL, label=_("&Not now"))
		sHelper.addDialogDismissButtons(buttons)
		main = wx.BoxSizer(wx.VERTICAL)
		main.Add(sHelper.sizer, 1, wx.EXPAND | wx.ALL, guiHelper.BORDER_FOR_DIALOGS)
		self.SetSizerAndFit(main)
		self.SetEscapeId(wx.ID_CANCEL)
		self.CentreOnScreen()
		# The changes come first, as in WhatsApp Access: NVDA reads them from the top.
		self.notes.SetFocus()
		self.notes.SetInsertionPoint(0)
