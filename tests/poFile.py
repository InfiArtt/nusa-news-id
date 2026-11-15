"""Read the add-on's po files for the tests: translations, and a way to use them instead of NVDA's gettext."""

import ast
import builtins
import re
from contextlib import contextmanager
from pathlib import Path

LOCALE = Path(__file__).resolve().parent.parent / "addon" / "locale"


def entries(language: str) -> list[dict]:
	"""Each message as {"msgid", "msgid_plural", "msgstr"}; the header is left out."""
	text = (LOCALE / language / "LC_MESSAGES" / "nvda.po").read_text(encoding="utf-8")
	found = []
	for block in text.strip().split("\n\n"):
		fields: dict[str, list[str]] = {}
		key = None
		for line in block.splitlines():
			if line.startswith("#"):
				continue
			match = re.match(r"^(msgid_plural|msgid|msgstr(?:\[\d\])?) (\".*\")$", line)
			if match:
				key = match.group(1).replace("[0]", "")
				fields[key] = [match.group(2)]
			elif key:
				fields[key].append(line)
		joined = {name: "".join(ast.literal_eval(part) for part in parts) for name, parts in fields.items()}
		if joined.get("msgid"):
			found.append(joined)
	return found


@contextmanager
def translated(language: str):
	"""Use a po file's translations for _ and ngettext while the block runs."""
	table = {entry["msgid"]: entry["msgstr"] for entry in entries(language)}
	saved = builtins._, builtins.ngettext
	builtins._ = lambda text: table.get(text) or text
	builtins.ngettext = lambda singular, plural, count: (
		table.get(singular) or (singular if count == 1 else plural)
	)
	try:
		yield
	finally:
		builtins._, builtins.ngettext = saved
