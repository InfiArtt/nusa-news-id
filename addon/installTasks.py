# installTasks.py
#
# Runs when NVDA installs or removes the add-on: a welcome dialog, and the settings section.

import addonHandler
import gui
import wx

addonHandler.initTranslation()


class DonationDialog(wx.Dialog):
	"""Read-only donation information.

	The same dialog as in gui.py, which cannot be imported while the add-on is being installed.
	"""

	def __init__(self, parent):
		# Translators: title of the donation dialog.
		super().__init__(parent, title=_("Donate to NusaNewsID"), style=wx.DEFAULT_DIALOG_STYLE)
		sizer = wx.BoxSizer(wx.VERTICAL)
		# Translators: the text of the donation dialog. Keep the phone number and the name.
		msg = _(
			"You can donate through GoPay to 088222553434, under the name Rexya Muhamad Rizki.\n\n"
			"Every donation helps keep this add-on going. Thank you!"
		)
		# Translators: label of the text box in the donation dialog.
		sizer.Add(wx.StaticText(self, label=_("Donation information:")), 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
		text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(400, 150))
		text.SetValue(msg)
		sizer.Add(text, 1, wx.EXPAND | wx.ALL, 10)
		# Translators: button that closes a dialog.
		btn = wx.Button(self, wx.ID_OK, label=_("&Close"))
		sizer.Add(btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
		self.SetSizerAndFit(sizer)
		self.Centre()
		text.SetFocus()


class WelcomeDialog(wx.Dialog):
	"""Shown when the add-on is installed."""

	def __init__(self, parent):
		# Translators: title of the dialog shown when the add-on is installed.
		super().__init__(parent, title=_("Welcome to NusaNewsID"), style=wx.DEFAULT_DIALOG_STYLE)
		sizer = wx.BoxSizer(wx.VERTICAL)
		# Translators: the text of the dialog shown when the add-on is installed.
		# Keep NVDA+Shift+/ and the name.
		msg = _(
			"Thank you for installing NusaNewsID.\n\n"
			"This add-on reads news from Indonesian news sites and is made for screen reader users.\n\n"
			"You can filter the news by source and category.\n"
			"To open the news list, press NVDA+Shift+/.\n\n"
			"Made by Rexya Muhamad Rizki. You can support its development with the Donate button."
		)
		# Translators: label of the text box in the welcome dialog.
		sizer.Add(wx.StaticText(self, label=_("About NusaNewsID:")), 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
		self.text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(450, 200))
		self.text.SetValue(msg)
		sizer.Add(self.text, 1, wx.EXPAND | wx.ALL, 10)

		btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: button that closes the welcome dialog so the installation goes on.
		self.btn_continue = wx.Button(self, label=_("&Continue installing"))
		# Translators: button that opens the donation dialog.
		self.btn_donate = wx.Button(self, label=_("D&onate"))
		btn_sizer.Add(self.btn_continue, 0, wx.RIGHT, 10)
		btn_sizer.Add(self.btn_donate, 0)
		sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

		self.btn_continue.Bind(wx.EVT_BUTTON, self.on_continue)
		self.btn_donate.Bind(wx.EVT_BUTTON, self.on_donate)
		self.SetSizerAndFit(sizer)
		self.Centre()
		# Start on the text, so NVDA reads the welcome first.
		self.text.SetFocus()

	def on_continue(self, event):
		self.EndModal(wx.ID_OK)

	def on_donate(self, event):
		dlg = DonationDialog(self)
		dlg.ShowModal()
		dlg.Destroy()


def _loadConfigSpec():
	"""The add-on's settings specification, from its own module, without importing the add-on."""
	import importlib.util
	import os

	path = os.path.join(os.path.dirname(__file__), "globalPlugins", "nusaNewsID", "configSpec.py")
	spec = importlib.util.spec_from_file_location("nusaNewsID_configSpec", path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def _registerSettings():
	"""From NVDA 2026.3: register the settings section, the same in every profile, loaded at NVDA's start."""
	try:
		from config import configSections
	except ImportError:
		return
	configSpec = _loadConfigSpec()
	configSections.registerSection(configSpec.CONFIG_SECTION, configSpec.CONFIG_SPEC, isBaseOnly=True)


def onInstall():
	"""Hook executed by NVDA when the addon is installed."""
	try:
		_registerSettings()
	except Exception:
		import logHandler

		logHandler.log.exception("NusaNews: Registering the settings section failed.")

	def show_welcome():
		app = wx.GetApp()
		if app and hasattr(gui, "mainFrame"):
			dlg = WelcomeDialog(gui.mainFrame)
			dlg.ShowModal()
			dlg.Destroy()

	# NVDA executes onInstall in a background thread during addon installation.
	# We must use wx.CallAfter to safely spawn GUI elements on the main thread.
	wx.CallAfter(show_welcome)


def onUninstall():
	"""Hook executed by NVDA when the add-on is removed: forget the settings section."""
	try:
		from config import configSections
	except ImportError:
		return
	configSections.unregisterSection("nusaNewsID")
