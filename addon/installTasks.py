# installTasks.py
#
# Runs when NVDA installs or removes the add-on: the welcome with its donation invitation, as in InfiArtt's
# Emoji ID add-on, and the settings section.
# Only NVDA's own message dialogs are used, run on the main thread with wxCallOnMain, so the installation
# waits for the user without blocking NVDA.

import addonHandler
import api
import config
import gui
import logHandler
from gui.guiHelper import wxCallOnMain
from gui.message import MessageDialog, ReturnCode

# Keep in sync with globalPlugins/nusaNewsID/donation.py, which cannot be imported while installing.
GOPAY_NUMBER = "085128011831"
GOPAY_NAME = "Rexya Muhamad Rizki"
CONFIG_SECTION = "nusaNewsID"


def _show_welcome() -> None:
	"""Invite the user to donate and, if they agree, show and copy the GoPay number. Main thread."""
	gui.mainFrame.prePopup()
	try:
		answer = MessageDialog.confirm(
			_(
				# Translators: the welcome shown while the add-on is being installed. Keep NVDA+Shift+/.
				"Welcome to NusaNewsID!\n\n"
				"This add-on follows Indonesian news sites in the background, announces new stories, and "
				"opens whole articles in a window made for screen readers. Press NVDA+Shift+/ to open the "
				"news list.\n\n"
				"If this add-on helps you, you can support its developer with a voluntary donation through "
				"GoPay. Choose Donate to see the number, or Not now to go on with the installation."
			),
			# Translators: title of the welcome shown while the add-on is being installed.
			_("Welcome to NusaNewsID"),
			# Translators: button of the installation welcome that shows the donation details.
			okLabel=_("&Donate"),
			# Translators: button of the installation welcome that goes on with the installation.
			cancelLabel=_("&Not now"),
		)
		if answer != ReturnCode.OK:
			return
		copied = api.copyToClip(GOPAY_NUMBER)
		details = _(
			# Translators: the donation details. {number} is the GoPay phone number, {name} the account
			# holder.
			"Support the NusaNewsID developer\n\n"
			"Method: GoPay\n"
			"Phone number: {number}\n"
			"Name: {name}\n\n"
			"Every donation, whatever the amount, helps keep this add-on updated. Thank you!"
		).format(number=GOPAY_NUMBER, name=GOPAY_NAME)
		if copied:
			# Translators: added to the donation details after the GoPay number was copied.
			details += "\n\n" + _("The GoPay number has been copied to the clipboard.")
		MessageDialog.alert(
			details,
			# Translators: title of the dialog that shows the GoPay donation details.
			_("GoPay donation - NusaNewsID"),
		)
	finally:
		gui.mainFrame.postPopup()


def _mark_welcome_shown() -> None:
	"""Stop the add-on from showing the welcome again after NVDA restarts."""
	spec = config.conf.spec.setdefault(CONFIG_SECTION, {})
	spec.setdefault("first_run", "boolean(default=True)")
	config.conf[CONFIG_SECTION]["first_run"] = False
	config.conf.save()


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
	"""Hook executed by NVDA when the add-on is installed."""
	# Translations are loaded here rather than when the module is imported: NVDA also imports this module
	# from the old version while it installs an update, and gettext would then keep the old catalog.
	addonHandler.initTranslation()
	try:
		_registerSettings()
	except Exception:
		logHandler.log.exception("NusaNews: Registering the settings section failed.")
	try:
		wxCallOnMain(_show_welcome)
	except Exception:
		# A failed dialog must never fail the installation; the add-on shows its welcome after the restart.
		logHandler.log.exception("NusaNews: Showing the installation welcome failed.")
		return
	try:
		wxCallOnMain(_mark_welcome_shown)
	except Exception:
		logHandler.log.exception("NusaNews: Saving that the welcome was shown failed.")


def onUninstall():
	"""Hook executed by NVDA when the add-on is removed: forget the settings section."""
	try:
		from config import configSections
	except ImportError:
		return
	configSections.unregisterSection(CONFIG_SECTION)
