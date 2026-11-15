"""Check every provider and category against the real news sites, outside NVDA.

Run from the repository root:

    python tools/checkProviders.py            # every source
    python tools/checkProviders.py Kompas     # one source

For each source and category it prints whether the feed or the page was used, how many stories were found,
how many have a date, the newest story, and warnings for titles that still look unclean.
The exit code is 1 when a category that should have stories has none, so it can run on a schedule.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "addon" / "globalPlugins")]
sys.dont_write_bytecode = True

import nvda_mocks  # noqa: E402, F401
from nusaNewsID.providers import baseProvider, parsers  # noqa: E402
from nusaNewsID.providers.sourceManager import SourceManager  # noqa: E402

# Titles that still carry a time, a kanal name or a label from the page.
SUSPICIOUS = re.compile(
	r"^\d{1,2}[:.]\d{2}|^detik[A-Z]|^Headline\b|\s(?:Nasional|Regional|NEWS|Tekno|Hiburan)$|\s-\s,\s",
)


def main() -> int:
	only = set(sys.argv[1:])
	manager = SourceManager()
	failures = 0
	for name, provider in manager.providers.items():
		if only and name not in only:
			continue
		for category, source in provider.categories.items():
			items = provider.fetch_news(category)
			via = "RSS" if source.rss and _fromRss(provider, category) else "HTML"
			dated = sum(1 for item in items if item.published_at)
			newest = max((item.published_at for item in items if item.published_at), default="-")
			sample = items[0].title[:70] if items else "-"
			print(f"{name:14} {category:13} {via:4} {len(items):3} stories, {dated:3} dated, newest {newest}")
			print(f"{'':28} {sample}")
			for item in items:
				if SUSPICIOUS.search(item.title):
					print(f"{'':28} WARNING title: {item.title[:90]}")
			if not items and category != "Disabilitas":
				failures += 1
				print(f"{'':28} ERROR no stories")
	return 1 if failures else 0


def _fromRss(provider: baseProvider.BaseProvider, category: str) -> bool:
	"""Whether the stories came from the feed: fetch the feed alone and see if it gives any."""
	source = provider.categories[category]
	data = provider._request_http(source.rss)
	if not data:
		return False
	return bool(provider._accept(parsers.parse_rss(data), category, source, _oldest()))


def _oldest():
	from datetime import timedelta

	from nusaNewsID.providers.textUtils import now

	return now() - timedelta(days=7)


if __name__ == "__main__":
	sys.exit(main())
