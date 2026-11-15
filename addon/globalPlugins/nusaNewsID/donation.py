# donation.py
#
# The welcome, the donation reminder and the donation details, the same as in InfiArtt's Emoji ID add-on.
# Everything here runs on the main thread.

import addonHandler
import api
import gui
import logHandler
import ui
import wx

addonHandler.initTranslation()

# Keep in sync with installTasks.py, which cannot import the add-on while it is being installed.
GOPAY_NUMBER = "085128011831"
GOPAY_NAME = "Rexya Muhamad Rizki"


def _show_modal(dialog: wx.Dialog) -> int:
	"""Show a modal dialog with NVDA's pre and post popup handling, then destroy it."""
	gui.mainFrame.prePopup()
	try:
		return dialog.ShowModal()
	finally:
		dialog.Destroy()
		gui.mainFrame.postPopup()


def details_text() -> str:
	return _(
		# Translators: the donation details. {number} is the GoPay phone number, {name} the account holder.
		"Support the NusaNewsID developer\n\n"
		"Method: GoPay\n"
		"Phone number: {number}\n"
		"Name: {name}\n\n"
		"Every donation, whatever the amount, helps keep this add-on updated. Thank you!"
	).format(number=GOPAY_NUMBER, name=GOPAY_NAME)


class DonationDetailsDialog(wx.Dialog):
	"""The GoPay account details, with a button that copies the number."""

	def __init__(self, parent: wx.Window | None) -> None:
		# Translators: title of the dialog that shows the GoPay donation details.
		super().__init__(parent, title=_("GoPay donation - NusaNewsID"))
		sizer = wx.BoxSizer(wx.VERTICAL)
		# Translators: label of the text box with the donation details.
		sizer.Add(
			wx.StaticText(self, label=_("Donation details:")), flag=wx.LEFT | wx.RIGHT | wx.TOP, border=10
		)
		self.details = wx.TextCtrl(
			self,
			value=details_text(),
			style=wx.TE_MULTILINE | wx.TE_READONLY,
			size=self.FromDIP(wx.Size(480, 200)),
		)
		sizer.Add(self.details, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
		buttons = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: button that copies the GoPay number to the clipboard.
		copy = wx.Button(self, label=_("Co&py number"))
		copy.Bind(wx.EVT_BUTTON, self._on_copy)
		buttons.Add(copy, flag=wx.RIGHT, border=10)
		# Translators: button that closes a dialog.
		buttons.Add(wx.Button(self, wx.ID_CANCEL, label=_("&Close")))
		sizer.Add(buttons, flag=wx.ALIGN_RIGHT | wx.ALL, border=10)
		self.SetSizerAndFit(sizer)
		self.CentreOnScreen()
		self.details.SetFocus()
		self.details.SetInsertionPoint(0)

	def _on_copy(self, event: wx.CommandEvent) -> None:
		if api.copyToClip(GOPAY_NUMBER):
			# Translators: said after the GoPay number is copied. {number} is the number.
			ui.message(_("GoPay number {number} copied.").format(number=GOPAY_NUMBER))
		else:
			# Translators: said when the GoPay number could not be copied.
			ui.message(_("Could not copy the number."))


class DonationInviteDialog(wx.Dialog):
	"""A short message inviting the user to donate, with Donate and Not now buttons."""

	def __init__(self, parent: wx.Window | None, title: str, message: str) -> None:
		super().__init__(parent, title=title)
		sizer = wx.BoxSizer(wx.VERTICAL)
		text = wx.StaticText(self, label=message)
		text.Wrap(self.FromDIP(500))
		sizer.Add(text, flag=wx.ALL | wx.EXPAND, border=15)
		buttons = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: button that opens the donation details.
		donate = wx.Button(self, label=_("&Donate"))
		donate.Bind(wx.EVT_BUTTON, lambda event: show_donation_details(self))
		buttons.Add(donate, flag=wx.RIGHT, border=10)
		# Translators: button that closes the donation invitation.
		not_now = wx.Button(self, wx.ID_CANCEL, label=_("&Not now"))
		not_now.SetDefault()
		buttons.Add(not_now)
		sizer.Add(buttons, flag=wx.ALIGN_RIGHT | wx.ALL, border=15)
		self.SetSizerAndFit(sizer)
		self.CentreOnScreen()


def show_donation_details(parent: wx.Window | None = None) -> None:
	"""Open the GoPay donation details. Main thread only."""
	try:
		_show_modal(DonationDetailsDialog(parent or gui.mainFrame))
	except Exception:
		logHandler.log.exception("NusaNews: Showing the donation details failed.")


def _show_invite(title: str, message: str) -> None:
	try:
		_show_modal(DonationInviteDialog(gui.mainFrame, title, message))
	except Exception:
		logHandler.log.exception("NusaNews: Showing the donation invitation failed.")


def welcome_message() -> str:
	return _(
		# Translators: the welcome shown once after installing. Keep NVDA+Shift+/.
		"Welcome to NusaNewsID!\n\n"
		"This add-on follows Indonesian news sites in the background, announces new stories, and opens "
		"whole articles in a window made for screen readers. Press NVDA+Shift+/ to open the news list.\n\n"
		"If this add-on helps you, you can support its developer with a voluntary donation through GoPay. "
		"Choose Donate to see the number, or Not now to close this message."
	)


def show_welcome() -> None:
	"""The welcome shown once after installation, when the installer could not show it. Main thread only."""
	# Translators: title of the welcome shown once after installing.
	_show_invite(_("Welcome to NusaNewsID"), welcome_message())


def show_reminder() -> None:
	"""The occasional donation reminder, when turned on in the settings. Main thread only."""
	_show_invite(
		# Translators: title of the occasional donation reminder.
		_("Support the developer - NusaNewsID"),
		_(
			# Translators: the occasional donation reminder.
			"We hope NusaNewsID helps you keep up with the news every day.\n\n"
			"If you want this add-on to keep being updated, you can support its developer with a voluntary "
			"donation through GoPay. You can turn this reminder off in the NusaNewsID settings."
		),
	)
