import gui
import wx


class DonationDialog(wx.Dialog):
	"""Dialog that displays read-only donation information."""

	def __init__(self, parent):
		super().__init__(parent, title="Donasi NusaNewsID", style=wx.DEFAULT_DIALOG_STYLE)
		sizer = wx.BoxSizer(wx.VERTICAL)

		msg = (
			"Lakukan donasi melalui go-pay 088222553434, atas nama rexya muhamad rizki.\n\n"
			"Setiap donasi Anda akan sangat membantu kelangsungan pengembangan add-on ini. "
			"Terima kasih orang baik!"
		)

		# Multiline, read-only text control for accessible reading
		text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(400, 150))
		text.SetValue(msg)
		# Ensure background color matches dialog panel for aesthetic consistency
		text.SetBackgroundColour(self.GetBackgroundColour())

		sizer.Add(text, 1, wx.EXPAND | wx.ALL, 10)

		btn = wx.Button(self, wx.ID_OK, label="&Tutup")
		sizer.Add(btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

		self.SetSizerAndFit(sizer)
		self.Centre()


class WelcomeDialog(wx.Dialog):
	"""Welcome dialog shown during addon installation."""

	def __init__(self, parent):
		super().__init__(parent, title="Selamat Datang di NusaNewsID", style=wx.DEFAULT_DIALOG_STYLE)
		sizer = wx.BoxSizer(wx.VERTICAL)

		msg = (
			"Terima kasih telah menginstal NusaNewsID!\n\n"
			"Addon ini berguna untuk membaca portal berita Indonesia dengan aksesibilitas tinggi "
			"untuk pengguna pembaca layar (Screen Reader).\n\n"
			"Anda dapat memfilter berita berdasarkan kategori dan sumber portal terkemuka di Indonesia.\n"
			"Pintasan default untuk membuka pembaca berita: NVDA+Shift+/\n\n"
			"Dikembangkan oleh: Rexya Muhamad Rizki\n"
			"Dukung pengembangan addon ini melalui Donasi."
		)

		# Define text as self.text so we can set focus to it later
		self.text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(450, 200))
		self.text.SetValue(msg)
		self.text.SetBackgroundColour(self.GetBackgroundColour())
		sizer.Add(self.text, 1, wx.EXPAND | wx.ALL, 10)

		btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.btn_continue = wx.Button(self, label="&Lanjutkan Instalasi")
		self.btn_donate = wx.Button(self, label="&Donasi")

		btn_sizer.Add(self.btn_continue, 0, wx.RIGHT, 10)
		btn_sizer.Add(self.btn_donate, 0)

		sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

		self.btn_continue.Bind(wx.EVT_BUTTON, self.on_continue)
		self.btn_donate.Bind(wx.EVT_BUTTON, self.on_donate)

		self.SetSizerAndFit(sizer)
		self.Centre()

		# Set focus to the text field instead of the continue button
		self.text.SetFocus()

	def on_continue(self, event):
		"""Close dialog and allow installation to proceed."""
		self.EndModal(wx.ID_OK)

	def on_donate(self, event):
		"""Open the donation dialog."""
		dlg = DonationDialog(self)
		dlg.ShowModal()
		dlg.Destroy()


def onInstall():
	"""Hook executed by NVDA when the addon is installed."""

	def show_welcome():
		app = wx.GetApp()
		if app and hasattr(gui, "mainFrame"):
			dlg = WelcomeDialog(gui.mainFrame)
			dlg.ShowModal()
			dlg.Destroy()

	# NVDA executes onInstall in a background thread during addon installation.
	# We must use wx.CallAfter to safely spawn GUI elements on the main thread.
	wx.CallAfter(show_welcome)
