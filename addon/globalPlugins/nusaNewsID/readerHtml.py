# readerHtml.py
#
# The HTML page the article reader shows. It follows WCAG 2.2 for both screen reader and low vision users:
# - 1.3.1: the article keeps its headings, lists, quotes and links; the title is the only h1.
# - 3.1.1 and 3.1.2: the page has the add-on's language, the article its own, so NVDA can switch voices.
# - 1.4.3, 1.4.11 and 1.4.8: colors are Windows system colors (Window, WindowText, Highlight, GrayText,
#   ButtonFace, ButtonText), so the page follows the Windows colors and its contrast themes; no fixed colors.
# - 1.4.4, 1.4.10 and 1.4.12: sizes are in em, lines are at most 70 characters wide and wrap,
#   line height is 1.5 with space between paragraphs, and the text size can grow to 400 percent.
# - 1.1.1: images are only shown with a description, as visible text after the image (which then has an
#   empty alt), so it is read once. Videos and social posts are introduced by a line saying what they are.
# - 2.1.1, 2.4.7: every action is a real button with a visible focus outline; the dialog gives the same
#   shortcut keys, and Escape closes.
# The page is shown by Internet Explorer's engine, like NVDA's own HTML messages. The reader loads it from a
# file so it runs in IE 11 mode; the CSS and markup still work in the older IE 8 mode: landmarks are divs
# with ARIA roles rather than HTML5 elements, and each size in ch has an em size before it.
# The article itself comes from articleContent, which builds it from an allow list; nothing from the site
# is copied as is. No NVDA imports, so the tests can use it directly.

import html
import re

from .providers.articleContent import Article, blocks_html

# The text size at 100 percent zoom, in percent of the browser default.
BASE_TEXT_SIZE = 125

STYLE = """
body {
	margin: 0;
	background: Window;
	color: WindowText;
	font-family: "Segoe UI", sans-serif;
	line-height: 1.5;
	text-align: left;
	word-wrap: break-word;
}
.main { max-width: 38em; max-width: 70ch; margin: 0 auto; padding: 1em 1.25em 2em; }
h1 { font-size: 1.6em; line-height: 1.25; margin: 0 0 0.75em; }
h2 { font-size: 1.35em; line-height: 1.3; margin: 1.5em 0 0.5em; }
h3 { font-size: 1.2em; margin: 1.25em 0 0.5em; }
h4, h5, h6 { font-size: 1.05em; margin: 1em 0 0.5em; }
p, li, blockquote, pre { margin: 0 0 1em; }
ul, ol { padding-left: 1.5em; margin: 0 0 1em; }
blockquote { padding-left: 1em; border-left: 0.25em solid GrayText; }
pre, code, kbd { font-family: Consolas, monospace; }
pre { white-space: pre-wrap; }
a { text-decoration: underline; }
img { max-width: 100%; height: auto; }
.figure { margin: 1em 0; }
.caption { margin: 0.25em 0 0; }
blockquote .label { font-weight: bold; margin-bottom: 0.25em; }
.details { margin: 0 0 0.25em; }
.notice { padding: 0.75em 1em; border: 0.125em solid WindowText; }
.actions { margin-top: 2em; padding-top: 1em; border-top: 0.0625em solid GrayText; }
button {
	font: inherit;
	color: ButtonText;
	background: ButtonFace;
	border: 0.125em solid ButtonText;
	padding: 0.5em 1em;
	margin: 0 0.5em 0.5em 0;
	min-height: 2.75em;
}
a:focus, button:focus { outline: 0.2em solid Highlight; }
"""

# Sends a button's action to the add-on, which catches the address and runs the action.
SCRIPT = """
var buttons = document.getElementsByTagName("button");
for (var i = 0; i < buttons.length; i++) {
	buttons[i].onclick = function () {
		window.location.href = "nusanews-action:" + this.getAttribute("data-action");
	};
}
"""


def text_size(zoom: int) -> str:
	"""The CSS font size of the page for a zoom level in percent, such as "250%" for 200 percent."""
	return f"{round(BASE_TEXT_SIZE * zoom / 100)}%"


ACTIONS = ("browser", "link", "copy", "close")


def shortcut_key(label: str) -> str | None:
	"""The letter after & in a label such as "Open in &browser"."""
	match = re.search(r"&(\w)", label)
	return match.group(1).lower() if match else None


def build_page(
	title: str,
	details: list[str],
	url: str,
	article: Article | None,
	message: str | None,
	ui_language: str,
	labels: dict[str, str],
	zoom: int = 100,
) -> str:
	"""The whole page.

	details are the lines under the title (source and category, time), in the add-on's language.
	message replaces the article while it downloads or when it cannot be read.
	labels has the button labels with their & shortcut, for each of ACTIONS, "actions" for the group, and
	the words for photos, videos and social posts (see articleContent.blocks_html).
	zoom is the text size in percent.
	"""
	ui_language = _language(ui_language, "en")
	article_language = _language(article.language if article else None, "id")
	parts = [f'<h1 lang="{article_language}">{html.escape(title, quote=False)}</h1>']
	parts.extend(f'<p class="details">{html.escape(line, quote=False)}</p>' for line in details)
	escaped_url = html.escape(url)
	parts.append(f'<p class="details"><a href="{escaped_url}">{escaped_url}</a></p>')
	if message:
		parts.append(f'<p class="notice" role="status">{html.escape(message, quote=False)}</p>')
	# Some pages repeat the title as their own first heading; it is already the h1.
	blocks = [block for block in (article.blocks if article else []) if not _repeats(block.text, title)]
	if blocks:
		parts.append(
			f'<div lang="{article_language}">{blocks_html(_heading_levels(blocks), labels=labels)}</div>'
		)
	buttons = []
	for action in ACTIONS:
		label = labels[action]
		buttons.append(
			f'<button type="button" data-action="{action}">{html.escape(label.replace("&", ""))}</button>'
		)
	parts.append(
		f'<div class="actions" role="navigation" aria-label="{html.escape(labels["actions"])}">'
		f"{''.join(buttons)}</div>"
	)
	return (
		"<!doctype html>\n"
		f'<html lang="{ui_language}" style="font-size: {text_size(zoom)}">\n<head>\n<meta charset="utf-8">\n'
		'<meta http-equiv="X-UA-Compatible" content="IE=edge">\n'
		'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
		f"<title>{html.escape(title, quote=False)}</title>\n<style>{STYLE}</style>\n</head>\n"
		f'<body>\n<div class="main" role="main">\n<div role="article">\n{chr(10).join(parts[:-1])}\n</div>\n'
		f"{parts[-1]}\n</div>\n"
		f"<script>{SCRIPT}</script>\n</body>\n</html>\n"
	)


def _heading_levels(blocks: list) -> list:
	"""The page title is the only h1, so the article's headings start at h2 and never skip a level.

	Sites often jump from h2 to h4; NVDA's heading list then looks like a part is missing.
	"""
	from dataclasses import replace

	result = []
	previous = 1
	for block in blocks:
		if re.fullmatch(r"h[1-6]", block.kind):
			level = max(2, min(int(block.kind[1]), previous + 1))
			previous = level
			block = replace(block, kind=f"h{level}")
		result.append(block)
	return result


def _repeats(text: str, title: str) -> bool:
	def normal(value: str) -> str:
		return re.sub(r"\W+", " ", value).strip().casefold()

	return normal(text) == normal(title)


def _language(code: str | None, default: str) -> str:
	"""A language tag for the lang attribute, such as "id" or "en"; NVDA names such as "id_ID" become "id"."""
	if not code:
		return default
	match = re.match(r"[A-Za-z]{2,3}", code)
	return match.group(0).lower() if match else default
