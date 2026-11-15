# -*- coding: utf-8 -*-
# gui.py
#
# Documentation Compliance Notes:
# - Inherits from gui.SettingsPanel to register configuration UI elements in NVDA's settings dialog.
# - Dialog widgets utilize explicit labels and accessible descriptions, ensuring native accessibility.
# Threading Notes:
# - All GUI rendering and interactions execute synchronously on NVDA's main thread.
# - External triggers (background thread poll updates) refresh the dialog via wx.CallAfter callbacks.
# Lifecycle Notes:
# - NusaNewsDialog is instantiated modally on script trigger and destroyed on Close/Escape.
# - NusaNewsSettingsPanel appends/removes its class during addon initialization/termination.
# Design Explanation:
# - Implements a list-based Pembaca Berita dialog with filtering by source/category, browser-opening hooks,
#   and a settings panel mapping options to config.conf.

import os
import threading
import wx
import gui
from gui.settingsDialogs import SettingsPanel
import logHandler
import ui
from typing import List, Optional

from . import config
from . import cache
from .models import NewsItem

# Pointer to active dialog to allow background refreshes
active_dialog = None

def refresh_active_dialog():
	"""Refreshes the active dialog news list and filters if open."""
	global active_dialog
	if active_dialog:
		wx.CallAfter(active_dialog.reload_settings)

def open_news_dialog():
	"""Safely initializes and displays the news reader dialog on the main thread."""
	global active_dialog
	import globalVars
	if globalVars.appArgs.secure:
		return
	if active_dialog:
		# Bring existing dialog to front
		active_dialog.Raise()
		return
	
	try:
		# Instantiates and displays dialog modelessly
		active_dialog = NusaNewsDialog(None)
		active_dialog.Show()
	except Exception as e:
		logHandler.log.error(f"NusaNews: Failed to display news dialog: {e}")


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
		
		text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(400, 150))
		text.SetValue(msg)
		text.SetBackgroundColour(self.GetBackgroundColour())
		
		sizer.Add(text, 1, wx.EXPAND | wx.ALL, 10)
		
		btn = wx.Button(self, wx.ID_OK, label="&Tutup")
		sizer.Add(btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
		
		self.SetSizerAndFit(sizer)
		self.Centre()

class NusaNewsDialog(wx.Dialog):
	"""Accessible dialog displaying Indonesian news updates."""
	
	def __init__(self, parent):
		# Set localized title and dialog attributes
		super().__init__(
			parent, 
			title="NusaNews - Pembaca Berita Indonesia", 
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
		)
		
		# Track state data
		self.news_items: List[NewsItem] = []
		self.sources = ["Semua"] + config.get_config_val("enabled_sources")
		self.current_display_limit = config.get_config_val("max_display_count")
		
		# Canonical category filters
		self.categories = [
			"Semua", "Nasional", "Internasional", "Teknologi", 
			"Politik", "Ekonomi", "Olahraga", "Entertainment", "Disabilitas"
		]

		self._setup_ui()
		self._bind_events()
		self.Centre()
		
		# Initial populate load
		self.populate_list()
		self.news_listbox.SetFocus()

	def _setup_ui(self):
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		
		# Instructions label
		instruction_lbl = wx.StaticText(
			self, 
			label="Daftar Berita. Gunakan panah atas/bawah untuk memilih, tekan Enter untuk membuka."
		)
		main_sizer.Add(instruction_lbl, 0, wx.ALL, 10)
		
		# Filters panel (Source & Category choices)
		filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		# Source filter dropdown
		filter_sizer.Add(wx.StaticText(self, label="Filter Sumber:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		self.source_choice = wx.Choice(self, choices=self.sources)
		self.source_choice.SetSelection(0)
		filter_sizer.Add(self.source_choice, 1, wx.EXPAND | wx.RIGHT, 15)
		
		# Category filter dropdown
		filter_sizer.Add(wx.StaticText(self, label="Filter Kategori:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		self.cat_choice = wx.Choice(self, choices=self.categories)
		self.cat_choice.SetSelection(0)
		filter_sizer.Add(self.cat_choice, 1, wx.EXPAND)
		
		main_sizer.Add(filter_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
		
		# Unread only checkbox filter
		self.unread_checkbox = wx.CheckBox(self, label="Tampilkan Berita Belum Dibaca Saja")
		self.unread_checkbox.SetValue(False)
		main_sizer.Add(self.unread_checkbox, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
		
		# News List Box
		self.news_listbox = wx.ListBox(self, style=wx.LB_SINGLE | wx.LB_NEEDED_SB)
		main_sizer.Add(self.news_listbox, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
		
		# Button controls
		btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		# Salin Link Button (Alt+C)
		self.btn_copy_link = wx.Button(self, label="Salin &Link")
		btn_sizer.Add(self.btn_copy_link, 0, wx.RIGHT, 5)
		
		# Tandai Dibaca Button (Alt+D)
		self.btn_mark_read = wx.Button(self, label="Tandai &Dibaca")
		btn_sizer.Add(self.btn_mark_read, 0, wx.RIGHT, 5)

		# Tandai Semua Dibaca Button (Alt+M)
		self.btn_mark_all = wx.Button(self, label="Tandai Se&mua dibaca")
		btn_sizer.Add(self.btn_mark_all, 0, wx.RIGHT, 5)

		# Segarkan Button (Alt+S)
		self.btn_refresh = wx.Button(self, label="&Segarkan")
		btn_sizer.Add(self.btn_refresh, 0, wx.RIGHT, 5)
		
		# Tutup Button (Escape / Alt+T)
		self.btn_close = wx.Button(self, id=wx.ID_CANCEL, label="&Tutup")
		btn_sizer.Add(self.btn_close, 0, wx.RIGHT, 5)

		# Donasi Button
		self.btn_donate = wx.Button(self, label="D&onasi")
		btn_sizer.Add(self.btn_donate, 0)
		
		main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
		
		self.SetSizer(main_sizer)
		self.SetMinSize((600, 450))
		self.Layout()

	def _bind_events(self):
		self.source_choice.Bind(wx.EVT_CHOICE, self.on_filter_changed)
		self.cat_choice.Bind(wx.EVT_CHOICE, self.on_filter_changed)
		self.unread_checkbox.Bind(wx.EVT_CHECKBOX, self.on_filter_changed)
		self.news_listbox.Bind(wx.EVT_LISTBOX_DCLICK, self.on_open)
		# Update button states dynamically when selection changes
		self.news_listbox.Bind(wx.EVT_LISTBOX, self.on_listbox_select)
		# Handle direct Enter key presses on ListBox items at the dialog level
		self.Bind(wx.EVT_CHAR_HOOK, self.on_dialog_char_hook)
		
		self.btn_copy_link.Bind(wx.EVT_BUTTON, self.on_copy_link)
		self.btn_mark_read.Bind(wx.EVT_BUTTON, self.on_mark_read)
		self.btn_mark_all.Bind(wx.EVT_BUTTON, self.on_mark_all_read)
		self.btn_refresh.Bind(wx.EVT_BUTTON, self.on_refresh)
		self.btn_close.Bind(wx.EVT_BUTTON, self.on_close)
		self.btn_donate.Bind(wx.EVT_BUTTON, self.on_donate)
		self.Bind(wx.EVT_CLOSE, self.on_close)

	def on_donate(self, event):
		"""Show donation dialog."""
		dlg = DonationDialog(self)
		dlg.ShowModal()
		dlg.Destroy()

	def populate_list(self, set_default_selection=True):
		"""Queries cached items matching criteria and reloads ListBox contents."""
		# Retrieve filters
		selected_source = self.source_choice.GetString(self.source_choice.GetSelection())
		selected_cat = self.cat_choice.GetString(self.cat_choice.GetSelection())
		unread_only = self.unread_checkbox.GetValue()
		
		# Map sources query
		if selected_source == "Semua":
			sources_filter = config.get_config_val("enabled_sources")
		else:
			sources_filter = [selected_source]
			
		# Map categories query
		if selected_cat == "Semua":
			cats_filter = [c for c in self.categories if c != "Semua"]
		else:
			cats_filter = [selected_cat]
			
		# Fetch from cache database (occurs strictly on main thread)
		all_items = cache.get_news_items(
			enabled_sources=sources_filter,
			enabled_categories=cats_filter,
			filter_unread_only=unread_only
		)
		
		# Limit display count based on self.current_display_limit
		total_count = len(all_items)
		self.news_items = all_items[:self.current_display_limit]
		
		# Rebuild ListBox string items
		self.news_listbox.Clear()
		for item in self.news_items:
			seen_status = "[Baru] " if not item.seen else ""
			breaking_status = "[BREAKING] " if item.is_breaking else ""
			display_text = f"{seen_status}{breaking_status}[{item.source}] {item.title}"
			self.news_listbox.Append(display_text)
			
		# Append load more option if there are more items available
		if total_count > self.current_display_limit:
			self.news_listbox.Append("-- Muat Lebih Banyak --")
			
		# Select first item if list is not empty and set_default_selection is True
		if self.news_items and set_default_selection:
			self.news_listbox.SetSelection(0)
			
		self.update_button_states()

	def update_button_states(self):
		"""Enables/disables action buttons based on active selection and list items."""
		selection = self.news_listbox.GetSelection()
		if selection == wx.NOT_FOUND:
			self.btn_mark_read.Enable(False)
			self.btn_copy_link.Enable(False)
		elif selection == len(self.news_items):
			# Selected the "-- Muat Lebih Banyak --" option
			self.btn_mark_read.Enable(False)
			self.btn_copy_link.Enable(False)
		else:
			self.btn_mark_read.Enable(True)
			self.btn_copy_link.Enable(True)

	def on_listbox_select(self, event):
		"""Fires when user selection in list changes."""
		self.update_button_states()

	def on_filter_changed(self, event):
		self.populate_list()

	def on_dialog_char_hook(self, event):
		"""Intercepts Enter key presses at dialog level to open articles when listbox is focused."""
		key_code = event.GetKeyCode()
		if key_code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
			if self.FindFocus() == self.news_listbox:
				self.on_open(None)
				return
		event.Skip()

	def on_open(self, event):
		"""Opens the selected article in the offline reader dialog or triggers loading more."""
		selection = self.news_listbox.GetSelection()
		if selection == wx.NOT_FOUND:
			return
			
		# Check if they selected "-- Muat Lebih Banyak --"
		if selection == len(self.news_items):
			self.on_load_more()
			return
			
		if selection > len(self.news_items):
			return
			
		item = self.news_items[selection]
		
		try:
			# Open the offline reader dialog modelessly
			reader_dlg = NusaNewsReaderDialog(self, item)
			reader_dlg.Show()
		except Exception as e:
			logHandler.log.error(f"NusaNews: Failed to open offline reader: {e}")
			ui.message("Gagal membuka pembaca berita offline.")

	def on_load_more(self):
		"""Increases the current display limit and populates the listbox, focusing on the first new item."""
		old_count = len(self.news_items)
		increment = config.get_config_val("max_display_count")
		self.current_display_limit += increment
		
		self.populate_list(set_default_selection=False)
		
		# Focus and select the first newly loaded item
		new_count = self.news_listbox.GetCount()
		if old_count < new_count:
			self.news_listbox.SetSelection(old_count)
			self.news_listbox.SetFocus()
			self.update_button_states()



	def on_copy_link(self, event):
		"""Copies the selected article URL to clipboard."""
		selection = self.news_listbox.GetSelection()
		if selection == wx.NOT_FOUND or selection >= len(self.news_items):
			return
		item = self.news_items[selection]
		import ui
		if wx.TheClipboard.Open():
			try:
				wx.TheClipboard.SetData(wx.TextDataObject(item.url))
				ui.message("Link berita disalin.")
			except Exception as e:
				logHandler.log.error(f"NusaNews: Failed to copy link: {e}")
				ui.message("Gagal menyalin link.")
			finally:
				wx.TheClipboard.Close()
		else:
			ui.message("Clipboard sibuk.")

	def on_mark_read(self, event):
		"""Marks selected item as read in Cache."""
		selection = self.news_listbox.GetSelection()
		if selection == wx.NOT_FOUND or selection >= len(self.news_items):
			return
			
		item = self.news_items[selection]
		cache.mark_as_read(item.guid)
		self.populate_list(set_default_selection=False)
		# Restore selection
		if selection < self.news_listbox.GetCount():
			self.news_listbox.SetSelection(selection)

	def on_mark_all_read(self, event):
		"""Marks all cached articles as read."""
		cache.mark_all_as_read()
		self.populate_list(set_default_selection=False)
		ui.message("Semua berita ditandai dibaca.")

	def on_refresh(self, event):
		"""Triggers manual background monitors check immediately."""
		from . import addon_instance
		if addon_instance and addon_instance.request_refresh():
			ui.message("Memeriksa berita baru...")
		else:
			ui.message("Gagal menyegarkan. Addon tidak aktif.")

	def on_close(self, event):
		"""Handles dialog cleanup on exit."""
		global active_dialog
		active_dialog = None
		self.Destroy()

	def reload_settings(self):
		"""Updates choices and filters in the open dialog when configurations are updated."""
		self.sources = ["Semua"] + config.get_config_val("enabled_sources")
		new_limit = config.get_config_val("max_display_count")
		if not hasattr(self, 'current_display_limit') or self.current_display_limit < new_limit:
			self.current_display_limit = new_limit
		
		# Save current selection if possible
		current_source = self.source_choice.GetString(self.source_choice.GetSelection())
		
		# Rebuild source choice items
		self.source_choice.Clear()
		for src in self.sources:
			self.source_choice.Append(src)
			
		# Restore selection or select 'Semua'
		sel_idx = self.source_choice.FindString(current_source)
		if sel_idx != wx.NOT_FOUND:
			self.source_choice.SetSelection(sel_idx)
		else:
			self.source_choice.SetSelection(0)
			
		old_listbox_sel = self.news_listbox.GetSelection()
		self.populate_list(set_default_selection=False)
		
		# Restore listbox selection if still valid
		if old_listbox_sel != wx.NOT_FOUND and old_listbox_sel < self.news_listbox.GetCount():
			self.news_listbox.SetSelection(old_listbox_sel)
			self.update_button_states()
		elif self.news_listbox.GetCount() > 0:
			self.news_listbox.SetSelection(0)
			self.update_button_states()

class NusaNewsReaderDialog(wx.Dialog):
	"""Accessible dialog to read news articles offline."""
	
	def __init__(self, parent, item: NewsItem):
		super().__init__(
			parent, 
			title=f"Membaca Berita - {item.source}", 
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
		)
		self.item = item
		
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		
		# Metadata text content
		self.text_ctrl = wx.TextCtrl(
			self, 
			style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2
		)
		
		# Set minimum size for usability
		self.SetMinSize((700, 500))
		main_sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 10)
		
		# Buttons
		btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		# Buka di Browser (Alt+B)
		self.btn_browser = wx.Button(self, label="Buka di &Browser")
		self.btn_browser.Bind(wx.EVT_BUTTON, self.on_open_browser)
		btn_sizer.Add(self.btn_browser, 0, wx.RIGHT, 5)
		
		# Salin Link (Alt+C)
		self.btn_copy_link = wx.Button(self, label="Salin &Link")
		self.btn_copy_link.Bind(wx.EVT_BUTTON, self.on_copy_link)
		btn_sizer.Add(self.btn_copy_link, 0, wx.RIGHT, 5)
		
		# Salin (Alt+S)
		self.btn_copy = wx.Button(self, label="&Salin berita")
		self.btn_copy.Bind(wx.EVT_BUTTON, self.on_copy)
		btn_sizer.Add(self.btn_copy, 0, wx.RIGHT, 5)
		
		# Tutup (Escape / Alt+T)
		self.btn_close = wx.Button(self, id=wx.ID_CANCEL, label="&Tutup")
		self.btn_close.Bind(wx.EVT_BUTTON, self.on_close)
		btn_sizer.Add(self.btn_close, 0)
		
		main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
		
		self.SetSizer(main_sizer)
		self.Layout()
		self.Centre()
		
		# Mark article as read in cache/list since the user opened it
		cache.mark_as_read(item.guid)
		
		# Populate initial text content
		self.load_article()
		
		# Put focus on the text control so screen reader reads it
		self.text_ctrl.SetFocus()

	def load_article(self):
		"""Loads the article body from cache or triggers background download."""
		title = self.item.title
		source = self.item.source
		cat = self.item.category
		date = self.item.published_at or "-"
		url = self.item.url
		
		# Format header metadata
		header = (
			f"Judul: {title}\n"
			f"Sumber: {source} | Kategori: {cat} | Tanggal: {date}\n"
			f"Link: {url}\n"
			f"{'-'*60}\n\n"
		)
		
		# Check if content is already cached
		if self.item.content:
			self.text_ctrl.SetValue(header + self.item.content)
			self.text_ctrl.SetInsertionPoint(0)
		else:
			self.text_ctrl.SetValue(header + "Sedang mengunduh isi berita...")
			
			# Start background fetch thread
			# Settings are read here on the main thread, not in the download thread.
			bypass_ssl = config.get_config_val("bypass_ssl_verification")
			threading.Thread(
				target=self._bg_fetch,
				args=(self.item.guid, url, bypass_ssl),
				daemon=True
			).start()

	def _bg_fetch(self, guid, url, bypass_ssl):
		"""Worker function running in a background thread."""
		from .providers.htmlProvider import fetch_article_content
		content = fetch_article_content(url, bypass_ssl=bypass_ssl)
		
		# Dispatch UI updates back to the main thread
		wx.CallAfter(self._on_fetch_complete, guid, content)

	def _on_fetch_complete(self, guid, content):
		"""Executed on the main thread via wx.CallAfter."""
		if not self:
			return
			
		title = self.item.title
		source = self.item.source
		cat = self.item.category
		date = self.item.published_at or "-"
		url = self.item.url
		
		header = (
			f"Judul: {title}\n"
			f"Sumber: {source} | Kategori: {cat} | Tanggal: {date}\n"
			f"Link: {url}\n"
			f"{'-'*60}\n\n"
		)
		
		if content:
			# Save to cache database
			cache.update_article_content(guid, content)
			# Update the text control value
			self.text_ctrl.SetValue(header + content)
			self.text_ctrl.SetInsertionPoint(0)
			ui.message("Berita berhasil dimuat.")
		else:
			self.text_ctrl.SetValue(
				header + 
				"Gagal memuat isi berita secara offline.\n\n"
				"Silakan periksa koneksi internet Anda atau gunakan tombol 'Buka di Browser' (Alt+B) untuk membaca langsung di situs web."
			)
			self.text_ctrl.SetInsertionPoint(0)
			ui.message("Gagal mengunduh isi berita.")

	def on_open_browser(self, event):
		try:
			import os
			os.startfile(self.item.url)
		except Exception as e:
			logHandler.log.error(f"NusaNews: Failed to open URL '{self.item.url}': {e}")
			ui.message("Gagal membuka browser.")

	def on_copy_link(self, event):
		"""Copies the article URL to clipboard."""
		import ui
		if wx.TheClipboard.Open():
			try:
				wx.TheClipboard.SetData(wx.TextDataObject(self.item.url))
				ui.message("Link berita disalin.")
			except Exception as e:
				logHandler.log.error(f"NusaNews: Failed to copy link: {e}")
				ui.message("Gagal menyalin link.")
			finally:
				wx.TheClipboard.Close()
		else:
			ui.message("Clipboard sibuk.")

	def on_copy(self, event):
		"""Copies the article content to clipboard."""
		if wx.TheClipboard.Open():
			try:
				wx.TheClipboard.SetData(wx.TextDataObject(self.text_ctrl.GetValue()))
				ui.message("Isi berita disalin ke clipboard.")
			except Exception as e:
				logHandler.log.error(f"NusaNews: Failed to copy to clipboard: {e}")
				ui.message("Gagal menyalin berita.")
			finally:
				wx.TheClipboard.Close()
		else:
			ui.message("Clipboard sibuk.")

	def on_close(self, event):
		# Trigger list refresh in the main dialog to show marked as read state
		from .gui import refresh_active_dialog
		refresh_active_dialog()
		self.Destroy()


class NusaNewsSettingsPanel(SettingsPanel):
	"""Settings Panel class integrated inside NVDA options list."""
	title = "nusaNewsID"

	def makeSettings(self, settingsSizer):
		# BoxSizerHelper makes accessible form formatting simple
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		
		self._create_sources_group(sHelper)
		self._create_sync_group(sHelper)
		self._create_notifications_group(sHelper)
		self._create_dnd_group(sHelper)
		self._create_display_group(sHelper)
		self._create_cache_group(sHelper)

	def _create_sources_group(self, sHelper):
		sHelper.addItem(wx.StaticText(self, label="Sumber Berita Aktif: Pilih sumber berita yang diaktifkan:"))
		
		from .providers.sourceManager import SOURCE_NAMES
		self.sources_list = list(SOURCE_NAMES)
		self.source_checkboxes = {}
		
		enabled_sources = config.get_config_val("enabled_sources")
		for src in self.sources_list:
			chk = sHelper.addItem(wx.CheckBox(self, label=src))
			chk.SetValue(src in enabled_sources)
			self.source_checkboxes[src] = chk

	def _create_sync_group(self, sHelper):
		sHelper.addItem(wx.StaticText(self, label="Interval Penyegaran (menit):"))
		sHelper.addItem(wx.StaticText(self, label="Pilih seberapa sering addon mencari berita baru:"))
		self.interval_choice = wx.Choice(self, choices=["2", "5", "10", "15", "30", "60", "120"])
		current_interval = str(config.get_config_val("refresh_interval"))
		selection = self.interval_choice.FindString(current_interval)
		if selection != wx.NOT_FOUND:
			self.interval_choice.SetSelection(selection)
		else:
			self.interval_choice.SetSelection(1)  # Default 5 mins
		sHelper.addItem(self.interval_choice)

	def _create_notifications_group(self, sHelper):
		sHelper.addItem(wx.StaticText(self, label="Mode Notifikasi: Pilih bagaimana berita baru diberitahukan:"))
		self.notify_choice = wx.Choice(self, choices=["Hanya Ringkasan (Digest)", "Berita Langsung (Immediate)"])
		current_mode = config.get_config_val("notification_mode")
		self.notify_choice.SetSelection(0 if current_mode == "digest" else 1)
		sHelper.addItem(self.notify_choice)

		self.beep_checkbox = sHelper.addItem(wx.CheckBox(self, label="Mainkan nada notifikasi ketika ada berita baru"))
		self.beep_checkbox.SetValue(config.get_config_val("notification_tone"))

		self.breaking_checkbox = sHelper.addItem(wx.CheckBox(self, label="Utamakan berita breaking news (selalu umumkan langsung)"))
		self.breaking_checkbox.SetValue(config.get_config_val("breaking_news_preference"))

	def _create_dnd_group(self, sHelper):
		self.dnd_checkbox = sHelper.addItem(wx.CheckBox(self, label="Aktifkan Jam Sunyi (Do Not Disturb)"))
		self.dnd_checkbox.SetValue(config.get_config_val("silent_hours_enabled"))
		
		sHelper.addItem(wx.StaticText(self, label="Jam Sunyi Mulai (HH:MM): (Misal 22:00)"))
		self.dnd_start_txt = sHelper.addItem(wx.TextCtrl(self))
		self.dnd_start_txt.SetValue(config.get_config_val("silent_hours_start"))
		
		sHelper.addItem(wx.StaticText(self, label="Jam Sunyi Selesai (HH:MM): (Misal 06:00)"))
		self.dnd_end_txt = sHelper.addItem(wx.TextCtrl(self))
		self.dnd_end_txt.SetValue(config.get_config_val("silent_hours_end"))

	def _create_display_group(self, sHelper):
		self.ssl_checkbox = sHelper.addItem(wx.CheckBox(self, label="Lewati Verifikasi SSL (Gunakan jika koneksi error)"))
		self.ssl_checkbox.SetValue(config.get_config_val("bypass_ssl_verification"))

		sHelper.addItem(wx.StaticText(self, label="Jumlah Berita Awal yang Ditampilkan: Pilih jumlah berita yang ditampilkan di daftar:"))
		self.display_limit_choice = wx.Choice(self, choices=["20", "50", "100"])
		current_limit = str(config.get_config_val("max_display_count"))
		selection = self.display_limit_choice.FindString(current_limit)
		if selection != wx.NOT_FOUND:
			self.display_limit_choice.SetSelection(selection)
		else:
			self.display_limit_choice.SetSelection(1) # Default 50
		sHelper.addItem(self.display_limit_choice)

	def _create_cache_group(self, sHelper):
		sHelper.addItem(wx.StaticText(self, label="Batas Penyimpanan Cache (Hari): Hapus berita yang lebih lama dari:"))
		self.cache_spin = wx.SpinCtrl(self, min=1, max=30, initial=config.get_config_val("cache_duration"))
		sHelper.addItem(self.cache_spin)

		sHelper.addItem(wx.StaticText(self, label="Tindakan Pemeliharaan:"))
		self.btn_clear_cache = sHelper.addItem(wx.Button(self, label="Hapus Semua Cache Berita"))
		self.btn_clear_cache.Bind(wx.EVT_BUTTON, self.on_clear_cache)

		# Button to open donation
		sHelper.addItem(wx.StaticText(self, label="Dukungan:"))
		self.btn_donate = sHelper.addItem(wx.Button(self, label="Dukungan / Donasi"))
		self.btn_donate.Bind(wx.EVT_BUTTON, self.on_donate)

	def on_donate(self, event):
		"""Show donation dialog."""
		dlg = DonationDialog(self)
		dlg.ShowModal()
		dlg.Destroy()

	def onSave(self):
		# Extract checked sources list
		enabled_srcs = [src for src, chk in self.source_checkboxes.items() if chk.GetValue()]
		if not enabled_srcs:
			# Enforce at least one source selected
			enabled_srcs = ["Detik"]
			
		config.set_config_val("enabled_sources", enabled_srcs)
		
		# Save interval selection
		interval_str = self.interval_choice.GetString(self.interval_choice.GetSelection())
		config.set_config_val("refresh_interval", int(interval_str))
		
		# Save notification options
		notify_selection = "digest" if self.notify_choice.GetSelection() == 0 else "immediate"
		config.set_config_val("notification_mode", notify_selection)
		
		config.set_config_val("notification_tone", self.beep_checkbox.GetValue())
		config.set_config_val("breaking_news_preference", self.breaking_checkbox.GetValue())
		
		# Save quiet hours ranges
		config.set_config_val("silent_hours_enabled", self.dnd_checkbox.GetValue())
		config.set_config_val("silent_hours_start", self.dnd_start_txt.GetValue().strip())
		config.set_config_val("silent_hours_end", self.dnd_end_txt.GetValue().strip())
		
		# Save SSL bypass checkbox and cache spin controls
		config.set_config_val("bypass_ssl_verification", self.ssl_checkbox.GetValue())
		config.set_config_val("cache_duration", self.cache_spin.GetValue())
		
		# Save display limit selection
		limit_str = self.display_limit_choice.GetString(self.display_limit_choice.GetSelection())
		config.set_config_val("max_display_count", int(limit_str))
		
		# Hand the new settings to the background thread. NVDA writes nvda.ini itself.
		from . import addon_instance
		if addon_instance:
			addon_instance.apply_settings()

		# Refresh the active news dialog if open to apply new filters/sources immediately
		refresh_active_dialog()

	def on_clear_cache(self, event):
		# Show confirmation dialog
		msg = "Apakah Anda yakin ingin menghapus semua cache berita yang disimpan?"
		title = "Konfirmasi Hapus Cache - NusaNews"
		dlg = wx.MessageDialog(self, msg, title, wx.YES_NO | wx.ICON_QUESTION)
		
		# NVDA dialog helper wrapping
		gui.mainFrame.prePopup()
		result = dlg.ShowModal()
		gui.mainFrame.postPopup()
		dlg.Destroy()
		
		if result == wx.ID_YES:
			try:
				cache.clear_cache()
				ui.message("Cache berita berhasil dikosongkan.")
				# Refresh active dialog if open
				refresh_active_dialog()
			except Exception as e:
				logHandler.log.error(f"NusaNews: Failed to clear cache: {e}")
				ui.message("Gagal mengosongkan cache berita.")
