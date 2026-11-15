# textUtils.py
#
# Text rules shared by every provider: dates, titles and keyword matching.
# No NVDA imports, so the tests can use it directly.

import email.utils
import html
import re
from datetime import UTC, datetime, timedelta, timezone

# Indonesian news sites give their times in Western Indonesia Time (WIB).
WIB = timezone(timedelta(hours=7), "WIB")

_MONTHS = {
	"jan": 1,
	"januari": 1,
	"january": 1,
	"feb": 2,
	"februari": 2,
	"february": 2,
	"mar": 3,
	"maret": 3,
	"march": 3,
	"apr": 4,
	"april": 4,
	"mei": 5,
	"may": 5,
	"jun": 6,
	"juni": 6,
	"june": 6,
	"jul": 7,
	"juli": 7,
	"july": 7,
	"agu": 8,
	"agt": 8,
	"agus": 8,
	"agustus": 8,
	"aug": 8,
	"august": 8,
	"sep": 9,
	"sept": 9,
	"september": 9,
	"okt": 10,
	"oktober": 10,
	"oct": 10,
	"october": 10,
	"nov": 11,
	"nop": 11,
	"november": 11,
	"des": 12,
	"desember": 12,
	"dec": 12,
	"december": 12,
}
_MONTH_NAMES = "|".join(sorted(_MONTHS, key=len, reverse=True))

_RELATIVE = re.compile(
	r"\b(\d+)\s*(detik|menit|jam|hari|minggu|pekan|bulan|tahun|seconds?|minutes?|hours?|days?|weeks?|months?|years?)"
	r"\s+(?:yang\s+)?(?:lalu|ago)\b",
	re.IGNORECASE,
)
_RELATIVE_UNITS = {
	"detik": 1,
	"second": 1,
	"menit": 60,
	"minute": 60,
	"jam": 3600,
	"hour": 3600,
	"hari": 86400,
	"day": 86400,
	"minggu": 7 * 86400,
	"pekan": 7 * 86400,
	"week": 7 * 86400,
	"bulan": 30 * 86400,
	"month": 30 * 86400,
	"tahun": 365 * 86400,
	"year": 365 * 86400,
}
_ISO = re.compile(
	r"\b(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?(Z|[+-]\d{2}:?\d{2})?)?"
)
_DAY_MONTH_YEAR = re.compile(
	rf"\b(\d{{1,2}})\s+({_MONTH_NAMES})\.?\s+(\d{{4}})(?:\s*,?\s*(?:pukul\s+)?(\d{{1,2}})[:.](\d{{2}}))?",
	re.IGNORECASE,
)
_NUMERIC = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})(?:\s*,?\s*(\d{1,2})[:.](\d{2}))?")
_YESTERDAY = re.compile(r"\bkemarin\b(?:\s*,?\s*(?:pukul\s+)?(\d{1,2})[:.](\d{2}))?", re.IGNORECASE)
_UNIX = re.compile(r"^\d{10}$")


def now() -> datetime:
	"""The current time in WIB. Tests replace it."""
	return datetime.now(WIB)


def parse_date(text: str | None, reference: datetime | None = None) -> datetime | None:
	"""Read a date in any form the sites use, or None.

	Handles RSS dates, ISO dates, Unix timestamps, "15 November 2026, 03:02", "15/11/2026",
	"kemarin" and relative times such as "10 jam yang lalu", which count back from ``reference``.
	Times without a time zone are taken as WIB.
	"""
	if not text:
		return None
	text = html.unescape(text).strip()
	if not text:
		return None
	reference = reference or now()
	if _UNIX.match(text):
		return datetime.fromtimestamp(int(text), WIB)
	if "," in text[:5] or re.search(r"\d{2}:\d{2}:\d{2} (?:[+-]\d{4}|GMT|UT)", text):
		try:
			parsed = email.utils.parsedate_to_datetime(text)
		except (TypeError, ValueError, IndexError):
			parsed = None
		if parsed is not None:
			return parsed if parsed.tzinfo else parsed.replace(tzinfo=WIB)
	match = _ISO.search(text)
	if match:
		year, month, day, hour, minute, second, zone = match.groups()
		try:
			parsed = datetime(
				int(year), int(month), int(day), int(hour or 0), int(minute or 0), int(second or 0)
			)
		except ValueError:
			return None
		if zone:
			if zone == "Z":
				return parsed.replace(tzinfo=UTC)
			sign = 1 if zone[0] == "+" else -1
			digits = zone[1:].replace(":", "")
			offset = timedelta(hours=int(digits[:2]), minutes=int(digits[2:]))
			return parsed.replace(tzinfo=timezone(sign * offset))
		return parsed.replace(tzinfo=WIB)
	match = _RELATIVE.search(text)
	if match:
		amount, unit = int(match.group(1)), match.group(2).lower().rstrip("s")
		return reference - timedelta(seconds=amount * _RELATIVE_UNITS[unit])
	match = _DAY_MONTH_YEAR.search(text)
	if match:
		day, monthName, year, hour, minute = match.groups()
		try:
			return datetime(
				int(year), _MONTHS[monthName.lower()], int(day), int(hour or 0), int(minute or 0), tzinfo=WIB
			)
		except ValueError:
			return None
	match = _NUMERIC.search(text)
	if match:
		day, month, year, hour, minute = match.groups()
		try:
			return datetime(int(year), int(month), int(day), int(hour or 0), int(minute or 0), tzinfo=WIB)
		except ValueError:
			return None
	match = _YESTERDAY.search(text)
	if match:
		yesterday = reference.astimezone(WIB) - timedelta(days=1)
		hour, minute = match.groups()
		if hour is None:
			return yesterday
		return yesterday.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
	return None


def looks_like_date(text: str) -> bool:
	"""Whether a piece of text is (or contains) a date or time, such as a card's "12 jam lalu"."""
	return bool(
		_RELATIVE.search(text)
		or _DAY_MONTH_YEAR.search(text)
		or _NUMERIC.search(text)
		or _ISO.search(text)
		or re.fullmatch(r"\s*\d{1,2}[:.]\d{2}\s*(?:WIB)?\s*", text)
	)


# Leftovers that sites put around a title: a time before it ("18:13Jangan ..."), a video length,
# or a label such as "VIDEO:" or "FOTO:".
_TITLE_PREFIXES = re.compile(r"^(?:\d{1,2}[:.]\d{2}(?:\s*WIB)?\s*)+", re.IGNORECASE)


def clean_title(text: str, extra_patterns: tuple[str, ...] = ()) -> str:
	"""Unescape HTML, join whitespace and remove leftovers around the title."""
	title = html.unescape(text or "")
	title = re.sub(r"\s+", " ", title).strip()
	title = _TITLE_PREFIXES.sub("", title)
	for pattern in extra_patterns:
		title = re.sub(pattern, "", title, flags=re.IGNORECASE).strip()
	return title.strip(" -|:–—")


def keyword_pattern(keywords: tuple[str, ...]) -> re.Pattern:
	"""A pattern that finds any of the keywords as whole words, ignoring case."""
	alternatives = "|".join(re.escape(keyword).replace(r"\ ", r"\s+") for keyword in keywords)
	return re.compile(rf"(?<![\w-])(?:{alternatives})(?![\w-])", re.IGNORECASE)


# Disasters and emergencies only. Words such as "presiden" or "waspada" made ordinary news "breaking".
BREAKING_KEYWORDS: tuple[str, ...] = (
	"breaking news",
	"gempa",
	"tsunami",
	"erupsi",
	"meletus",
	"banjir bandang",
	"longsor",
	"tanah longsor",
	"kebakaran hutan",
	"bencana",
	"darurat",
	"evakuasi",
	"peringatan dini",
	"bom",
	"teroris",
	"terorisme",
)

# Words used only, or almost only, about disability. Words with common other meanings
# ("lumpuh" for traffic, "cacat" for laws, "inklusif" for economy, "buta" in "buta huruf") are left out.
DISABILITY_KEYWORDS: tuple[str, ...] = (
	"disabilitas",
	"difabel",
	"penyandang disabilitas",
	"tunanetra",
	"tunarungu",
	"tunadaksa",
	"tunawicara",
	"tunagrahita",
	"tunalaras",
	"tuli",
	"autis",
	"autisme",
	"braille",
	"slb",
	"sekolah luar biasa",
	"kursi roda",
	"down syndrome",
	"sindrom down",
	"asperger",
	"adhd",
	"cerebral palsy",
	"berkebutuhan khusus",
	"alat bantu dengar",
	"kaki palsu",
	"tangan palsu",
	"bahasa isyarat",
	"juru bahasa isyarat",
	"ramah disabilitas",
	"ramah difabel",
	"low vision",
	"pembaca layar",
	"screen reader",
)

BREAKING_PATTERN = keyword_pattern(BREAKING_KEYWORDS)
DISABILITY_PATTERN = keyword_pattern(DISABILITY_KEYWORDS)


def is_breaking(title: str) -> bool:
	return bool(BREAKING_PATTERN.search(title))


def is_about_disability(text: str) -> bool:
	return bool(DISABILITY_PATTERN.search(text))
