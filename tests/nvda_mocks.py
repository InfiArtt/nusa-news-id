"""Minimal stand-ins for NVDA and wx so the add-on can be tested without NVDA.

Importing this module registers the fakes in ``sys.modules``. Only what the tested code uses is faked.
"""

import builtins
import sys
from types import ModuleType, SimpleNamespace
from typing import Any

builtins._ = lambda text: text  # type: ignore[attr-defined]


def _module(name: str, **attributes: Any) -> ModuleType:
	module = ModuleType(name)
	module.__dict__.update(attributes)
	sys.modules[name] = module
	return module


class _Anything:
	"""Accepts any attribute access or call, for modules the tested code only touches at run time."""

	def __getattr__(self, name: str) -> "_Anything":
		return _Anything()

	def __call__(self, *args: Any, **kwargs: Any) -> "_Anything":
		return _Anything()


class _Log:
	"""Collects log calls so tests can check what was logged."""

	def __init__(self) -> None:
		self.records: list[tuple[str, str]] = []

	def __getattr__(self, level: str):
		return lambda message="", *args, **kwargs: self.records.append((level, str(message)))


spoken: list[str] = []
calledAfter: list[tuple] = []


class GlobalPlugin:
	def __init__(self) -> None:
		pass

	def terminate(self, *args: Any, **kwargs: Any) -> None:
		pass


class _CategoryClasses(list):
	pass


log = _Log()
_module("addonHandler", initTranslation=lambda: None, getCodeAddon=_Anything())
_module("logHandler", log=log)
_module("ui", message=lambda text, *args, **kwargs: spoken.append(text))
_module("tones", beep=lambda *args, **kwargs: None)
_module("wx", CallAfter=lambda function, *args, **kwargs: calledAfter.append((function, args, kwargs)))
_module("globalPluginHandler", GlobalPlugin=GlobalPlugin)
appArgs = SimpleNamespace(secure=False, configPath=None)
_module("globalVars", appArgs=appArgs)
_module("scriptHandler", script=lambda **kwargs: (lambda function: function))
_module("config", conf=_Anything())
settingsDialogs = _module(
	"gui.settingsDialogs",
	NVDASettingsDialog=SimpleNamespace(categoryClasses=_CategoryClasses()),
	SettingsPanel=object,
)
_module("gui", mainFrame=_Anything(), settingsDialogs=settingsDialogs, guiHelper=_Anything())
