# infiartt.py
#
# InfiArtt (infiartt.com), the organization behind this add-on: its articles and its knowledge base.
# This source is always on and cannot be turned off.
# Unlike the news sites, InfiArtt has a JSON API (the one InfiApp uses), so this provider reads it
# instead of pages: /api/v1/posts for articles and /api/v1/kb for the knowledge base. The knowledge base
# list has no dates, so they come from the sitemap's lastmod.

import html
import json
import re
from datetime import datetime, timedelta

from ..models import NewsItem
from .articleContent import Article, parse_blocks
from .baseProvider import BaseProvider, CategorySource
from .textUtils import clean_title, is_breaking, now, parse_date

SITE = "https://infiartt.com"
ARTICLES = "Artikel InfiArtt"
KNOWLEDGE_BASE = "Pusat Pengetahuan"
# Article pages to read per check; the API gives 10 articles per page.
MAX_PAGES = 3


class InfiArttProvider(BaseProvider):
	source_name = "InfiArtt"
	base_url = SITE
	article_pattern = r"infiartt\.com/"
	# Read through the API, so these only name the categories this source offers.
	categories = {
		ARTICLES: CategorySource(rss=f"{SITE}/api/v1/posts"),
		KNOWLEDGE_BASE: CategorySource(rss=f"{SITE}/api/v1/kb"),
	}

	def fetch_news(self, category: str, bypass_ssl: bool = False, max_age_days: int = 7) -> list[NewsItem]:
		oldest = now() - timedelta(days=max_age_days)
		if category == ARTICLES:
			return self._articles(bypass_ssl, oldest)
		if category == KNOWLEDGE_BASE:
			return self._knowledge_base(bypass_ssl, oldest)
		return []

	def _json(self, url: str, bypass_ssl: bool) -> dict | None:
		data = self._request_http(url, bypass_ssl)
		if not data:
			return None
		try:
			payload = json.loads(data)
		except ValueError:
			return None
		if not isinstance(payload, dict) or not payload.get("ok"):
			return None
		return payload.get("data")

	def _item(
		self, title: str, url: str, category: str, published: datetime | None, summary: str | None
	) -> NewsItem:
		title = clean_title(title)
		return NewsItem(
			title=title,
			source=self.source_name,
			url=url,
			guid=url,
			category=category,
			summary=summary or None,
			published_at=published.isoformat(timespec="seconds") if published else None,
			is_breaking=is_breaking(title),
		)

	def _articles(self, bypass_ssl: bool, oldest: datetime) -> list[NewsItem]:
		items: list[NewsItem] = []
		for page in range(1, MAX_PAGES + 1):
			if self._stopped():
				break
			data = self._json(f"{SITE}/api/v1/posts?page={page}", bypass_ssl)
			if not data:
				break
			reached_old = False
			for post in data.get("items", []):
				published = parse_date(post.get("published_at"))
				if published is not None and published < oldest:
					reached_old = True
					continue
				if post.get("title") and post.get("url"):
					items.append(
						self._item(post["title"], post["url"], ARTICLES, published, post.get("excerpt"))
					)
			# The API lists the newest first, so an old article means the rest are older still.
			if reached_old or not data.get("has_more"):
				break
		return items

	def _knowledge_base(self, bypass_ssl: bool, oldest: datetime) -> list[NewsItem]:
		tree = self._json(f"{SITE}/api/v1/kb", bypass_ssl)
		if not tree:
			return []
		sitemap = self._request_http(f"{SITE}/sitemap.xml", bypass_ssl) or b""
		pages: dict[int, tuple[str, datetime | None]] = {}
		for entry in re.findall(rb"<url>(.*?)</url>", sitemap, re.S):
			location = re.search(rb"<loc>\s*(https?://[^<\s]+/kb/(\d+)/[^<\s]*)\s*</loc>", entry)
			if not location:
				continue
			modified = re.search(rb"<lastmod>\s*([^<\s]+)\s*</lastmod>", entry)
			date = parse_date(modified.group(1).decode()) if modified else None
			pages[int(location.group(2))] = (location.group(1).decode(), date)
		items: list[NewsItem] = []
		for node in _leaves(tree.get("items", [])):
			url, updated = pages.get(node["id"], (f"{SITE}/kb/{node['id']}", None))
			# Without a date it cannot be told from an old guide, so it waits until the sitemap lists it.
			if updated is None or updated < oldest:
				continue
			items.append(self._item(node["title"], url, KNOWLEDGE_BASE, updated, None))
		return items

	def fetch_article(self, url: str, bypass_ssl: bool = False) -> Article | None:
		"""The article or guide from the API, with its own structure and language."""
		match = re.search(r"/kb/(\d+)", url)
		if match:
			data = self._json(f"{SITE}/api/v1/kb/{match.group(1)}", bypass_ssl)
		else:
			slug = url.rstrip("/").rsplit("/", 1)[-1]
			data = self._json(f"{SITE}/api/v1/posts/{slug}", bypass_ssl)
		if not data:
			return None
		article = Article(
			blocks=parse_blocks(data.get("content_html") or "", SITE, whole_document=True),
			language=str(data.get("language") or "id")[:2].lower(),
			summary=data.get("excerpt"),
		)
		if data.get("locked"):
			# Members-only articles: the API gives no text, so the reader shows the summary and says why.
			article.blocks = parse_blocks(
				f"<p>{html.escape(data.get('excerpt') or '', quote=False)}</p>", SITE, whole_document=True
			)
			article.locked_note = str(data.get("requirement") or "") or "members"
		return article if article.blocks or article.locked_note else None


def _leaves(nodes: list[dict]) -> list[dict]:
	"""Every guide in the knowledge base tree, without the folders."""
	found: list[dict] = []
	for node in nodes:
		if node.get("is_folder"):
			found.extend(_leaves(node.get("children") or []))
		elif node.get("id") and node.get("title"):
			found.append({"id": int(node["id"]), "title": str(node["title"])})
	return found
