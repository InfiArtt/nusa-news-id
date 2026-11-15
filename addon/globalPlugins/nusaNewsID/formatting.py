# formatting.py
#
# How a story is read out: in the news list, in notifications and in the article reader.
# Every place uses these functions, so a story always sounds the same. Words only, no brackets,
# bars or dashes, because NVDA reads those differently depending on the punctuation level.
# No NVDA imports, so the tests can use it directly.

from datetime import datetime, timedelta

from .models import NewsItem

_MONTHS = (
	"Januari",
	"Februari",
	"Maret",
	"April",
	"Mei",
	"Juni",
	"Juli",
	"Agustus",
	"September",
	"Oktober",
	"November",
	"Desember",
)


def parse_iso(value: str | None) -> datetime | None:
	"""A stored time as an aware datetime. Times stored without a zone are the computer's local time."""
	if not value:
		return None
	try:
		parsed = datetime.fromisoformat(value)
	except ValueError:
		return None
	return parsed if parsed.tzinfo else parsed.astimezone()


def story_time(item: NewsItem) -> datetime | None:
	"""When the story was published, or when the add-on first found it if the site gives no time."""
	return parse_iso(item.published_at) or parse_iso(item.found_at)


def local_now() -> datetime:
	"""The current local time. Tests replace it."""
	return datetime.now().astimezone()


def format_date(moment: datetime) -> str:
	"""For example "13 November 2026 pukul 20.00", in the computer's time zone."""
	local = moment.astimezone()
	return f"{local.day} {_MONTHS[local.month - 1]} {local.year} pukul {local.hour:02d}.{local.minute:02d}"


def format_time(moment: datetime | None, now: datetime | None = None) -> str:
	"""How long ago, for the last 24 hours; the date and time for older stories."""
	if moment is None:
		return ""
	now = now or local_now()
	age = now - moment
	if age < timedelta(minutes=1):
		return "baru saja"
	if age < timedelta(hours=1):
		return f"{int(age.total_seconds() // 60)} menit lalu"
	if age < timedelta(days=1):
		return f"{int(age.total_seconds() // 3600)} jam lalu"
	return format_date(moment)


def list_item_text(item: NewsItem, now: datetime | None = None) -> str:
	"""For example "Breaking. Gempa guncang Maluku. Antara, Nasional, 5 menit lalu. Belum dibaca." """
	parts = []
	if item.is_breaking:
		parts.append("Breaking.")
	parts.append(_sentence(item.title))
	details = [item.source, item.category]
	when = format_time(story_time(item), now)
	if when:
		details.append(when)
	parts.append(_sentence(", ".join(details)))
	if not item.seen:
		parts.append("Belum dibaca.")
	return " ".join(parts)


def load_more_text(count: int) -> str:
	"""The last item of a list that continues."""
	return f"Muat {count} berita berikutnya"


def notification_text(item: NewsItem) -> str:
	"""The announcement of one new story."""
	if item.is_breaking:
		return f"Breaking dari {item.source}: {_sentence(item.title)}"
	return f"Berita baru dari {item.source}: {_sentence(item.title)}"


def digest_text(count: int, gesture: str | None) -> str:
	"""The announcement of several new stories at once."""
	if gesture:
		return f"NusaNews: {count} berita baru. Tekan {gesture} untuk membuka."
	return f"NusaNews: {count} berita baru. Tetapkan tombol untuk membukanya di Gestur Masukan."


def article_header(item: NewsItem) -> str:
	"""The lines above an article's text, one fact per line."""
	lines = [item.title, f"{item.source}, kategori {item.category}"]
	published = parse_iso(item.published_at)
	if published:
		lines.append(f"Terbit {format_date(published)}")
	else:
		found = parse_iso(item.found_at)
		if found:
			# The site gives no time; this is when the add-on first saw the story.
			lines.append(f"Ditemukan {format_date(found)}")
	lines.append(item.url)
	return "\n".join(lines)


def article_text(item: NewsItem, body: str) -> str:
	"""What the reader shows: the header, an empty line, then the article."""
	return f"{article_header(item)}\n\n{body}"


def article_copy_text(item: NewsItem, body: str) -> str:
	"""What "Salin berita" copies: the title and the article, without the details."""
	return f"{item.title}\n\n{body}" if body else item.title


def _sentence(text: str) -> str:
	text = text.strip()
	return text if text.endswith((".", "!", "?")) else f"{text}."
