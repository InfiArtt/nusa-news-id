# cache.py
#
# The JSON cache of news stories, keyed by guid. Runs on the main thread only.

import contextlib
import datetime
import json
import os

import globalVars
import logHandler

from .formatting import parse_iso, story_time
from .models import NewsItem
from .providers.textUtils import is_breaking, parse_date

CACHE_FILE = "nusaNewsCache.json"


def get_cache_dir() -> str:
	"""Determines the absolute directory path to the NusaNews cache directory."""
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
	"""Determines the absolute file path to the JSON cache file within NusaNews cache directory."""
	cache_dir = get_cache_dir()
	os.makedirs(cache_dir, exist_ok=True)
	return os.path.join(cache_dir, CACHE_FILE)


def init_db():
	"""Ensures the cache file is initialized and handles migration from old root location."""
	path = get_cache_path()
	try:
		old_path = os.path.join(os.path.dirname(get_cache_dir()), CACHE_FILE)
		if os.path.exists(old_path) and not os.path.exists(path):
			import shutil

			logHandler.log.info("NusaNews: Migrating old cache file to new directory.")
			shutil.copy2(old_path, path)
			os.remove(old_path)
	except Exception as e:
		logHandler.log.error(f"NusaNews: Failed to migrate old cache file: {e}")

	if not os.path.exists(path):
		_write_cache({})


def _read_cache() -> dict:
	"""Safely reads the dictionary from the JSON cache file."""
	path = get_cache_path()
	if not os.path.exists(path):
		return {}
	try:
		with open(path, encoding="utf-8") as f:
			return json.load(f)
	except Exception as e:
		logHandler.log.error(f"NusaNews: Failed to read JSON cache: {e}")
		return {}


def _write_cache(data: dict):
	"""Writes the dictionary to the JSON cache file using a safe atomic replace pattern."""
	path = get_cache_path()
	tmp_path = path + ".tmp"
	try:
		# Write to temporary file first
		with open(tmp_path, "w", encoding="utf-8") as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
		# Atomically replace active file (safe against partial write corruption)
		os.replace(tmp_path, path)
	except Exception as e:
		logHandler.log.error(f"NusaNews: Failed to write JSON cache: {e}")
		if os.path.exists(tmp_path):
			with contextlib.suppress(Exception):
				os.remove(tmp_path)


def save_news_items(items: list[NewsItem]) -> list[NewsItem]:
	"""
	Saves a batch of NewsItems to the JSON cache file.
	Returns a list of items that were successfully added (indicating they are new, not duplicates).
	"""
	cache_data = _read_cache()
	new_items = []
	now_str = datetime.datetime.now().isoformat()
	cache_updated = False

	for item in items:
		if item.guid not in cache_data:
			cache_data[item.guid] = {
				"title": item.title,
				"source": item.source,
				"url": item.url,
				"category": item.category,
				"summary": item.summary,
				"content": item.content,
				"published_at": item.published_at,
				"is_breaking": item.is_breaking,
				"seen": False,
				"cached_at": now_str,
			}
			new_items.append(item)
			cache_updated = True
		else:
			# Check if this article is now being fetched under a new category
			existing_entry = cache_data[item.guid]
			existing_cat_str = existing_entry.get("category", "")
			existing_categories = [c.strip() for c in existing_cat_str.split(",") if c.strip()]
			if item.category not in existing_categories:
				existing_categories.append(item.category)
				existing_entry["category"] = ", ".join(existing_categories)
				cache_updated = True

	if cache_updated:
		_write_cache(cache_data)
	return new_items


def get_news_items(
	enabled_sources: list[str], enabled_categories: list[str], filter_unread_only: bool = False
) -> list[NewsItem]:
	"""Retrieves cached news items filtered by active settings from the main thread."""
	cache_data = _read_cache()
	items = []

	for guid, val in cache_data.items():
		source = val.get("source", "")
		category_str = val.get("category", "")
		seen = val.get("seen", False)

		if source not in enabled_sources:
			continue

		# Check if any of the item's categories match the active filters
		item_categories = [c.strip() for c in category_str.split(",") if c.strip()]
		matched_category = None
		for cat in item_categories:
			if cat in enabled_categories:
				matched_category = cat
				break

		if not matched_category:
			continue

		if filter_unread_only and seen:
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
				content=val.get("content"),
				published_at=_published_iso(val),
				# Worked out again, so stories saved by older versions follow today's rule.
				is_breaking=is_breaking(title),
				seen=seen,
				found_at=val.get("cached_at"),
			)
		)

	# Newest first, by publication time, or by when the add-on found the story if the site gives no time.
	oldest = datetime.datetime.min.replace(tzinfo=datetime.UTC)
	items.sort(key=lambda item: story_time(item) or oldest, reverse=True)
	return items[:500]


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


def mark_as_read(guid: str):
	"""Marks a single article as read (seen = True)."""
	cache_data = _read_cache()
	if guid in cache_data:
		cache_data[guid]["seen"] = True
		_write_cache(cache_data)


def mark_all_as_read():
	"""Marks all currently cached articles as read."""
	cache_data = _read_cache()
	updated = False
	for _guid, val in cache_data.items():
		if not val.get("seen", False):
			val["seen"] = True
			updated = True
	if updated:
		_write_cache(cache_data)


def get_unread_count() -> int:
	"""Returns the total number of unread articles in the cache."""
	cache_data = _read_cache()
	count = 0
	for val in cache_data.values():
		if not val.get("seen", False):
			count += 1
	return count


def prune_cache(retention_days: int):
	"""Deletes articles cached beyond the user's expiration policy."""
	cache_data = _read_cache()
	now = datetime.datetime.now()
	cutoff = now - datetime.timedelta(days=retention_days)

	to_delete = []
	for guid, val in cache_data.items():
		cached_at_str = val.get("cached_at")
		if cached_at_str:
			try:
				cached_at = datetime.datetime.fromisoformat(cached_at_str)
				if cached_at < cutoff:
					to_delete.append(guid)
			except Exception:
				pass

	if to_delete:
		for guid in to_delete:
			del cache_data[guid]
		_write_cache(cache_data)
		logHandler.log.info(
			f"NusaNews: Pruned JSON cache, removed {len(to_delete)} items older than {retention_days} days."
		)


def update_article_content(guid: str, content: str):
	"""Updates the content of an existing cached news item."""
	cache_data = _read_cache()
	if guid in cache_data:
		cache_data[guid]["content"] = content
		_write_cache(cache_data)


def clear_cache():
	"""Clears all cached news articles completely."""
	_write_cache({})
