# gui.py
#
# The news list dialog, the article reader dialog and the settings panel.
# Everything here runs on the main thread.

import re
import threading

import gui
import logHandler
import ui
import wx
from gui import guiHelper, nvdaControls
from gui.message import MessageDialog, ReturnCode
from gui.settingsDialogs import SettingsPanel

from . import cache, config, formatting
from .models import NewsItem
from .providers.sourceManager import CATEGORIES, SOURCE_NAMES

ALL = "Semua"
REFRESH_INTERVALS = (2, 5, 10, 15, 30, 60, 120)
DISPLAY_COUNTS = (20, 50, 100)
NOTIFICATION_MODES = (("digest", "Ringkasan jumlah berita baru"), ("immediate", "Judul setiap berita baru"))
_TIME = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")

# The open news list dialog, so background checks and settings can refresh it.
active_dialog = None


def refresh_active_dialog():
	"""Reload the open news list, keeping the selected story selected."""
	if active_dialog:
		wx.CallAfter(active_dialog.reload_settings)


def open_news_dialog():
	"""Open the news list, or bring it to the front if it is open."""
	global active_dialog
	import globalVars

	if globalVars.appArgs.secure:
		return
	if active_dialog:
		active_dialog.Raise()
		active_dialog.news_listbox.SetFocus()
		return
	try:
		active_dialog = NusaNewsDialog(gui.mainFrame)
		# prePopup and postPopup let NVDA bring its own window to the front.
		gui.mainFrame.prePopup()
		active_dialog.Show()
		gui.mainFrame.postPopup()
	except Exception:
		logHandler.log.exception("NusaNews: Opening the news list failed.")


def _copy_to_clipboard(text: str, done_message: str) -> None:
	if not wx.TheClipboard.Open():
		ui.message("Papan klip sedang dipakai program lain. Coba lagi.")
		return
	try:
		wx.TheClipboard.SetData(wx.TextDataObject(text))
		ui.message(done_message)
	except Exception:
		logHandler.log.exception("NusaNews: Copying failed.")
		ui.message("Gagal menyalin.")
	finally:
		wx.TheClipboard.Close()


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
		label = wx.StaticText(self, label="Informasi donasi:")
		sizer.Add(label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
		text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(400, 150))
		text.SetValue(msg)
		sizer.Add(text, 1, wx.EXPAND | wx.ALL, 10)
		btn = wx.Button(self, wx.ID_OK, label="&Tutup")
		sizer.Add(btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
		self.SetSizerAndFit(sizer)
		self.Centre()
		text.SetFocus()


class NusaNewsDialog(wx.Dialog):
	"""The list of cached stories, with filters and actions."""

	def __init__(self, parent):
		super().__init__(
			parent,
			title="NusaNews - Pembaca Berita Indonesia",
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
		)
		self.news_items: list[NewsItem] = []
		self.sources = [ALL] + config.read_settings()["enabled_sources"]
		self.categories = [ALL, *CATEGORIES]
		self.current_display_limit = config.get_config_val("max_display_count")
		self._setup_ui()
		self._bind_events()
		self.Centre()
		self.populate_list()
		self.news_listbox.SetFocus()

	def _setup_ui(self):
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)

		filters = guiHelper.BoxSizerHelper(self, orientation=wx.HORIZONTAL)
		self.source_choice = filters.addLabeledControl("&Sumber:", wx.Choice, choices=self.sources)
		self.source_choice.SetSelection(0)
		self.cat_choice = filters.addLabeledControl("&Kategori:", wx.Choice, choices=self.categories)
		self.cat_choice.SetSelection(0)
		sHelper.addItem(filters)

		self.unread_checkbox = sHelper.addItem(wx.CheckBox(self, label="Hanya yang &belum dibaca"))

		# The label makes NVDA say "Daftar berita, list" when the list gets focus.
		self.news_listbox = sHelper.addLabeledControl(
			"Daftar berita. Tekan Enter untuk membaca:",
			wx.ListBox,
			style=wx.LB_SINGLE | wx.LB_NEEDED_SB,
			size=(700, 360),
		)

		buttons = guiHelper.ButtonHelper(wx.HORIZONTAL)
		self.btn_copy_link = buttons.addButton(self, label="Salin &link")
		self.btn_mark_read = buttons.addButton(self, label="Tandai &dibaca")
		self.btn_mark_all = buttons.addButton(self, label="Tandai se&mua dibaca")
		self.btn_refresh = buttons.addButton(self, label="Se&garkan")
		self.btn_donate = buttons.addButton(self, label="D&onasi")
		self.btn_close = buttons.addButton(self, id=wx.ID_CANCEL, label="&Tutup")
		sHelper.addDialogDismissButtons(buttons)

		main_sizer.Add(sHelper.sizer, 1, wx.EXPAND | wx.ALL, guiHelper.BORDER_FOR_DIALOGS)
		self.SetSizerAndFit(main_sizer)
		self.SetEscapeId(wx.ID_CANCEL)

	def _bind_events(self):
		self.source_choice.Bind(wx.EVT_CHOICE, self.on_filter_changed)
		self.cat_choice.Bind(wx.EVT_CHOICE, self.on_filter_changed)
		self.unread_checkbox.Bind(wx.EVT_CHECKBOX, self.on_filter_changed)
		self.news_listbox.Bind(wx.EVT_LISTBOX_DCLICK, self.on_open)
		self.news_listbox.Bind(wx.EVT_LISTBOX, self.on_listbox_select)
		self.Bind(wx.EVT_CHAR_HOOK, self.on_dialog_char_hook)
		self.btn_copy_link.Bind(wx.EVT_BUTTON, self.on_copy_link)
		self.btn_mark_read.Bind(wx.EVT_BUTTON, self.on_mark_read)
		self.btn_mark_all.Bind(wx.EVT_BUTTON, self.on_mark_all_read)
		self.btn_refresh.Bind(wx.EVT_BUTTON, self.on_refresh)
		self.btn_close.Bind(wx.EVT_BUTTON, self.on_close)
		self.btn_donate.Bind(wx.EVT_BUTTON, self.on_donate)
		self.Bind(wx.EVT_CLOSE, self.on_close)

	def on_donate(self, event):
		dlg = DonationDialog(self)
		dlg.ShowModal()
		dlg.Destroy()

	def _selected_item(self) -> NewsItem | None:
		selection = self.news_listbox.GetSelection()
		if selection == wx.NOT_FOUND or selection >= len(self.news_items):
			return None
		return self.news_items[selection]

	def populate_list(self, keep_guid: str | None = None):
		"""Fill the list from the cache. keep_guid selects that story again if it is still listed."""
		selected_source = self.source_choice.GetString(self.source_choice.GetSelection())
		selected_cat = self.cat_choice.GetString(self.cat_choice.GetSelection())
		sources_filter = self.sources[1:] if selected_source == ALL else [selected_source]
		cats_filter = list(CATEGORIES) if selected_cat == ALL else [selected_cat]
		all_items = cache.get_news_items(
			enabled_sources=sources_filter,
			enabled_categories=cats_filter,
			filter_unread_only=self.unread_checkbox.GetValue(),
		)
		total_count = len(all_items)
		self.news_items = all_items[: self.current_display_limit]
		now = formatting.local_now()
		lines = [formatting.list_item_text(item, now) for item in self.news_items]
		if total_count > self.current_display_limit:
			remaining = total_count - self.current_display_limit
			lines.append(
				formatting.load_more_text(min(config.get_config_val("max_display_count"), remaining))
			)
		self.news_listbox.Set(lines)
		index = 0
		if keep_guid is not None:
			index = next((i for i, item in enumerate(self.news_items) if item.guid == keep_guid), 0)
		if lines:
			self.news_listbox.SetSelection(index)
		self.update_button_states()

	def update_item(self, guid: str) -> None:
		"""Read one story again from the cache and change its line in place, without rebuilding the list.

		Rebuilding the list while it has focus makes NVDA read the selected line twice.
		"""
		if self.unread_checkbox.GetValue():
			# The story may have to leave the list.
			self.populate_list(keep_guid=guid)
			return
		for index, item in enumerate(self.news_items):
			if item.guid != guid:
				continue
			updated = cache.get_news_items([item.source], [item.category])
			for fresh in updated:
				if fresh.guid == guid:
					self.news_items[index] = fresh
					self.news_listbox.SetString(index, formatting.list_item_text(fresh))
					break
			return

	def update_button_states(self):
		has_story = self._selected_item() is not None
		self.btn_mark_read.Enable(has_story)
		self.btn_copy_link.Enable(has_story)

	def on_listbox_select(self, event):
		self.update_button_states()

	def on_filter_changed(self, event):
		self.populate_list()

	def on_dialog_char_hook(self, event):
		"""Enter on the list opens the story."""
		if (
			event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER)
			and self.FindFocus() == self.news_listbox
		):
			self.on_open(None)
			return
		event.Skip()

	def on_open(self, event):
		"""Open the selected story in the reader, or load more stories."""
		selection = self.news_listbox.GetSelection()
		if selection == wx.NOT_FOUND:
			return
		if selection == len(self.news_items):
			self.on_load_more()
			return
		item = self._selected_item()
		if item is None:
			return
		try:
			NusaNewsReaderDialog(self, item).Show()
		except Exception:
			logHandler.log.exception("NusaNews: Opening the article reader failed.")
			ui.message("Gagal membuka berita.")

	def on_load_more(self):
		"""Show more stories and move to the first of them."""
		first_new = len(self.news_items)
		self.current_display_limit += config.get_config_val("max_display_count")
		self.populate_list()
		if first_new < len(self.news_items):
			self.news_listbox.SetSelection(first_new)
			self.update_button_states()

	def on_copy_link(self, event):
		item = self._selected_item()
		if item is not None:
			_copy_to_clipboard(item.url, "Link berita disalin.")

	def on_mark_read(self, event):
		item = self._selected_item()
		if item is None:
			return
		cache.mark_as_read(item.guid)
		self.update_item(item.guid)
		ui.message("Ditandai dibaca.")

	def on_mark_all_read(self, event):
		item = self._selected_item()
		cache.mark_all_as_read()
		self.populate_list(keep_guid=item.guid if item else None)
		ui.message("Semua berita ditandai dibaca.")

	def on_refresh(self, event):
		from . import addon_instance

		if addon_instance and addon_instance.request_refresh():
			ui.message("Memeriksa berita baru...")
		else:
			ui.message("Gagal menyegarkan. Add-on tidak aktif.")

	def on_close(self, event):
		global active_dialog
		active_dialog = None
		self.Destroy()

	def reload_settings(self):
		"""Apply changed sources and new stories, keeping the filters and the selected story."""
		item = self._selected_item()
		current_source = self.source_choice.GetString(self.source_choice.GetSelection())
		self.sources = [ALL] + config.read_settings()["enabled_sources"]
		self.current_display_limit = max(
			self.current_display_limit, config.get_config_val("max_display_count")
		)
		self.source_choice.Set(self.sources)
		index = self.source_choice.FindString(current_source)
		self.source_choice.SetSelection(index if index != wx.NOT_FOUND else 0)
		self.populate_list(keep_guid=item.guid if item else None)


class NusaNewsReaderDialog(wx.Dialog):
	"""Reads one story: its details and the article text, downloaded when needed."""

	def __init__(self, parent: NusaNewsDialog, item: NewsItem):
		super().__init__(parent, title=item.title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self.item = item
		self.list_dialog = parent
		self.body = ""

		main_sizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		self.text_ctrl = sHelper.addLabeledControl(
			"Isi berita:",
			wx.TextCtrl,
			style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
			size=(700, 450),
		)
		buttons = guiHelper.ButtonHelper(wx.HORIZONTAL)
		self.btn_browser = buttons.addButton(self, label="Buka di &browser")
		self.btn_copy_link = buttons.addButton(self, label="Salin &link")
		self.btn_copy = buttons.addButton(self, label="&Salin berita")
		self.btn_close = buttons.addButton(self, id=wx.ID_CANCEL, label="&Tutup")
		sHelper.addDialogDismissButtons(buttons)
		main_sizer.Add(sHelper.sizer, 1, wx.EXPAND | wx.ALL, guiHelper.BORDER_FOR_DIALOGS)
		self.SetSizerAndFit(main_sizer)
		self.SetEscapeId(wx.ID_CANCEL)
		self.Centre()

		self.btn_browser.Bind(wx.EVT_BUTTON, self.on_open_browser)
		self.btn_copy_link.Bind(wx.EVT_BUTTON, self.on_copy_link)
		self.btn_copy.Bind(wx.EVT_BUTTON, self.on_copy)
		self.btn_close.Bind(wx.EVT_BUTTON, self.on_close)
		self.Bind(wx.EVT_CLOSE, self.on_close)

		# Opening a story marks it read.
		cache.mark_as_read(item.guid)
		self.load_article()
		self.text_ctrl.SetFocus()

	def load_article(self):
		"""Show the saved article, or download it in a background thread."""
		content = cache.get_article_content(self.item.guid)
		if content:
			self._show(content)
			return
		self._show("Sedang mengunduh isi berita...", body_loaded=False)
		# Settings are read here on the main thread, not in the download thread.
		bypass_ssl = config.get_config_val("bypass_ssl_verification")
		threading.Thread(
			target=self._bg_fetch, args=(self.item.guid, self.item.url, bypass_ssl), daemon=True
		).start()

	def _show(self, body: str, body_loaded: bool = True) -> None:
		self.body = body if body_loaded else ""
		self.text_ctrl.SetValue(formatting.article_text(self.item, body))
		self.text_ctrl.SetInsertionPoint(0)

	def _bg_fetch(self, guid, url, bypass_ssl):
		"""Runs in a background thread."""
		from .providers.articleContent import fetch_article_content

		content = fetch_article_content(url, bypass_ssl=bypass_ssl)
		wx.CallAfter(self._on_fetch_complete, guid, content)

	def _on_fetch_complete(self, guid, content):
		if not self:
			# The reader was closed while downloading.
			if content:
				cache.update_article_content(guid, content)
			return
		if content:
			cache.update_article_content(guid, content)
			self._show(content)
			ui.message("Berita berhasil dimuat.")
		else:
			self._show(
				"Gagal memuat isi berita secara offline.\n\n"
				"Periksa koneksi internet Anda, atau tekan Buka di browser (Alt+B) "
				"untuk membacanya langsung di situs web.",
				body_loaded=False,
			)
			ui.message("Gagal mengunduh isi berita.")

	def on_open_browser(self, event):
		try:
			import os

			os.startfile(self.item.url)
		except Exception:
			logHandler.log.exception(f"NusaNews: Opening {self.item.url} failed.")
			ui.message("Gagal membuka browser.")

	def on_copy_link(self, event):
		_copy_to_clipboard(self.item.url, "Link berita disalin.")

	def on_copy(self, event):
		_copy_to_clipboard(formatting.article_copy_text(self.item, self.body), "Berita disalin.")

	def on_close(self, event):
		# Update the story's line before focus goes back to the list, so NVDA reads it once, as read.
		if self.list_dialog:
			self.list_dialog.update_item(self.item.guid)
		self.Destroy()


class NusaNewsSettingsPanel(SettingsPanel):
	"""The add-on's category in NVDA's settings."""

	title = "NusaNewsID"

	def makeSettings(self, settingsSizer):
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		settings = config.read_settings()

		self.sources_list = list(SOURCE_NAMES)
		self.sources_checklist = sHelper.addLabeledControl(
			"&Sumber berita yang dipantau:", nvdaControls.CustomCheckListBox, choices=self.sources_list
		)
		self.sources_checklist.SetCheckedStrings(settings["enabled_sources"])
		self.sources_checklist.SetSelection(0)

		self.interval_choice = sHelper.addLabeledControl(
			"&Periksa berita baru setiap (menit):", wx.Choice, choices=[str(m) for m in REFRESH_INTERVALS]
		)
		self.interval_choice.SetSelection(_nearest_index(REFRESH_INTERVALS, settings["refresh_interval"]))

		notifications = self._group(sHelper, "Notifikasi")
		self.notify_choice = notifications.addLabeledControl(
			"&Cara memberi tahu berita baru:", wx.Choice, choices=[label for _, label in NOTIFICATION_MODES]
		)
		modes = [mode for mode, _ in NOTIFICATION_MODES]
		self.notify_choice.SetSelection(
			modes.index(settings["notification_mode"]) if settings["notification_mode"] in modes else 0
		)
		self.beep_checkbox = notifications.addItem(
			wx.CheckBox(self._box(notifications), label="Bunyikan &nada saat ada berita baru")
		)
		self.beep_checkbox.SetValue(settings["notification_tone"])
		self.breaking_checkbox = notifications.addItem(
			wx.CheckBox(self._box(notifications), label="Umumkan berita &breaking juga saat jam sunyi")
		)
		self.breaking_checkbox.SetValue(settings["breaking_news_preference"])

		quiet = self._group(sHelper, "Jam sunyi")
		self.dnd_checkbox = quiet.addItem(wx.CheckBox(self._box(quiet), label="Ak&tifkan jam sunyi"))
		self.dnd_checkbox.SetValue(settings["silent_hours_enabled"])
		self.dnd_checkbox.Bind(wx.EVT_CHECKBOX, self._on_dnd_toggled)
		self.dnd_start_txt = quiet.addLabeledControl("&Mulai (jam:menit, misalnya 22:00):", wx.TextCtrl)
		self.dnd_start_txt.SetValue(settings["silent_hours_start"])
		self.dnd_end_txt = quiet.addLabeledControl("S&elesai (jam:menit, misalnya 06:00):", wx.TextCtrl)
		self.dnd_end_txt.SetValue(settings["silent_hours_end"])
		self._on_dnd_toggled(None)

		self.display_limit_choice = sHelper.addLabeledControl(
			"&Jumlah berita yang ditampilkan sekaligus:", wx.Choice, choices=[str(n) for n in DISPLAY_COUNTS]
		)
		self.display_limit_choice.SetSelection(_nearest_index(DISPLAY_COUNTS, settings["max_display_count"]))

		storage = self._group(sHelper, "Penyimpanan")
		self.cache_spin = storage.addLabeledControl(
			"&Lama penyimpanan berita (hari):",
			nvdaControls.SelectOnFocusSpinCtrl,
			min=1,
			max=30,
			initial=settings["cache_duration"],
		)
		self.btn_clear_cache = storage.addItem(
			wx.Button(self._box(storage), label="&Hapus semua berita tersimpan")
		)
		self.btn_clear_cache.Bind(wx.EVT_BUTTON, self.on_clear_cache)

		self.ssl_checkbox = sHelper.addItem(
			wx.CheckBox(
				self,
				label="Lewati pemeriksaan sertifikat &keamanan (hanya jika koneksi selalu gagal; tidak aman)",
			)
		)
		self.ssl_checkbox.SetValue(settings["bypass_ssl_verification"])

		self.btn_donate = sHelper.addItem(wx.Button(self, label="D&ukungan dan donasi"))
		self.btn_donate.Bind(wx.EVT_BUTTON, self.on_donate)

	def _group(self, sHelper: guiHelper.BoxSizerHelper, label: str) -> guiHelper.BoxSizerHelper:
		"""A labelled group, which NVDA announces when focus enters it."""
		sizer = wx.StaticBoxSizer(wx.VERTICAL, self, label=label)
		# The group's controls are children of its box, as wxPython expects for a StaticBoxSizer.
		group = guiHelper.BoxSizerHelper(sizer.GetStaticBox(), sizer=sizer)
		sHelper.addItem(group)
		return group

	@staticmethod
	def _box(group: guiHelper.BoxSizerHelper) -> wx.StaticBox:
		return group.sizer.GetStaticBox()

	def _on_dnd_toggled(self, event):
		enabled = self.dnd_checkbox.GetValue()
		self.dnd_start_txt.Enable(enabled)
		self.dnd_end_txt.Enable(enabled)

	def on_donate(self, event):
		dlg = DonationDialog(self)
		dlg.ShowModal()
		dlg.Destroy()

	def isValid(self) -> bool:
		"""Refuse to save quiet hours that are not times, and say which field is wrong."""
		if self.dnd_checkbox.GetValue():
			for field, name in ((self.dnd_start_txt, "mulai"), (self.dnd_end_txt, "selesai")):
				if not _TIME.match(field.GetValue().strip()):
					MessageDialog.alert(
						f"Jam {name} jam sunyi harus berupa jam dan menit, misalnya 22:00.",
						"Jam sunyi tidak valid",
						self,
					)
					field.SetFocus()
					return False
		if not self.sources_checklist.GetCheckedItems():
			MessageDialog.alert("Pilih setidaknya satu sumber berita.", "Tidak ada sumber berita", self)
			self.sources_checklist.SetFocus()
			return False
		return super().isValid()

	def onSave(self):
		config.set_config_val("enabled_sources", list(self.sources_checklist.GetCheckedStrings()))
		config.set_config_val("refresh_interval", REFRESH_INTERVALS[self.interval_choice.GetSelection()])
		config.set_config_val("notification_mode", NOTIFICATION_MODES[self.notify_choice.GetSelection()][0])
		config.set_config_val("notification_tone", self.beep_checkbox.GetValue())
		config.set_config_val("breaking_news_preference", self.breaking_checkbox.GetValue())
		config.set_config_val("silent_hours_enabled", self.dnd_checkbox.GetValue())
		config.set_config_val("silent_hours_start", _normal_time(self.dnd_start_txt.GetValue()))
		config.set_config_val("silent_hours_end", _normal_time(self.dnd_end_txt.GetValue()))
		config.set_config_val("bypass_ssl_verification", self.ssl_checkbox.GetValue())
		config.set_config_val("cache_duration", self.cache_spin.GetValue())
		config.set_config_val("max_display_count", DISPLAY_COUNTS[self.display_limit_choice.GetSelection()])

		# Hand the new settings to the background thread. NVDA writes nvda.ini itself.
		from . import addon_instance

		if addon_instance:
			addon_instance.apply_settings()
		refresh_active_dialog()

	def on_clear_cache(self, event):
		result = MessageDialog.confirm(
			"Hapus semua berita dan artikel yang tersimpan? Tindakan ini tidak bisa dibatalkan.",
			"Hapus berita tersimpan",
			self,
			okLabel="&Hapus",
			cancelLabel="&Batal",
		)
		if result != ReturnCode.OK:
			return
		try:
			cache.clear_cache()
			ui.message("Semua berita tersimpan sudah dihapus.")
			refresh_active_dialog()
		except Exception:
			logHandler.log.exception("NusaNews: Clearing the cache failed.")
			ui.message("Gagal menghapus berita tersimpan.")


def _nearest_index(values: tuple[int, ...], value: int) -> int:
	"""The index of the choice closest to a saved value, for values saved before a choice existed."""
	return min(range(len(values)), key=lambda index: abs(values[index] - value))


def _normal_time(text: str) -> str:
	"""Write a time as HH:MM, so "6:00" is saved as "06:00"."""
	match = _TIME.match(text.strip())
	if not match:
		return text.strip()
	return f"{int(match.group(1)):02d}:{match.group(2)}"
