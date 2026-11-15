# Build customizations
# Change this file instead of sconstruct or manifest files, whenever possible.

from site_scons.site_tools.NVDATool.typings import AddonInfo, BrailleTables, SymbolDictionaries

# Since some strings in `addon_info` are translatable,
# we need to include them in the .po files.
# Gettext recognizes only strings given as parameters to the `_` function.
# To avoid initializing translations in this module we simply import a "fake" `_` function
# which returns whatever is given to it as an argument.
from site_scons.site_tools.NVDATool.utils import _

# Add-on information variables
addon_info = AddonInfo(
	# add-on Name/identifier, internal for NVDA. Never change it: NVDA uses it to find the installed add-on.
	addon_name="nusaNewsID",
	# Add-on summary/title, usually the user visible name of the add-on
	# Translators: Summary/title for this add-on
	# to be shown on installation and add-on information found in add-on store
	addon_summary=_("NusaNewsID - Indonesian News Reader"),
	# Add-on description
	# Translators: Long description to be shown for this add-on on add-on information from add-on store
	addon_description=_(
		"Follows Indonesian news from Antara, Kompas, Detik, Republika, Liputan6, Merdeka, "
		"CNN Indonesia and WinPoin. Announces new stories in the background, "
		"keeps quiet during the hours you choose, and lets you read whole articles "
		"in an accessible window without opening a browser."
	),
	# version
	addon_version="1.1.0",
	# Brief changelog for this version
	# Translators: what's new content for the add-on version to be shown in the add-on store
	addon_changelog=_("""
- Merdeka works again: it now finds articles at Merdeka's new web addresses instead of links from the page footer.
- Antara works again inside NVDA: its security certificate is now checked with the certificates that come with NVDA, so the "CERTIFICATE_VERIFY_FAILED" error is gone. A certificate error is no longer retried three times.
- Clean titles and exact publication times: stories now come from each site's RSS feed where it is kept up to date, and from its pages otherwise. Leftovers such as times, section names or "Headline" no longer appear in titles.
- A story sounds the same everywhere: title first, then source, category and how long ago, with "Breaking" in front only for breaking news and "Belum dibaca" at the end only for unread stories. No more brackets, bars or dashes, which NVDA read differently depending on the punctuation level.
- Times are shown as "14 menit lalu" or "3 jam lalu" for the last day, and as "13 November 2026 pukul 20.00" for older stories. The list is sorted by publication time, newest first.
- The article reader shows one fact per line: title, source and category, publication time and link. "Salin berita" copies only the title and the article.
- Several new stories announced at once are now one message, so a braille display shows them all. The message names the key that opens the reader as set in Input Gestures.
- The first check after installing, or after deleting saved stories, fills the list quietly and says "NusaNews: N berita dimuat." instead of announcing hundreds of stories. Stories saved by older versions are marked read once, so "Belum dibaca" means new.
- Faster: stories are kept in memory and saved shortly after a change, article texts are saved separately, old stories are removed after every check, and the list is no longer limited to 500 stories.
- Settings are the same in every configuration profile from NVDA 2026.3.
- Settings are grouped and labelled: sources are a checkable list, quiet hours must be times such as 22:00, and deleting saved stories asks with NVDA's own confirmation dialog.
- The news list has a label, keeps the selected story selected when new stories arrive, and reads a story once when you return from the reader. Refresh is now Alt+G, because Alt+S moves to the source filter.
- Every story now has the category it was listed under: stories from sidebars, "popular" boxes and other sections of a page are left out.
- Stories older than the cache period are no longer added, so news from 2023 or 2024 is no longer announced as new.
- Breaking news is now only about disasters and emergencies. Words such as "presiden" or "waspada" no longer mark ordinary stories as breaking, so they no longer break through quiet hours.
- The disability category matches whole words only, and no longer picks up stories with words such as "menulis", "lumpuh" or "inklusif".
- Tempo and MacPoin are removed: Tempo refuses connections from the add-on, and MacPoin has not published since March 2024.
- Some sources no longer offer a category that the site stopped updating: Detik and Republika have no politics, and Republika has no entertainment.
- Refresh no longer starts a second background check, so new stories are no longer announced twice. After a refresh, NVDA says how many new stories were found.
- Stopping NVDA or reloading add-ons no longer waits for the current news check to finish.
- On secure screens, such as the Windows sign-in screen, the news reader no longer opens and NVDA no longer logs an error when it closes.
	"""),
	# Author(s)
	addon_author="Rexya Muhamad Rizki <rexya2017@gmail.com>",
	# URL for the add-on documentation support
	addon_url="https://github.com/InfiArtt/nusa-news-id",
	# URL for the add-on repository where the source code can be found
	addon_sourceURL="https://github.com/InfiArtt/nusa-news-id",
	# Documentation file name
	addon_docFileName="readme.html",
	# Minimum NVDA version supported (e.g. "2019.3.0", minor version is optional)
	addon_minimumNVDAVersion="2026.1",
	# Last NVDA version supported/tested (e.g. "2024.4.0", ideally more recent than minimum version)
	addon_lastTestedNVDAVersion="2026.3.1",
	# Add-on update channel (default is None, denoting stable releases,
	# and for development releases, use "dev".)
	# Do not change unless you know what you are doing!
	addon_updateChannel=None,
	# Add-on license such as GPL 2
	addon_license="GNU General Public License, version 2 or later",
	# URL for the license document the ADDON is licensed under
	addon_licenseURL="https://www.gnu.org/licenses/gpl-2.0.html",
)

# Define the python files that are the sources of your add-on.
# You can either list every file (using ""/") as a path separator,
# or use glob expressions.
pythonSources: list[str] = [
	"addon/globalPlugins/nusaNewsID/**/*.py",
	"addon/installTasks.py",
]

# Files that contain strings for translation. Usually your python sources
i18nSources: list[str] = pythonSources + ["buildVars.py"]

# Files that will be ignored when building the nvda-addon file
# Paths are relative to the addon directory, not to the root directory of your addon sources.
# You can either list every file (using ""/") as a path separator,
# or use glob expressions.
excludedFiles: list[str] = ["*.pyc"]

# Base language for the NVDA add-on
# If your add-on is written in a language other than english, modify this variable.
# For example, set baseLanguage to "es" if your add-on is primarily written in spanish.
# You must also edit .gitignore file to specify base language files to be ignored.
baseLanguage: str = "en"

# Markdown extensions for add-on documentation
# Most add-ons do not require additional Markdown extensions.
# If you need to add support for markup such as tables, fill out the below list.
# Extensions string must be of the form "markdown.extensions.extensionName"
# e.g. "markdown.extensions.tables" to add tables.
markdownExtensions: list[str] = []

# Custom braille translation tables
# If your add-on includes custom braille tables (most will not), fill out this dictionary.
brailleTables: BrailleTables = {}

# Custom speech symbol dictionaries
# Symbol dictionary files reside in the locale folder, e.g. `locale\en`, and are named `symbols-<name>.dic`.
# If your add-on includes custom speech symbol dictionaries (most will not), fill out this dictionary.
symbolDictionaries: SymbolDictionaries = {}
