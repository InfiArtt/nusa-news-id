# Instructions for AI coding agents

This file is read by AI coding agents (Claude Code, Codex, GitHub Copilot, Cursor, Gemini and others) working in this repository. People should start with the README and the [InfiArtt contributing guide](https://github.com/InfiArtt/.github/blob/main/CONTRIBUTING.md).

## About this project

NusaNewsID is an NVDA add-on (Python 3.13, wxPython, NVDA's add-on API) for blind and low-vision users in Indonesia. A background thread checks Indonesian news sites (Antara, Kompas, Detik, Republika, Liputan6, Merdeka, CNN Indonesia, WinPoin) through their RSS feeds where they are kept up to date and their category pages otherwise, keeps the stories in a JSON cache, announces new ones with `ui.message`, and shows them in an accessible reader dialog.

## Commands

- Tests: `python -m pytest` (Python 3.13). The tests replace NVDA and wx with stubs from `tests/nvda_mocks.py`.
- Lint and format: `ruff check .` and `ruff format .` (tabs, line length 110, settings in `pyproject.toml`).
- Build: `scons` writes `nusaNewsID-<version>.nvda-addon`; `scons pot` writes the translation template. Needs the `build` dependency group from `pyproject.toml` and gettext.
- Live check of every provider and category against the real sites: `python tools/checkProviders.py` (or with a source name). It prints feed or page, story counts, dates and suspicious titles, and exits 1 when a category is empty.

Run the tests before committing, and add a test when you fix a bug.

## Rules

- **Accessibility first.** InfiArtt is led by people with disabilities. Every control needs a label that screen readers announce, everything must work with the keyboard alone, and messages should say clearly what happened and what to do next.
- **Never commit secrets**: passwords, API keys, tokens, `.env` files. Push protection blocks known kinds of secrets, but don't rely on it.
- **Don't push to `main`.** Work on a branch and open a pull request.
- **Ask first** before anything that publishes or can't easily be undone: merging, releases, tags, deployments, package uploads, force-pushing, deleting branches or repositories.
- **Never post in other people's repositories** (issues, comments, pull requests, submissions) on the team's behalf. Some communities forbid AI tools from interacting with them; NV Access, for example, bans them from the NVDA Add-on Store repository. Prepare the facts and leave the posting to a person.
- **Be transparent about AI involvement.** Keep `Co-Authored-By` trailers in commits, and don't disguise AI-written text as written by a person.
- Keep changes focused, and match the existing code style, naming and comment density.
- Write code, comments and commit messages in English, with Conventional Commits prefixes (`feat:`, `fix:`, `docs:`, `test:`, `ci:`, `refactor:`). Talk to the team in the language they use with you, often Indonesian.

## Reading rules (WCAG 2.2)

Stories must be easy to read with a screen reader and with low vision. Every change to how stories are shown follows these rules; `tests/test_reader.py` checks most of them.

- Structure (1.3.1): the reader page keeps the article's paragraphs, headings, lists, quotes and links. The story title is the only h1, the article's headings start at h2, and levels never skip.
- Language (3.1.1, 3.1.2): the page has NVDA's language, the article its own (`lang`), so NVDA can switch voices.
- Colors (1.4.3, 1.4.11): only Windows system colors (Window, WindowText, Highlight, GrayText, ButtonFace, ButtonText); never fixed colors, so contrast themes work.
- Size and spacing (1.4.4, 1.4.10, 1.4.12, 1.4.8): sizes in em or rem, never px; line height 1.5, space between paragraphs, lines at most 70ch and wrapping, text left aligned. Text size goes from 100 to 400 percent (Control+plus, Control+minus, Control+0, and the setting).
- Images (1.1.1): only with a text alternative; images without one are left out.
- Keyboard and focus (2.1.1, 2.4.7, 2.4.3): every action is a real button with a visible focus outline and the dialog's shortcut key; Escape closes. Lists and dialogs keep the focus order checked with `nvda_audit_focus_order`.
- Names and status (4.1.2, 4.1.3, 3.3.1): every control has a label; results are announced with `ui.message`; errors say what is wrong and how to fix it. An empty list shows a line explaining why, never nothing.
- Article content is rebuilt from an allow list in `providers/articleContent.py`; the site's own markup, styles and scripts never reach the page. Boilerplate (ads, "baca juga", addresses, copyright lines) is removed by `is_boilerplate`.
- The reader uses Internet Explorer's engine, like NVDA's own HTML messages, so CSS and script stay within IE 11. Without a web engine it falls back to a plain text box with the same text.

## Project-specific notes

- The add-on id `nusaNewsID` (in `buildVars.py`), the config section name `nusaNewsID` and its keys (`refresh_interval`, `enabled_sources`, ...) and the cache file `nusaNewsCache.json` with its field names must not change: installed copies would lose their settings and cache.
- User-facing strings are English in the code, wrapped in `_()` or `ngettext()` with a `# Translators:` comment above, in modules that call `addonHandler.initTranslation()`. Use `{name}` placeholders with `.format()`, never f-strings, inside translatable text. The Indonesian translation is `addon/locale/id/LC_MESSAGES/nvda.po`: after changing strings, run `scons pot`, then `msgmerge --update --no-location addon/locale/id/LC_MESSAGES/nvda.po nusaNewsID.pot`, translate the new entries, and check with `msgcmp`. `tests/test_translations.py` checks that every message is translated, keeps its placeholders and shortcut key, and that shortcut keys differ within each window in both languages. Most formatting tests read the Indonesian translation (see `tests/poFile.py`).
- Category names are stored in Indonesian (`CATEGORIES` in `providers/sourceManager.py`) and shown through `formatting.category_label`.
- Every change for the version being worked on goes into two places: `addon_changelog` in `buildVars.py` (English, short, shown in the Add-on Store) and the version's section in `CHANGELOG.md` (Indonesian, detailed). Replace `addon_changelog` when starting a new version.
- Releases: CI (`.github/workflows/build.yml`) publishes a GitHub Release when `main` gets an `addon_version` with no tag yet and a dated `## [X.Y.Z] - YYYY-MM-DD` section in `CHANGELOG.md`. A section marked "belum dirilis" is built but not published. Keep `version` in `pyproject.toml` equal to `addon_version`.
- Generated files are not committed: `addon/manifest.ini`, `addon/locale/*/manifest.ini`, `addon/doc/*/readme.html`, `addon/doc/style.css`, `*.mo` and `*.pot` all come from `scons`.
- Threading: network requests run only in the background `MonitorThread` or the article download thread. Everything that touches wx, `config.conf`, `ui` or the cache runs on the main thread (`wx.CallAfter`). Settings are copied on the main thread and handed to the thread.
- Background work must stop quickly: check the stop event between requests and wait on it instead of `time.sleep`.
- InfiArtt (`providers/infiartt.py`) is the exception to "data only": it is the organization's own site, always on (`ALWAYS_ON_SOURCES`, not in the settings list), and read through its JSON API (`/api/v1/posts`, `/api/v1/kb`, used by InfiApp; code in the private repository InfiArtt/infiartt-website). Knowledge base dates come from `sitemap.xml`. The age rules do not apply to it: it lists every article and guide, and `prune_cache(keep_sources=ALWAYS_ON_SOURCES)` keeps them. The first check reads every page of `/api/v1/posts`; later checks stop at the first page with a known article. Its articles open from the API, members-only ones show their summary.
- A source with no saved story yet (just turned on, or InfiArtt's archive) is saved quietly as read the first time (`quiet_sources` in `on_check_finished`).
- Providers are data only (`providers/<site>.py`): `CategorySource(rss=..., html=..., sections=..., curated=...)` per category, `article_pattern`, optional `deny_pattern` and `url_date_pattern`. All behaviour lives in `providers/baseProvider.py` (rules), `providers/parsers.py` (RSS and HTML) and `providers/textUtils.py` (dates, titles, keywords), the same for every site. Do not add site-specific code paths; add data or a general rule instead.
- Sites change their HTML and feeds often. When a provider breaks, run `tools/checkProviders.py`, check the real page or feed first and fix its data; never guess. A category the site no longer updates is removed rather than kept with old stories.
- NVDA's Python has certifi; `networkUtils` uses it together with the Windows certificate store, because some sites (Antara) use roots that Windows only downloads on demand.
- Before using an NVDA API, check that it exists in the NVDA version you target (the NVDA MCP tool `nvda_lookup_api` does this against the running NVDA). Minimum NVDA is 2026.1.
