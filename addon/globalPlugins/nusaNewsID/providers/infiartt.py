# infiartt.py
#
# InfiArtt (infiartt.com), the organization behind this add-on: its articles and its knowledge base.
# This source is always on and cannot be turned off.
# Unlike the news sites, InfiArtt has a JSON API (the one InfiApp uses), so this provider reads it
# instead of pages: /api/v1/posts for articles and /api/v1/kb for the knowledge base. The knowledge base
# list has no dates or authors, so each guide's details are read once, the first time it is listed.
# The news sites' rules on age do not apply: every article and guide is listed, however old, and the
# cache keeps them (prune_cache leaves the always-on sources alone).

import html
import json
import re
from datetime import datetime

from ..models import NewsItem
from .articleContent import Article, parse_blocks
from .baseProvider import BaseProvider, CategorySource
from .textUtils import clean_title, is_breaking, parse_date

SITE = "https://infiartt.com"
ARTICLES = "Artikel InfiArtt"
KNOWLEDGE_BASE = "Pusat Pengetahuan"
# A limit on article pages per check, in case the API keeps saying there are more; it gives 10 per page.
MAX_PAGES = 100


class InfiArttProvider(BaseProvider):
	source_name = "InfiArtt"
	base_url = SITE
	article_pattern = r"infiartt\.com/"
	# Read through the API, so these only name the categories this source offers.
	categories = {
		ARTICLES: CategorySource(rss=f"{SITE}/api/v1/posts"),
		KNOWLEDGE_BASE: CategorySource(rss=f"{SITE}/api/v1/kb"),
	}

	def __init__(self) -> None:
		# Article addresses already listed by this provider since NVDA started. The first check reads
		# every page; later checks stop at the first page with an article seen before.
		self._known_articles: set[str] = set()
		# Details of each knowledge base guide, by id: address, author and time, read once per NVDA start.
		self._guides: dict[int, tuple[str, str | None, datetime | None]] = {}

	def fetch_news(self, category: str, bypass_ssl: bool = False, max_age_days: int = 7) -> list[NewsItem]:
		"""Every article or guide; max_age_days is ignored for InfiArtt."""
		if category == ARTICLES:
			return self._articles(bypass_ssl)
		if category == KNOWLEDGE_BASE:
			return self._knowledge_base(bypass_ssl)
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
		self,
		title: str,
		url: str,
		category: str,
		published: datetime | None,
		summary: str | None,
		author: str | None = None,
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
			author=author or None,
		)

	def _articles(self, bypass_ssl: bool) -> list[NewsItem]:
		items: list[NewsItem] = []
		for page in range(1, MAX_PAGES + 1):
			if self._stopped():
				break
			data = self._json(f"{SITE}/api/v1/posts?page={page}", bypass_ssl)
			if not data:
				break
			reached_known = False
			for post in data.get("items", []):
				if not (post.get("title") and post.get("url")):
					continue
				if post["url"] in self._known_articles:
					reached_known = True
				published = parse_date(post.get("published_at"))
				items.append(
					self._item(
						post["title"],
						post["url"],
						ARTICLES,
						published,
						post.get("excerpt"),
						_author_name(post.get("author")),
					)
				)
			# The API lists the newest first: after a page with a known article, the rest are known too.
			if reached_known or not data.get("has_more"):
				break
		if not self._stopped():
			self._known_articles.update(item.url for item in items)
		return items

	def _knowledge_base(self, bypass_ssl: bool) -> list[NewsItem]:
		tree = self._json(f"{SITE}/api/v1/kb", bypass_ssl)
		if not tree:
			return []
		items: list[NewsItem] = []
		for node in _leaves(tree.get("items", [])):
			if self._stopped():
				break
			details = self._guides.get(node["id"])
			if details is None:
				data = self._json(f"{SITE}/api/v1/kb/{node['id']}", bypass_ssl) or {}
				details = (
					str(data.get("url") or f"{SITE}/kb/{node['id']}"),
					_author_name(data.get("author")),
					parse_date(data.get("updated_at")),
				)
				if data:
					self._guides[node["id"]] = details
			url, author, updated = details
			items.append(self._item(node["title"], url, KNOWLEDGE_BASE, updated, None, author))
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


def _author_name(author) -> str | None:
	"""The name to show for an author: the API gives a display name and username for articles, a username
	for guides."""
	if isinstance(author, dict):
		return str(author.get("display_name") or author.get("username") or "") or None
	return str(author) if author else None


def _leaves(nodes: list[dict]) -> list[dict]:
	"""Every guide in the knowledge base tree, without the folders."""
	found: list[dict] = []
	for node in nodes:
		if node.get("is_folder"):
			found.extend(_leaves(node.get("children") or []))
		elif node.get("id") and node.get("title"):
			found.append({"id": int(node["id"]), "title": str(node["title"])})
	return found
