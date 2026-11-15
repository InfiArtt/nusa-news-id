# cache.py
#
# The cache of news stories, kept in memory and saved as JSON, keyed by guid.
# Every function is called on the main thread. The file is written by a short-lived timer thread
# about two seconds after the last change, and once more when NVDA closes, so small actions such as
# marking a story read never wait for the disk.
# The file format and field names are the same as in version 1.0.2, so older caches load unchanged.
# Article texts are kept in separate files, read only when an article is opened.

import contextlib
import datetime
import hashlib
import json
import os
import shutil
import threading

import globalVars
import logHandler

from .formatting import parse_iso, story_time
from .models import NewsItem
from .providers.articleContent import Article, blocks_from_text, parse_blocks
from .providers.textUtils import is_breaking, parse_date

CACHE_FILE = "nusaNewsCache.json"
ARTICLES_DIR = "articles"
SAVE_DELAY_SECONDS = 2.0

_stories: dict[str, dict] | None = None
# Held while the stories change or are written out, so a write never sees a half-made change.
_lock = threading.RLock()
_saveTimer: threading.Timer | None = None


def get_cache_dir() -> str:
	"""The folder of the cache, inside NVDA's configuration folder."""
	try:
		config_dir = globalVars.appArgs.configPath
		if config_dir:
			return os.path.join(config_dir, "nusaNewsID")
	except Exception:
		pass
	# Fallback path traversal (5 directories up from addon/globalPlugins/nusaNewsID/cache.py)
	path = os.path.abspath(__file__)
	for _ in range(5):
		path = os.path.dirname(path)
	return os.path.join(path, "nusaNewsID")


def get_cache_path() -> str:
	cache_dir = get_cache_dir()
	os.makedirs(cache_dir, exist_ok=True)
	return os.path.join(cache_dir, CACHE_FILE)


def _article_path(guid: str, extension: str = "json") -> str:
	"""Articles are saved as JSON (structure and language); version 1.1.0 drafts saved plain .txt."""
	name = hashlib.sha1(guid.encode("utf-8")).hexdigest()
	return os.path.join(get_cache_dir(), ARTICLES_DIR, f"{name}.{extension}")


def init_db() -> None:
	"""Load the cache into memory, moving a cache from the place version 1.0.0 used."""
	global _stories
	path = get_cache_path()
	try:
		old_path = os.path.join(os.path.dirname(get_cache_dir()), CACHE_FILE)
		if os.path.exists(old_path) and not os.path.exists(path):
			logHandler.log.info("NusaNews: Moving the cache file to its own folder.")
			shutil.copy2(old_path, path)
			os.remove(old_path)
	except Exception:
		logHandler.log.exception("NusaNews: Moving the old cache file failed.")
	stories = _read_file(path)
	changed = False
	for guid, val in stories.items():
		# Older versions stored dates as the site's text and article texts inside this file.
		published = _published_iso(val)
		if published != val.get("published_at"):
			val["published_at"] = published
			changed = True
		content = val.pop("content", None)
		if content:
			_write_article(guid, Article(blocks=blocks_from_text(content)))
			changed = True
	with _lock:
		_stories = stories
	if changed:
		_schedule_save()


def _data() -> dict[str, dict]:
	if _stories is None:
		init_db()
	return _stories  # type: ignore[return-value]


def _read_file(path: str) -> dict[str, dict]:
	if not os.path.exists(path):
		return {}
	try:
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		return data if isinstance(data, dict) else {}
	except Exception:
		logHandler.log.exception("NusaNews: Reading the cache failed; starting with an empty one.")
		return {}


def _schedule_save() -> None:
	"""Write the cache a little later, once, however many changes come before then."""
	global _saveTimer
	with _lock:
		if _saveTimer is not None:
			_saveTimer.cancel()
		_saveTimer = threading.Timer(SAVE_DELAY_SECONDS, flush)
		_saveTimer.name = "NusaNewsCacheSave"
		_saveTimer.daemon = True
		_saveTimer.start()


def flush() -> None:
	"""Write the cache now if anything changed. Safe from any thread."""
	global _saveTimer
	with _lock:
		if _saveTimer is not None:
			_saveTimer.cancel()
			_saveTimer = None
		if _stories is None:
			return
		text = json.dumps(_stories, ensure_ascii=False, separators=(",", ":"))
	path = get_cache_path()
	tmp_path = path + ".tmp"
	try:
		with open(tmp_path, "w", encoding="utf-8") as f:
			f.write(text)
		# Replacing the file in one step keeps the old cache if NVDA stops halfway.
		os.replace(tmp_path, path)
	except Exception:
		logHandler.log.exception("NusaNews: Writing the cache failed.")
		with contextlib.suppress(Exception):
			os.remove(tmp_path)


def is_empty() -> bool:
	return not _data()


def sources() -> set[str]:
	"""The sources that have at least one saved story."""
	return {val.get("source", "") for val in _data().values()}


def save_news_items(
	items: list[NewsItem],
	mark_seen: bool = False,
	quiet_sources: set[str] | None = None,
	refresh_sources: tuple[str, ...] = (),
) -> list[NewsItem]:
	"""Add the stories not cached yet and return them. A story found again in another category gets it too.

	mark_seen saves every new story as read, for the first fill of an empty cache; quiet_sources does the
	same for the stories of those sources only (a source's first fill). For refresh_sources (InfiArtt, whose
	API is the source of truth), saved stories take the title, time, summary and author found now.
	"""
	stories = _data()
	new_items: list[NewsItem] = []
	now_str = datetime.datetime.now().isoformat()
	changed = False
	with _lock:
		for item in items:
			entry = stories.get(item.guid)
			if entry is None:
				stories[item.guid] = {
					"title": item.title,
					"source": item.source,
					"url": item.url,
					"category": item.category,
					"summary": item.summary,
					"published_at": item.published_at,
					"is_breaking": item.is_breaking,
					"author": item.author,
					"seen": mark_seen or item.source in (quiet_sources or ()),
					"cached_at": now_str,
				}
				new_items.append(item)
				changed = True
				continue
			if item.source in refresh_sources:
				for field_name, value in (
					("title", item.title),
					("published_at", item.published_at),
					("summary", item.summary),
					("author", item.author),
				):
					if value and entry.get(field_name) != value:
						entry[field_name] = value
						changed = True
			if item.author and not entry.get("author"):
				# Stories saved before the author was read get it the next time they are found.
				entry["author"] = item.author
				changed = True
			categories = [c.strip() for c in entry.get("category", "").split(",") if c.strip()]
			if item.category not in categories:
				categories.append(item.category)
				entry["category"] = ", ".join(categories)
				changed = True
	if changed:
		_schedule_save()
	return new_items


def get_news_items(
	enabled_sources: list[str], enabled_categories: list[str], filter_unread_only: bool = False
) -> list[NewsItem]:
	"""The cached stories of the given sources and categories, newest first."""
	items: list[NewsItem] = []
	for guid, val in _data().items():
		source = val.get("source", "")
		if source not in enabled_sources:
			continue
		seen = val.get("seen", False)
		if filter_unread_only and seen:
			continue
		categories = [c.strip() for c in val.get("category", "").split(",") if c.strip()]
		matched_category = next((c for c in categories if c in enabled_categories), None)
		if not matched_category:
			continue
		title = val.get("title", "")
		items.append(
			NewsItem(
				guid=guid,
				title=title,
				source=source,
				url=val.get("url", ""),
				category=matched_category,
				summary=val.get("summary"),
				published_at=val.get("published_at"),
				# Worked out again, so stories saved by older versions follow today's rule.
				is_breaking=is_breaking(title),
				seen=seen,
				found_at=val.get("cached_at"),
				author=val.get("author"),
			)
		)
	# Newest first, by publication time, or by when the add-on found the story if the site gives no time.
	oldest = datetime.datetime.min.replace(tzinfo=datetime.UTC)
	items.sort(key=lambda item: story_time(item) or oldest, reverse=True)
	return items


def _published_iso(val: dict) -> str | None:
	"""The publication time as ISO 8601.

	Versions before 1.1.0 stored the site's text, such as "10 jam lalu" or "15/11/2026";
	it is read again, counting relative times from when the story was saved.
	That text was sometimes a sentence from the story ("... 29 Desember 2026"), so a time after the
	story was saved is not a publication time and is dropped.
	"""
	published = val.get("published_at")
	if not published or parse_iso(published):
		return published or None
	cachedAt = parse_iso(val.get("cached_at"))
	parsed = parse_date(published, cachedAt)
	if parsed is None or (cachedAt is not None and parsed > cachedAt + datetime.timedelta(hours=1)):
		return None
	return parsed.isoformat(timespec="seconds")


def mark_as_read(guid: str) -> None:
	entry = _data().get(guid)
	if entry is not None and not entry.get("seen", False):
		with _lock:
			entry["seen"] = True
		_schedule_save()


def mark_all_as_read() -> None:
	changed = False
	with _lock:
		for val in _data().values():
			if not val.get("seen", False):
				val["seen"] = True
				changed = True
	if changed:
		_schedule_save()


def get_unread_count() -> int:
	return sum(1 for val in _data().values() if not val.get("seen", False))


def prune_cache(retention_days: int, keep_sources: tuple[str, ...] = ()) -> None:
	"""Remove stories found more than retention_days ago, with their saved article texts.

	Stories of keep_sources (InfiArtt, which lists its whole archive) are never removed.
	"""
	cutoff = datetime.datetime.now().astimezone() - datetime.timedelta(days=retention_days)
	stories = _data()
	to_delete = []
	for guid, val in stories.items():
		if val.get("source") in keep_sources:
			continue
		cached_at = parse_iso(val.get("cached_at"))
		if cached_at is not None and cached_at < cutoff:
			to_delete.append(guid)
	if not to_delete:
		return
	with _lock:
		for guid in to_delete:
			del stories[guid]
	for guid in to_delete:
		for extension in ("json", "txt"):
			with contextlib.suppress(FileNotFoundError):
				os.remove(_article_path(guid, extension))
	_schedule_save()
	logHandler.log.info(f"NusaNews: Removed {len(to_delete)} stories older than {retention_days} days.")


def get_article(guid: str) -> Article | None:
	"""The saved article, or None when it was never downloaded."""
	try:
		with open(_article_path(guid), encoding="utf-8") as f:
			saved = json.load(f)
		return Article(
			blocks=parse_blocks(saved.get("html", ""), "", whole_document=True),
			language=saved.get("language") or "id",
			locked_note=saved.get("locked_note"),
			summary=saved.get("summary"),
		)
	except FileNotFoundError:
		pass
	except Exception:
		logHandler.log.exception("NusaNews: Reading a saved article failed.")
		return None
	try:
		with open(_article_path(guid, "txt"), encoding="utf-8") as f:
			return Article(blocks=blocks_from_text(f.read()))
	except FileNotFoundError:
		return None
	except Exception:
		logHandler.log.exception("NusaNews: Reading a saved article failed.")
		return None


def _write_article(guid: str, article: Article) -> None:
	path = _article_path(guid)
	saved = {
		"html": article.html,
		"language": article.language,
		"locked_note": article.locked_note,
		"summary": article.summary,
	}
	try:
		os.makedirs(os.path.dirname(path), exist_ok=True)
		with open(path, "w", encoding="utf-8") as f:
			json.dump(saved, f, ensure_ascii=False)
		with contextlib.suppress(FileNotFoundError):
			os.remove(_article_path(guid, "txt"))
	except Exception:
		logHandler.log.exception("NusaNews: Saving an article failed.")


def update_article(guid: str, article: Article) -> None:
	"""Save a downloaded article, for reading it again without the network."""
	if guid in _data():
		_write_article(guid, article)


def clear_cache() -> None:
	"""Remove every story and saved article."""
	with _lock:
		_data().clear()
	shutil.rmtree(os.path.join(get_cache_dir(), ARTICLES_DIR), ignore_errors=True)
	flush()
