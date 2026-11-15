"""The Indonesian translation is complete and keeps what the code needs."""

import re

import pytest
from poFile import entries

INDONESIAN = entries("id")


def test_every_message_is_translated():
	assert len(INDONESIAN) > 100
	assert [entry["msgid"] for entry in INDONESIAN if not entry["msgstr"].strip()] == []


@pytest.mark.parametrize("entry", INDONESIAN, ids=lambda entry: entry["msgid"][:40])
def test_placeholders_are_kept(entry):
	names = set(re.findall(r"\{(\w+)\}", entry["msgid"]))
	assert set(re.findall(r"\{(\w+)\}", entry["msgstr"])) == names


@pytest.mark.parametrize("entry", INDONESIAN, ids=lambda entry: entry["msgid"][:40])
def test_shortcut_keys_are_kept(entry):
	"""A label with a shortcut key (an & before a letter) needs one in the translation too."""
	assert entry["msgid"].count("&") == entry["msgstr"].count("&")


@pytest.mark.parametrize(
	"labels",
	[
		# The news list dialog.
		[
			"&Source:",
			"Ca&tegory:",
			"&Unread only",
			"Copy &link",
			"&Mark read",
			"Mark &all read",
			"&Refresh",
			"D&onate",
			"&Close",
		],
		# The article reader.
		["Open in &browser", "Copy &link", "Copy &story", "&Close"],
		# The settings panel, with NVDA's own Apply button (Alt+A).
		[
			"News &sources to follow:",
			"&Check for new stories every (minutes):",
			"&How to announce new stories:",
			"Play a &tone when new stories arrive",
			"Announce &breaking news during quiet hours too",
			"&Use quiet hours",
			"Sta&rt (hours:minutes, such as 22:00):",
			"&End (hours:minutes, such as 06:00):",
			"&Number of stories shown at a time:",
			"&Keep stories for (days):",
			"&Delete all saved stories",
			"Skip security certi&ficate checks (only if connections always fail; not safe)",
			"Support and d&onations",
			"&Apply",
		],
	],
	ids=["news list", "reader", "settings"],
)
def test_shortcut_keys_differ_within_a_window(labels):
	table = {entry["msgid"]: entry["msgstr"] for entry in INDONESIAN}
	for language in ("en", "id"):
		texts = labels if language == "en" else [table.get(label, label) for label in labels]
		keys = [re.search(r"&(\w)", text).group(1).lower() for text in texts]
		assert len(keys) == len(set(keys)), (language, texts)
