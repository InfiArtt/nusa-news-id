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
		"CNN Indonesia and WinPoin. It announces new stories in the background, stays quiet during "
		"the hours you choose, and opens whole articles in an accessible window, so you do not need a browser."
	),
	# version
	addon_version="1.1.0",
	# Brief changelog for this version
	# Translators: what's new content for the add-on version to be shown in the add-on store
	addon_changelog=_("""
- InfiArtt, the organization that makes this add-on, is now a source that is always on. New articles from infiartt.com/posts and new guides from the knowledge base at infiartt.com/kb appear in two new categories, InfiArtt articles and InfiArtt knowledge base, right below All in the source filter. Every InfiArtt article and guide is listed, however old, and stays in storage. The list and the reader name each one's author. The add-on reads them through InfiArtt's own API.
- The reader shows the article as a web page that NVDA reads in browse mode, with the article's headings, lists, quotes and links, so you can move by heading with H. The article is marked as Indonesian, so NVDA can switch to an Indonesian voice.
- For low vision: Control+plus, Control+minus and Control+0 change the reader's text size from 100 to 400 percent, and the new setting "Reader text size" keeps it. The page uses the Windows colors, including contrast themes, with wider line spacing and lines of at most 70 characters.
- Articles are cleaner. Ads, "baca juga" boxes, sidebars, copyright lines and office addresses are left out, and images appear with their descriptions.
- A source with no saved stories yet, such as one you just turned on, or InfiArtt with its whole archive, is saved quietly as read instead of being announced story by story.
- An empty news list now says why it is empty, instead of NVDA saying "unknown".
- Merdeka works again. The add-on finds its articles at Merdeka's new web addresses.
- Antara works again inside NVDA. Its certificate is checked against the certificates that come with NVDA, so the "CERTIFICATE_VERIFY_FAILED" error is gone, and certificate errors are no longer retried.
- Titles are clean and times are exact. Stories come from each site's RSS feed when the feed is kept up to date, and from its pages otherwise.
- Each story stays in the category it was listed under. Sidebars, "popular" boxes and other sections of a page are left out.
- Stories older than the storage period are skipped, so old news is no longer announced as new.
- A story reads the same in the list, in notifications and in the reader: title first, then source, category and time. "Breaking" comes first only for breaking news, and "Unread" comes last only for unread stories. Brackets, bars and dashes are gone.
- Times read like "14 minutes ago" or "3 hours ago" during the first day, and as a date and time after that. The newest stories come first.
- The reader shows the title, the source and category, the publication time and the link on separate lines. "Copy story" copies only the title and the text.
- Several new stories are announced in one message, so a braille display shows all of them. The message names the key that opens the news list, including a key you set in Input Gestures.
- The first check after installing, or after deleting saved stories, saves the stories quietly and says how many it loaded. Stories saved by older versions are marked read once.
- The add-on is faster. It keeps stories in memory, saves them shortly after a change, and stores article texts separately. Old stories are removed after every check, and the list no longer stops at 500 stories.
- From NVDA 2026.3, the settings are the same in every configuration profile.
- The settings are grouped and labelled. Sources are a list of check boxes, quiet hours must be times such as 22:00, and NVDA's own dialog confirms deleting saved stories.
- The news list has a label, keeps your place when new stories arrive, and reads a story only once when you come back from the reader. Refresh is now Alt+R.
- Breaking news now means disasters and emergencies only. Words such as "presiden" no longer mark ordinary stories as breaking, so those stories stay quiet during quiet hours.
- The disability category matches whole words only.
- Tempo and MacPoin are removed. Tempo refuses connections from the add-on, and MacPoin has published nothing since March 2024.
- Detik and Republika no longer list politics, and Republika no longer lists entertainment, because the sites stopped updating those sections.
- Refresh no longer starts a second check, so stories are no longer announced twice. After a refresh, NVDA says how many new stories it found.
- Closing NVDA or reloading add-ons no longer waits for a news check to finish.
- On secure screens, such as the Windows sign-in screen, the news list no longer opens.
- The add-on's messages are now written in English, with an Indonesian translation that NVDA uses when its language is Indonesian.
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
