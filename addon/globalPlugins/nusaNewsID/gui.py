# gui.py
#
# The news list dialog, the article reader dialog and the settings panel.
# Everything here runs on the main thread.

import re
import threading

import addonHandler
import gui
import logHandler
import ui
import wx
from gui import guiHelper, nvdaControls
from gui.message import MessageDialog, ReturnCode
from gui.settingsDialogs import SettingsPanel

from . import cache, config, formatting, readerHtml
from .models import NewsItem
from .providers.articleContent import Article
from .providers.sourceManager import ALWAYS_ON_SOURCES, CATEGORIES, SOURCE_NAMES

addonHandler.initTranslation()

REFRESH_INTERVALS = (2, 5, 10, 15, 30, 60, 120)
DISPLAY_COUNTS = (20, 50, 100)
READER_ZOOMS = (100, 125, 150, 175, 200, 250, 300, 350, 400)
NOTIFICATION_MODES = ("digest", "immediate")


def _notification_mode_labels() -> list[str]:
	return [
		# Translators: a choice for how new stories are announced: one message with their number.
		_("Number of new stories"),
		# Translators: a choice for how new stories are announced: the title of each story.
		_("Title of each new story"),
	]


def _listed_sources() -> list[str]:
	"""The sources of the news list's filter: InfiArtt first, as it is always on, then the enabled ones."""
	return list(ALWAYS_ON_SOURCES) + config.read_settings()["enabled_sources"]


def _all_label() -> str:
	# Translators: the first choice of the source and category filters, which shows everything.
	return _("All")


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
		# Translators: said when copying fails because another program holds the clipboard.
		ui.message(_("Another program is using the clipboard. Try again."))
		return
	try:
		wx.TheClipboard.SetData(wx.TextDataObject(text))
		ui.message(done_message)
	except Exception:
		logHandler.log.exception("NusaNews: Copying failed.")
		# Translators: said when copying to the clipboard fails.
		ui.message(_("Could not copy."))
	finally:
		wx.TheClipboard.Close()


class DonationDialog(wx.Dialog):
	"""Dialog that displays read-only donation information."""

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
		label = wx.StaticText(self, label=_("Donation information:"))
		sizer.Add(label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
		text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(400, 150))
		text.SetValue(msg)
		sizer.Add(text, 1, wx.EXPAND | wx.ALL, 10)
		# Translators: button that closes a dialog.
		btn = wx.Button(self, wx.ID_OK, label=_("&Close"))
		sizer.Add(btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
		self.SetSizerAndFit(sizer)
		self.Centre()
		text.SetFocus()


class NusaNewsDialog(wx.Dialog):
	"""The list of cached stories, with filters and actions."""

	def __init__(self, parent):
		super().__init__(
			parent,
			# Translators: title of the news list dialog.
			title=_("NusaNews - Indonesian news reader"),
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
		)
		self.news_items: list[NewsItem] = []
		self.sources = _listed_sources()
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
		self.source_choice = filters.addLabeledControl(
			# Translators: label of the filter that shows the stories of one news site.
			_("&Source:"),
			wx.Choice,
			choices=[_all_label(), *self.sources],
		)
		self.source_choice.SetSelection(0)
		self.cat_choice = filters.addLabeledControl(
			# Translators: label of the filter that shows the stories of one category.
			_("Ca&tegory:"),
			wx.Choice,
			choices=[_all_label(), *(formatting.category_label(category) for category in CATEGORIES)],
		)
		self.cat_choice.SetSelection(0)
		sHelper.addItem(filters)

		# Translators: check box that shows only the stories not read yet.
		self.unread_checkbox = sHelper.addItem(wx.CheckBox(self, label=_("&Unread only")))

		# The label makes NVDA say "Daftar berita, list" when the list gets focus.
		self.news_listbox = sHelper.addLabeledControl(
			# Translators: label of the news list.
			_("News. Press Enter to read the selected story:"),
			wx.ListBox,
			style=wx.LB_SINGLE | wx.LB_NEEDED_SB,
			size=(700, 360),
		)

		buttons = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that copies the web address of the selected story.
		self.btn_copy_link = buttons.addButton(self, label=_("Copy &link"))
		# Translators: button that marks the selected story as read.
		self.btn_mark_read = buttons.addButton(self, label=_("&Mark read"))
		# Translators: button that marks every saved story as read.
		self.btn_mark_all = buttons.addButton(self, label=_("Mark &all read"))
		# Translators: button that checks the news sites for new stories now.
		self.btn_refresh = buttons.addButton(self, label=_("&Refresh"))
		# Translators: button that opens the donation dialog.
		self.btn_donate = buttons.addButton(self, label=_("D&onate"))
		self.btn_close = buttons.addButton(self, id=wx.ID_CANCEL, label=_("&Close"))
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
		# The first choice of each filter is "All"; the others follow self.sources and CATEGORIES.
		source_index = self.source_choice.GetSelection()
		category_index = self.cat_choice.GetSelection()
		sources_filter = self.sources if source_index <= 0 else [self.sources[source_index - 1]]
		cats_filter = list(CATEGORIES) if category_index <= 0 else [CATEGORIES[category_index - 1]]
		all_items = cache.get_news_items(
			enabled_sources=sources_filter,
			enabled_categories=cats_filter,
			filter_unread_only=self.unread_checkbox.GetValue(),
		)
		total_count = len(all_items)
		self.news_items = all_items[: self.current_display_limit]
		now = formatting.local_now()
		lines = [formatting.list_item_text(item, now) for item in self.news_items]
		self._has_more = total_count > self.current_display_limit
		if not lines:
			# An empty list is read as "unknown"; this line says why it is empty.
			# Translators: the only line of the news list when no saved story matches the filters.
			lines.append(_("No stories here yet. New stories appear after the next check."))
		if self._has_more:
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
			if self._has_more:
				self.on_load_more()
			return
		item = self._selected_item()
		if item is None:
			return
		try:
			NusaNewsReaderDialog(self, item).Show()
		except Exception:
			logHandler.log.exception("NusaNews: Opening the article reader failed.")
			# Translators: said when the article reader cannot open.
			ui.message(_("Could not open the story."))

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
			# Translators: said after copying a story's web address.
			_copy_to_clipboard(item.url, _("Link copied."))

	def on_mark_read(self, event):
		item = self._selected_item()
		if item is None:
			return
		cache.mark_as_read(item.guid)
		self.update_item(item.guid)
		# Translators: said after marking a story as read.
		ui.message(_("Marked read."))

	def on_mark_all_read(self, event):
		item = self._selected_item()
		cache.mark_all_as_read()
		self.populate_list(keep_guid=item.guid if item else None)
		# Translators: said after marking every story as read.
		ui.message(_("All stories marked read."))

	def on_refresh(self, event):
		from . import addon_instance

		if addon_instance and addon_instance.request_refresh():
			# Translators: said when Refresh starts a check of the news sites.
			ui.message(_("Checking for new stories..."))
		else:
			# Translators: said when Refresh cannot start because the add-on is not running.
			ui.message(_("Could not refresh. The add-on is not running."))

	def on_close(self, event):
		global active_dialog
		active_dialog = None
		self.Destroy()

	def reload_settings(self):
		"""Apply changed sources and new stories, keeping the filters and the selected story."""
		item = self._selected_item()
		source_index = self.source_choice.GetSelection()
		current_source = self.sources[source_index - 1] if source_index > 0 else None
		self.sources = _listed_sources()
		self.current_display_limit = max(
			self.current_display_limit, config.get_config_val("max_display_count")
		)
		self.source_choice.Set([_all_label(), *self.sources])
		index = self.sources.index(current_source) + 1 if current_source in self.sources else 0
		self.source_choice.SetSelection(index)
		self.populate_list(keep_guid=item.guid if item else None)


def _webview_available() -> bool:
	"""Whether a web page can be shown in a window.

	The reader uses Internet Explorer's engine, as NVDA's own HTML messages do: it is part of Windows,
	opens at once, and NVDA reads it in browse mode.
	"""
	try:
		from wx import html2

		return bool(html2.WebView.IsBackendAvailable(html2.WebViewBackendIE))
	except Exception:
		return False


def _reader_labels() -> dict[str, str]:
	return {
		# Translators: button that opens the story on its website.
		"browser": _("Open in &browser"),
		"link": _("Copy &link"),
		# Translators: button that copies the title and text of the story.
		"copy": _("Copy &story"),
		"close": _("&Close"),
		# Translators: name of the group of buttons at the end of a story in the reader.
		"actions": _("Actions"),
	}


class NusaNewsReaderDialog(wx.Dialog):
	"""Reads one story: its details and its article, downloaded when needed.

	The article is shown as a web page (readerHtml), which NVDA reads in browse mode with headings,
	lists and links, and whose text low vision users can enlarge with Control+plus and Control+minus.
	Without a web engine it falls back to a plain text box.
	"""

	def __init__(self, parent: NusaNewsDialog, item: NewsItem):
		super().__init__(
			parent,
			title=item.title,
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
		)
		self.item = item
		self.list_dialog = parent
		self.article: Article | None = None
		self.web = None
		self.text_ctrl = None
		self._zoom = config.get_config_val("reader_zoom")

		main_sizer = wx.BoxSizer(wx.VERTICAL)
		if _webview_available():
			from wx import html2

			self.web = html2.WebView.New(self, backend=html2.WebViewBackendIE, size=(900, 650))
			self.web.EnableContextMenu(False)
			self.web.EnableHistory(False)
			main_sizer.Add(self.web, 1, wx.EXPAND)
			self.web.Bind(html2.EVT_WEBVIEW_NAVIGATING, self._on_navigating)
			self.web.Bind(html2.EVT_WEBVIEW_NEWWINDOW, self._on_new_window)
			self.web.Bind(html2.EVT_WEBVIEW_LOADED, self._on_loaded)
			self.SetSizer(main_sizer)
			self.SetSize((900, 700))
			self._bind_keys()
		else:
			sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
			self.text_ctrl = sHelper.addLabeledControl(
				# Translators: label of the text box with the story in the article reader.
				_("Story text:"),
				wx.TextCtrl,
				style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
				size=(700, 450),
			)
			labels = _reader_labels()
			buttons = guiHelper.ButtonHelper(wx.HORIZONTAL)
			btn_browser = buttons.addButton(self, label=labels["browser"])
			btn_copy_link = buttons.addButton(self, label=labels["link"])
			btn_copy = buttons.addButton(self, label=labels["copy"])
			btn_close = buttons.addButton(self, id=wx.ID_CANCEL, label=labels["close"])
			sHelper.addDialogDismissButtons(buttons)
			main_sizer.Add(sHelper.sizer, 1, wx.EXPAND | wx.ALL, guiHelper.BORDER_FOR_DIALOGS)
			self.SetSizerAndFit(main_sizer)
			self.SetEscapeId(wx.ID_CANCEL)
			btn_browser.Bind(wx.EVT_BUTTON, self.on_open_browser)
			btn_copy_link.Bind(wx.EVT_BUTTON, self.on_copy_link)
			btn_copy.Bind(wx.EVT_BUTTON, self.on_copy)
			btn_close.Bind(wx.EVT_BUTTON, self.on_close)
		self.Centre()
		self.Bind(wx.EVT_CLOSE, self.on_close)

		# Opening a story marks it read.
		cache.mark_as_read(item.guid)
		self.load_article()
		(self.web or self.text_ctrl).SetFocus()

	def load_article(self):
		"""Show the saved article, or download it in a background thread."""
		article = cache.get_article(self.item.guid)
		if article and (article.blocks or article.locked_note):
			self._show(article)
			return
		# Translators: shown in the article reader while the story downloads.
		self._show(None, _("Downloading the story..."))
		# Settings are read here on the main thread, not in the download thread.
		bypass_ssl = config.get_config_val("bypass_ssl_verification")
		threading.Thread(
			target=self._bg_fetch,
			args=(self.item.guid, self.item.source, self.item.url, bypass_ssl),
			daemon=True,
		).start()

	def _show(self, article: Article | None, message: str | None = None) -> None:
		self.article = article
		if article and article.locked_note:
			# Translators: shown in the reader for an article only members of InfiArtt can read.
			message = _(
				"Only InfiArtt members can read this article. Press Open in browser and sign in to read it."
			)
		if self.web is not None:
			import languageHandler

			page = readerHtml.build_page(
				title=self.item.title,
				details=formatting.article_detail_lines(self.item),
				url=self.item.url,
				article=article,
				message=message,
				ui_language=languageHandler.getLanguage(),
				labels=_reader_labels(),
				zoom=self._zoom,
			)
			self.web.SetPage(page, "")
		else:
			body = "\n\n".join(part for part in (message, article.text if article else "") if part)
			self.text_ctrl.SetValue(formatting.article_text(self.item, body))
			self.text_ctrl.SetInsertionPoint(0)

	def _bg_fetch(self, guid, source, url, bypass_ssl):
		"""Runs in a background thread."""
		from .providers.sourceManager import provider_for

		try:
			article = provider_for(source).fetch_article(url, bypass_ssl)
		except Exception:
			logHandler.log.exception("NusaNews: Downloading an article failed.")
			article = None
		wx.CallAfter(self._on_fetch_complete, guid, article)

	def _on_fetch_complete(self, guid, article):
		if article:
			cache.update_article(guid, article)
		if not self:
			# The reader was closed while downloading; the article is saved for next time.
			return
		if article:
			self._show(article)
			# Translators: said when the story has downloaded and is shown in the article reader.
			ui.message(_("Story loaded."))
		else:
			self._show(
				None,
				# Translators: shown in the article reader when the story cannot be downloaded.
				_(
					"Could not download the story. "
					"Check your internet connection, or press Open in browser (Alt+B) "
					"to read it on the website."
				),
			)
			# Translators: said when the story cannot be downloaded.
			ui.message(_("Could not download the story."))

	def _on_loaded(self, event):
		"""Put the focus, and so NVDA's browse mode, in the page."""
		self.web.SetFocus()

	def _bind_keys(self) -> None:
		"""Shortcut keys for the page, as a table the dialog handles before the web engine sees the keys.

		Escape closes; Alt and the underlined letter of a button runs it; Control+plus, Control+minus and
		Control+0 change the text size.
		"""
		entries = []

		def add(flags: int, key: int, handler) -> None:
			command = wx.NewIdRef()
			self.Bind(wx.EVT_MENU, lambda event: handler(), id=command)
			entries.append(wx.AcceleratorEntry(flags, key, command))

		add(wx.ACCEL_NORMAL, wx.WXK_ESCAPE, self.Close)
		for action, label in _reader_labels().items():
			letter = readerHtml.shortcut_key(label)
			if letter and action in readerHtml.ACTIONS:
				add(wx.ACCEL_ALT, ord(letter.upper()), lambda action=action: self._run_action(action))
		for key in (ord("="), wx.WXK_NUMPAD_ADD):
			add(wx.ACCEL_CTRL, key, lambda: self._change_zoom(1))
		for key in (ord("-"), wx.WXK_NUMPAD_SUBTRACT):
			add(wx.ACCEL_CTRL, key, lambda: self._change_zoom(-1))
		add(wx.ACCEL_CTRL, ord("0"), lambda: self._change_zoom(0))
		self.SetAcceleratorTable(wx.AcceleratorTable(entries))

	def _change_zoom(self, step: int) -> None:
		"""One step larger or smaller in READER_ZOOMS, or back to 100 percent with step 0."""
		if step == 0:
			zoom = 100
		else:
			index = _nearest_index(READER_ZOOMS, self._zoom) + step
			zoom = READER_ZOOMS[max(0, min(len(READER_ZOOMS) - 1, index))]
		self._zoom = zoom
		self.web.RunScript(f'document.documentElement.style.fontSize = "{readerHtml.text_size(zoom)}";')
		config.set_config_val("reader_zoom", zoom)
		# Translators: said when the text size of the article reader changes,
		# for example "Text size 150 percent".
		ui.message(_("Text size {percent} percent").format(percent=zoom))

	def _on_navigating(self, event):
		"""Buttons in the page send nusanews-action: addresses; links open in the browser."""
		url = event.GetURL()
		if url.startswith("nusanews-action:"):
			event.Veto()
			wx.CallAfter(self._run_action, url.split(":", 1)[1])
		elif url.startswith(("http://", "https://")):
			event.Veto()
			self._open_url(url)

	def _on_new_window(self, event):
		self._open_url(event.GetURL())

	def _run_action(self, action: str) -> None:
		{
			"browser": self.on_open_browser,
			"link": self.on_copy_link,
			"copy": self.on_copy,
			"close": lambda event: self.Close(),
		}.get(action, lambda event: None)(None)

	def _open_url(self, url: str) -> None:
		try:
			import os

			os.startfile(url)
		except Exception:
			logHandler.log.exception(f"NusaNews: Opening {url} failed.")
			# Translators: said when the web browser cannot be opened.
			ui.message(_("Could not open the browser."))

	def on_open_browser(self, event):
		self._open_url(self.item.url)

	def on_copy_link(self, event):
		_copy_to_clipboard(self.item.url, _("Link copied."))

	def on_copy(self, event):
		body = self.article.text if self.article else ""
		# Translators: said after copying the title and text of a story.
		_copy_to_clipboard(formatting.article_copy_text(self.item, body), _("Story copied."))

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
			# Translators: label of the list of news sites the add-on checks.
			_("News &sources to follow (InfiArtt is always checked):"),
			nvdaControls.CustomCheckListBox,
			choices=self.sources_list,
		)
		self.sources_checklist.SetCheckedStrings(settings["enabled_sources"])
		self.sources_checklist.SetSelection(0)

		self.interval_choice = sHelper.addLabeledControl(
			# Translators: label of the choice of how often the add-on checks for news.
			_("Check for new stories e&very (minutes):"),
			wx.Choice,
			choices=[str(m) for m in REFRESH_INTERVALS],
		)
		self.interval_choice.SetSelection(_nearest_index(REFRESH_INTERVALS, settings["refresh_interval"]))

		# Translators: name of a group of settings.
		notifications = self._group(sHelper, _("Notifications"))
		self.notify_choice = notifications.addLabeledControl(
			# Translators: label of the choice of how new stories are announced.
			_("&How to announce new stories:"),
			wx.Choice,
			choices=_notification_mode_labels(),
		)
		mode = settings["notification_mode"]
		self.notify_choice.SetSelection(NOTIFICATION_MODES.index(mode) if mode in NOTIFICATION_MODES else 0)
		self.beep_checkbox = notifications.addItem(
			# Translators: check box in the settings.
			wx.CheckBox(self._box(notifications), label=_("Play a &tone when new stories arrive"))
		)
		self.beep_checkbox.SetValue(settings["notification_tone"])
		self.breaking_checkbox = notifications.addItem(
			# Translators: check box in the settings.
			wx.CheckBox(self._box(notifications), label=_("Announce &breaking news during quiet hours too"))
		)
		self.breaking_checkbox.SetValue(settings["breaking_news_preference"])

		# Translators: name of a group of settings: hours when new stories are not announced.
		quiet = self._group(sHelper, _("Quiet hours"))
		# Translators: check box in the settings.
		self.dnd_checkbox = quiet.addItem(wx.CheckBox(self._box(quiet), label=_("&Use quiet hours")))
		self.dnd_checkbox.SetValue(settings["silent_hours_enabled"])
		self.dnd_checkbox.Bind(wx.EVT_CHECKBOX, self._on_dnd_toggled)
		self.dnd_start_txt = quiet.addLabeledControl(
			# Translators: label of the field for the start of quiet hours.
			_("Sta&rt (hours:minutes, such as 22:00):"),
			wx.TextCtrl,
		)
		self.dnd_start_txt.SetValue(settings["silent_hours_start"])
		self.dnd_end_txt = quiet.addLabeledControl(
			# Translators: label of the field for the end of quiet hours.
			_("&End (hours:minutes, such as 06:00):"),
			wx.TextCtrl,
		)
		self.dnd_end_txt.SetValue(settings["silent_hours_end"])
		self._on_dnd_toggled(None)

		self.display_limit_choice = sHelper.addLabeledControl(
			# Translators: label of the choice of how many stories the news list shows before "Load more".
			_("&Number of stories shown at a time:"),
			wx.Choice,
			choices=[str(n) for n in DISPLAY_COUNTS],
		)
		self.display_limit_choice.SetSelection(_nearest_index(DISPLAY_COUNTS, settings["max_display_count"]))

		self.zoom_choice = sHelper.addLabeledControl(
			# Translators: label of the choice of text size in the article reader, in percent.
			# Control+plus and Control+minus in the reader change it too.
			_("Reader te&xt size (percent):"),
			wx.Choice,
			choices=[str(size) for size in READER_ZOOMS],
		)
		self.zoom_choice.SetSelection(_nearest_index(READER_ZOOMS, settings["reader_zoom"]))

		# Translators: name of a group of settings.
		storage = self._group(sHelper, _("Storage"))
		self.cache_spin = storage.addLabeledControl(
			# Translators: label of the number of days the add-on keeps stories.
			_("&Keep stories for (days):"),
			nvdaControls.SelectOnFocusSpinCtrl,
			min=1,
			max=30,
			initial=settings["cache_duration"],
		)
		self.btn_clear_cache = storage.addItem(
			# Translators: button that deletes every saved story and article.
			wx.Button(self._box(storage), label=_("&Delete all saved stories"))
		)
		self.btn_clear_cache.Bind(wx.EVT_BUTTON, self.on_clear_cache)

		self.ssl_checkbox = sHelper.addItem(
			wx.CheckBox(
				self,
				# Translators: check box in the settings. It makes connections less safe.
				label=_("Skip security certi&ficate checks (only if connections always fail; not safe)"),
			)
		)
		self.ssl_checkbox.SetValue(settings["bypass_ssl_verification"])

		# Translators: button in the settings that opens the donation dialog.
		self.btn_donate = sHelper.addItem(wx.Button(self, label=_("Support and d&onations")))
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
			fields = (
				# Translators: error when the start of quiet hours is not a time.
				(self.dnd_start_txt, _("The start of quiet hours must be a time such as 22:00.")),
				# Translators: error when the end of quiet hours is not a time.
				(self.dnd_end_txt, _("The end of quiet hours must be a time such as 06:00.")),
			)
			for field, message in fields:
				if not _TIME.match(field.GetValue().strip()):
					# Translators: title of the error about quiet hours.
					MessageDialog.alert(message, _("Invalid quiet hours"), self)
					field.SetFocus()
					return False
		if not self.sources_checklist.GetCheckedItems():
			MessageDialog.alert(
				# Translators: error when no news source is checked in the settings.
				_("Choose at least one news source."),
				# Translators: title of the error about news sources.
				_("No news source"),
				self,
			)
			self.sources_checklist.SetFocus()
			return False
		return super().isValid()

	def onSave(self):
		config.set_config_val("enabled_sources", list(self.sources_checklist.GetCheckedStrings()))
		config.set_config_val("refresh_interval", REFRESH_INTERVALS[self.interval_choice.GetSelection()])
		config.set_config_val("notification_mode", NOTIFICATION_MODES[self.notify_choice.GetSelection()])
		config.set_config_val("notification_tone", self.beep_checkbox.GetValue())
		config.set_config_val("breaking_news_preference", self.breaking_checkbox.GetValue())
		config.set_config_val("silent_hours_enabled", self.dnd_checkbox.GetValue())
		config.set_config_val("silent_hours_start", _normal_time(self.dnd_start_txt.GetValue()))
		config.set_config_val("silent_hours_end", _normal_time(self.dnd_end_txt.GetValue()))
		config.set_config_val("bypass_ssl_verification", self.ssl_checkbox.GetValue())
		config.set_config_val("cache_duration", self.cache_spin.GetValue())
		config.set_config_val("max_display_count", DISPLAY_COUNTS[self.display_limit_choice.GetSelection()])
		config.set_config_val("reader_zoom", READER_ZOOMS[self.zoom_choice.GetSelection()])

		# Hand the new settings to the background thread. NVDA writes nvda.ini itself.
		from . import addon_instance

		if addon_instance:
			addon_instance.apply_settings()
		refresh_active_dialog()

	def on_clear_cache(self, event):
		result = MessageDialog.confirm(
			# Translators: question before deleting every saved story.
			_("Delete all saved stories and articles? This cannot be undone."),
			# Translators: title of the question before deleting every saved story.
			_("Delete saved stories"),
			self,
			# Translators: button that confirms deleting every saved story.
			okLabel=_("&Delete"),
			# Translators: button that keeps the saved stories.
			cancelLabel=_("&Cancel"),
		)
		if result != ReturnCode.OK:
			return
		try:
			cache.clear_cache()
			# Translators: said after deleting every saved story.
			ui.message(_("All saved stories deleted."))
			refresh_active_dialog()
		except Exception:
			logHandler.log.exception("NusaNews: Clearing the cache failed.")
			# Translators: said when deleting the saved stories fails.
			ui.message(_("Could not delete the saved stories."))


def _nearest_index(values: tuple[int, ...], value: int) -> int:
	"""The index of the choice closest to a saved value, for values saved before a choice existed."""
	return min(range(len(values)), key=lambda index: abs(values[index] - value))


def _normal_time(text: str) -> str:
	"""Write a time as HH:MM, so "6:00" is saved as "06:00"."""
	match = _TIME.match(text.strip())
	if not match:
		return text.strip()
	return f"{int(match.group(1)):02d}:{match.group(2)}"
