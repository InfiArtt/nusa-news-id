"""Download a few articles of every source and show what the reader would get, outside NVDA.

Run from the repository root:

    python tools/checkArticles.py            # every source
    python tools/checkArticles.py Liputan6   # one source

For each article it prints the number of paragraphs, photos, videos and social posts, the author found in
the text, and lines that still look like leftovers: short lines, and words such as "Baca", "Perbesar",
"Foto:" or "Video" near the start of a paragraph. Read those lines on the real page before changing a rule.
The exit code is 1 when an article gives no text at all.
"""

import collections
import concurrent.futures
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "addon" / "globalPlugins")]
sys.dont_write_bytecode = True

import nvda_mocks  # noqa: E402, F401
from nusaNewsID.providers.sourceManager import ALWAYS_ON_SOURCES, SourceManager, provider_for  # noqa: E402

PER_CATEGORY = 2
CATEGORIES_PER_SOURCE = 3
SUSPECT = re.compile(
	r"perbesar|lihat foto|baca(?: juga)?\s*:|simak|tonton|video\s*:|advertis|iklan|scroll|ikuti|klik|"
	r"foto\s*:|sumber\s*:|editor\s*:|penulis\s*:|\(foto|dok\.|getty|shutterstock|selanjutnya|"
	r"berita terkait|pilihan redaksi|bagikan|copyright|©|placeholder",
	re.IGNORECASE,
)


def _articles(only: set[str]) -> list[tuple[str, str, str, str]]:
	manager = SourceManager()
	jobs = []
	for name, provider in manager.providers.items():
		if name in ALWAYS_ON_SOURCES or (only and name not in only):
			continue
		for category in list(provider.categories)[:CATEGORIES_PER_SOURCE]:
			for item in provider.fetch_news(category, max_age_days=30)[:PER_CATEGORY]:
				jobs.append((name, category, item.title, item.url))
	return jobs


def _download(job):
	name, _category, _title, url = job
	try:
		return job, provider_for(name).fetch_article(url), None
	except Exception as error:
		return job, None, error


def main() -> int:
	jobs = _articles(set(sys.argv[1:]))
	empty = 0
	with concurrent.futures.ThreadPoolExecutor(8) as pool:
		for (name, category, title, url), article, error in pool.map(_download, jobs):
			print(f"\n{name}, {category}: {title}\n  {url}")
			if not article or not article.blocks:
				empty += 1
				print(f"  NO TEXT{f' ({error})' if error else ''}")
				continue
			kinds = collections.Counter(block.kind for block in article.blocks)
			print(
				f"  {sum(n for kind, n in kinds.items() if kind not in ('image', 'video', 'social'))} parts, "
				f"{kinds['image']} photos, {kinds['video']} videos, {kinds['social']} social posts, "
				f"author {article.author or 'none'}"
			)
			for block in article.blocks:
				text = block.text.strip()
				if block.kind in ("image", "social"):
					print(f"  {block.kind}: {text[:100]} {block.extra}".rstrip())
				elif block.kind != "video" and (len(text) < 40 or SUSPECT.search(text[:120])):
					print(f"  check: {text[:100]!r}")
	print(f"\n{len(jobs)} articles, {empty} without text.")
	return 1 if empty else 0


if __name__ == "__main__":
	sys.exit(main())
