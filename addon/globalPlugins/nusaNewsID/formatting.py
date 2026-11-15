# formatting.py
#
# How a story is read out: in the news list, in notifications and in the article reader.
# Every place uses these functions, so a story always sounds the same. Words only, no brackets,
# bars or dashes, because NVDA reads those differently depending on the punctuation level.
# No NVDA imports, so the tests can use it directly.

from datetime import datetime, timedelta, tzinfo

import addonHandler

from .models import NewsItem

addonHandler.initTranslation()


def _months() -> tuple[str, ...]:
	return (
		# Translators: a month name, used in dates such as "13 November 2026, 20:05".
		_("January"),
		# Translators: a month name.
		_("February"),
		# Translators: a month name.
		_("March"),
		# Translators: a month name.
		_("April"),
		# Translators: a month name.
		_("May"),
		# Translators: a month name.
		_("June"),
		# Translators: a month name.
		_("July"),
		# Translators: a month name.
		_("August"),
		# Translators: a month name.
		_("September"),
		# Translators: a month name.
		_("October"),
		# Translators: a month name.
		_("November"),
		# Translators: a month name.
		_("December"),
	)


def category_label(category: str) -> str:
	"""The name of a category in the user's language. The cache keeps the Indonesian names."""
	labels = {
		# Translators: a news category.
		"Nasional": _("National"),
		# Translators: a news category.
		"Internasional": _("International"),
		# Translators: a news category.
		"Teknologi": _("Technology"),
		# Translators: a news category.
		"Politik": _("Politics"),
		# Translators: a news category.
		"Ekonomi": _("Economy"),
		# Translators: a news category.
		"Olahraga": _("Sports"),
		# Translators: a news category.
		"Entertainment": _("Entertainment"),
		# Translators: a news category: news about disability and people with disabilities.
		"Disabilitas": _("Disability"),
		# Translators: a news category: articles published on infiartt.com.
		"Artikel InfiArtt": _("InfiArtt articles"),
		# Translators: a news category: guides in the InfiArtt knowledge base.
		"Pusat Pengetahuan": _("InfiArtt knowledge base"),
	}
	return labels.get(category, category)


# The time zone to show times in. None means the computer's own zone; tests set it.
local_zone: tzinfo | None = None


def parse_iso(value: str | None) -> datetime | None:
	"""A stored time as an aware datetime. Times stored without a zone are the computer's local time."""
	if not value:
		return None
	try:
		parsed = datetime.fromisoformat(value)
	except ValueError:
		return None
	if parsed.tzinfo:
		return parsed
	return parsed.replace(tzinfo=local_zone) if local_zone else parsed.astimezone()


def story_time(item: NewsItem) -> datetime | None:
	"""When the story was published, or when the add-on first found it if the site gives no time."""
	return parse_iso(item.published_at) or parse_iso(item.found_at)


def local_now() -> datetime:
	"""The current local time. Tests replace it."""
	return datetime.now(local_zone).astimezone(local_zone)


def format_date(moment: datetime) -> str:
	"""For example "13 November 2026, 20:05", in the computer's time zone."""
	local = moment.astimezone(local_zone)
	# Translators: a date and time, for example "13 November 2026, 20:05".
	# Keep the names in braces; you can change their order and the words between them.
	return _("{day} {month} {year}, {hour}:{minute}").format(
		day=local.day,
		month=_months()[local.month - 1],
		year=local.year,
		hour=f"{local.hour:02d}",
		minute=f"{local.minute:02d}",
	)


def format_time(moment: datetime | None, now: datetime | None = None) -> str:
	"""How long ago, for the last 24 hours; the date and time for older stories."""
	if moment is None:
		return ""
	now = now or local_now()
	age = now - moment
	if age < timedelta(minutes=1):
		# Translators: the time of a story published less than a minute ago.
		return _("just now")
	if age < timedelta(hours=1):
		minutes = int(age.total_seconds() // 60)
		# Translators: the time of a story, for example "14 minutes ago".
		return ngettext("{count} minute ago", "{count} minutes ago", minutes).format(count=minutes)
	if age < timedelta(days=1):
		hours = int(age.total_seconds() // 3600)
		# Translators: the time of a story, for example "3 hours ago".
		return ngettext("{count} hour ago", "{count} hours ago", hours).format(count=hours)
	return format_date(moment)


def list_item_text(item: NewsItem, now: datetime | None = None) -> str:
	"""For example "Breaking. Gempa guncang Maluku. Antara, National, 5 minutes ago. Unread." """
	parts = []
	if item.is_breaking:
		# Translators: said before the title of a breaking news story in the news list.
		parts.append(_("Breaking."))
	parts.append(_sentence(item.title))
	details = [item.source, category_label(item.category)]
	if item.author:
		# Translators: who wrote a story, in the news list, for example "by Rexya".
		details.append(_("by {author}").format(author=item.author))
	when = format_time(story_time(item), now)
	if when:
		details.append(when)
	parts.append(_sentence(", ".join(details)))
	if not item.seen:
		# Translators: said after a story in the news list that has not been opened or marked read.
		parts.append(_("Unread."))
	return " ".join(parts)


def load_more_text(count: int) -> str:
	"""The last item of a list that continues."""
	# Translators: the last item of the news list, which shows more stories when pressed.
	return ngettext("Load {count} more story", "Load {count} more stories", count).format(count=count)


def notification_text(item: NewsItem) -> str:
	"""The announcement of one new story."""
	title = _sentence(item.title)
	if item.is_breaking:
		# Translators: announces one breaking story, for example "Breaking from Antara: Gempa guncang Maluku."
		return _("Breaking from {source}: {title}").format(source=item.source, title=title)
	# Translators: announces one new story, for example "New from Detik: Prabowo tiba di Manila."
	return _("New from {source}: {title}").format(source=item.source, title=title)


def digest_text(count: int, gesture: str | None) -> str:
	"""The announcement of several new stories at once."""
	if gesture:
		# Translators: announces several new stories. {gesture} is the key that opens the news list,
		# such as NVDA+shift+/.
		return ngettext(
			"NusaNews: {count} new story. Press {gesture} to open it.",
			"NusaNews: {count} new stories. Press {gesture} to open them.",
			count,
		).format(count=count, gesture=gesture)
	# Translators: announces several new stories when no key opens the news list.
	return ngettext(
		"NusaNews: {count} new story. To open it, assign a key in Input Gestures.",
		"NusaNews: {count} new stories. To open them, assign a key in Input Gestures.",
		count,
	).format(count=count)


def article_header(item: NewsItem) -> str:
	"""The lines above an article's text, one fact per line."""
	return "\n".join([item.title, *article_detail_lines(item), item.url])


def article_detail_lines(item: NewsItem) -> list[str]:
	"""The lines between an article's title and its link: source and category, and the time."""
	# Translators: the second line of an article in the reader, for example "Detik, category National".
	details = _("{source}, category {category}").format(
		source=item.source, category=category_label(item.category)
	)
	lines = [details]
	if item.author:
		# Translators: who wrote a story, in the article reader, for example "Written by Rexya".
		lines.append(_("Written by {author}").format(author=item.author))
	published = parse_iso(item.published_at)
	if published:
		# Translators: when the site published the story, for example "Published 13 November 2026, 20:05".
		lines.append(_("Published {date}").format(date=format_date(published)))
	else:
		found = parse_iso(item.found_at)
		if found:
			# Translators: for a story whose site gives no publication time, when the add-on first
			# found it, for example "Found 13 November 2026, 20:05".
			lines.append(_("Found {date}").format(date=format_date(found)))
	return lines


def preview_text(item: NewsItem) -> str:
	"""The preview under the news list: the whole title, its details, and the summary when there is one."""
	parts = [item.title, *article_detail_lines(item)]
	summary = (item.summary or "").strip()
	if summary and summary != item.title:
		parts.extend(["", summary])
	return "\n".join(parts)


def article_text(item: NewsItem, body: str) -> str:
	"""What the reader shows: the header, an empty line, then the article."""
	return f"{article_header(item)}\n\n{body}"


def article_copy_text(item: NewsItem, body: str) -> str:
	"""What "Copy story" copies: the title and the article, without the details."""
	return f"{item.title}\n\n{body}" if body else item.title


def _sentence(text: str) -> str:
	text = text.strip()
	return text if text.endswith((".", "!", "?")) else f"{text}."
