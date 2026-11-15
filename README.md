# NusaNewsID

An NVDA add-on that follows Indonesian news from Antara, Kompas, Detik, Republika, Liputan6, Merdeka, CNN Indonesia and WinPoin, along with the articles and knowledge base of InfiArtt. It checks for new stories in the background, announces them with NVDA, stays quiet during the hours you choose, and opens whole articles in a window made for screen readers and low vision, so you do not need a browser.

The user guide is in `addon/doc/en/readme.md` (English) and `addon/doc/id/readme.md` (Indonesian). Once the add-on is installed, the same guide opens from NVDA's Add-on Store.

## Features

- Press NVDA+Shift+/ to open the news list. Filter it by source, category or unread stories. A box below the list shows the selected story's whole title, details and summary.
- The reader shows the article as a page that NVDA reads in browse mode, with its headings, lists, quotes and links. Ads, "baca juga" boxes, photo credits and editors' codes are left out, photos are described once, and articles split over several pages are read whole.
- For low vision, Control+plus, Control+minus and Control+0 change the text size from 100 to 400 percent. The page follows the Windows colors, including contrast themes.
- New versions are offered from this repository's GitHub releases. The update window shows what changed before anything is installed, and NVDA's own installer installs the add-on.

## NVDA versions

- Minimum version: NVDA 2026.1.
- Last tested: NVDA 2026.3.1.

## Building the add-on

1. Install Python 3.13 and gettext.
2. Run `pip install --group build --group test ruff`.
3. Run `scons`. It writes `nusaNewsID-<version>.nvda-addon`.

Run the tests with `python -m pytest`, and check the code style with `ruff check .` and `ruff format --check .`.

To check every source against the real news sites, run `python tools/checkProviders.py` for the story lists and `python tools/checkArticles.py` for the articles.

## Releases and updates

CI publishes a GitHub release when `main` gets a new `addon_version` in `buildVars.py` and a dated section for it in `CHANGELOG.md`, such as `## [1.2.0] - 2026-12-01`. A section marked "belum dirilis" (not released yet) is built but not published.

The release notes are that `CHANGELOG.md` section. The add-on shows them in its update window, so write each version's changes there. The add-on checks for new versions once a day, a while after NVDA starts. You can turn this off, or check right away, in the NusaNewsID settings. Only a `.nvda-addon` file attached to a release of this repository, matching GitHub's SHA-256 checksum and the release's version, is installed.

## Support

NusaNewsID is free. If it helps you, you can support its developer with a voluntary donation through GoPay to 085128011831 (Rexya Muhamad Rizki). The same details are in the add-on's settings and news list.

## Changelog

The full history, in Indonesian, is in `CHANGELOG.md`.

## License

GNU General Public License version 2 or later. See `LICENSE`.
