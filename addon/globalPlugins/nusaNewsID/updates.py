# updates.py
#
# New versions of the add-on, from its GitHub releases. Taken from InfiArtt's WhatsApp Access add-on.
# Only Python's standard library and networkUtils' certificates, so the tests can use it without NVDA.

import contextlib
import hashlib
import http.client
import json
import os
import re
import urllib.request
import zipfile
from dataclasses import dataclass

REPOSITORY = "InfiArtt/nusa-news-id"
# The newest releases, newest first.
RELEASES_URL = f"https://api.github.com/repos/{REPOSITORY}/releases?per_page=30"
USER_AGENT = "NusaNewsID-NVDA-addon"
# Release files are only taken from GitHub itself.
DOWNLOAD_PREFIX = f"https://github.com/{REPOSITORY}/releases/download/"
ADDON_NAME = "nusaNewsID"
# The release notes are the version's whole CHANGELOG.md section, which can be long.
MAX_NOTES = 30000
# The release notes end with the file's checksum, which is of no use in the update window.
_CHECKSUM_PART = re.compile(r"\n+SHA256 checksum:.*\Z", re.DOTALL)


class UpdateError(Exception):
	pass


@dataclass
class Release:
	version: str
	notes: str
	url: str
	file_name: str
	sha256: str


def version_tuple(version: str) -> tuple[int, ...]:
	"""'v1.2.10' -> (1, 2, 10). Anything after the numbers, such as '-beta', is ignored."""
	match = re.match(r"v?(\d+(?:\.\d+)*)", version.strip())
	if not match:
		raise UpdateError(f"badVersion: {version}")
	return tuple(int(part) for part in match.group(1).split("."))


def is_newer(latest: str, current: str) -> bool:
	a, b = version_tuple(latest), version_tuple(current)
	length = max(len(a), len(b))
	return a + (0,) * (length - len(a)) > b + (0,) * (length - len(b))


def release_notes(body: str) -> str:
	"""What changed, from a release's description, without the checksum at its end."""
	notes = _CHECKSUM_PART.sub("", (body or "").replace("\r\n", "\n")).strip()
	if len(notes) > MAX_NOTES:
		notes = notes[:MAX_NOTES].rstrip() + "…"
	return notes


def parse_release(data: dict) -> Release:
	"""One published release, from GitHub's answer.

	It must carry a .nvda-addon file from this repository with GitHub's SHA-256 of it. Without the checksum
	nothing is installed: the file can't be checked, and NVDA would run whatever arrived.
	"""
	if data.get("draft") or data.get("prerelease"):
		raise UpdateError("noRelease")
	version = str(data.get("tag_name") or "")
	version_tuple(version)
	for asset in data.get("assets") or []:
		name = str(asset.get("name") or "")
		url = str(asset.get("browser_download_url") or "")
		if name.endswith(".nvda-addon") and url.startswith(DOWNLOAD_PREFIX):
			digest = str(asset.get("digest") or "")
			sha256 = digest.split(":", 1)[1].lower() if digest.startswith("sha256:") else ""
			if not sha256:
				raise UpdateError("noChecksum")
			# Only the name: it becomes a file in the temporary folder.
			file_name = os.path.basename(name.replace("\\", "/"))
			return Release(
				version.lstrip("v"), release_notes(str(data.get("body") or "")), url, file_name, sha256
			)
	raise UpdateError("noAddonFile")


def _published(data: dict) -> bool:
	if not isinstance(data, dict) or data.get("draft") or data.get("prerelease"):
		return False
	try:
		version_tuple(str(data.get("tag_name") or ""))
	except UpdateError:
		return False
	return True


def newest_release(releases: list) -> Release:
	"""The newest published release that has its add-on file.

	A release whose file is not uploaded yet is passed over, so it does not keep everyone from the one
	before it.
	"""
	published = [data for data in releases if _published(data)]
	if not published:
		raise UpdateError("noRelease")
	problem: UpdateError | None = None
	for data in sorted(published, key=lambda data: version_tuple(str(data["tag_name"])), reverse=True):
		try:
			return parse_release(data)
		except UpdateError as e:
			problem = problem or e
	raise problem or UpdateError("noRelease")


def _open(url: str, accept: str, timeout: float):
	from .networkUtils import _getSslContext

	request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
	return urllib.request.urlopen(request, timeout=timeout, context=_getSslContext())


def latest_release(timeout: float = 15) -> Release:
	try:
		with _open(RELEASES_URL, "application/vnd.github+json", timeout) as response:
			data = json.load(response)
	except (OSError, http.client.HTTPException) as e:
		code = getattr(e, "code", None)
		# 404: the repository is not public.
		raise UpdateError("noRelease" if code == 404 else f"network: {e}") from e
	except ValueError as e:
		raise UpdateError(f"network: {e}") from e
	if not isinstance(data, list):
		raise UpdateError("noRelease")
	return newest_release(data)


def check_package(path: str, version: str) -> None:
	"""The file must be this add-on, at the version its release names; otherwise a release whose file is
	another add-on, or another version than its tag, would be installed."""
	try:
		with zipfile.ZipFile(path) as package:
			manifest = package.read("manifest.ini").decode("utf-8")
	except (OSError, KeyError, UnicodeDecodeError, zipfile.BadZipFile) as e:
		raise UpdateError(f"badPackage: {e}") from e
	values = {}
	for line in manifest.splitlines():
		key, sep, value = line.partition("=")
		if sep:
			values[key.strip()] = value.strip().strip('"')
	if values.get("name") != ADDON_NAME:
		raise UpdateError(f"badPackage: name {values.get('name')!r}")
	try:
		same = version_tuple(values.get("version", "")) == version_tuple(version)
	except UpdateError:
		same = False
	if not same:
		raise UpdateError(f"badPackage: version {values.get('version')!r} for {version}")


def download(release: Release, path: str, timeout: float = 60) -> str:
	"""Save the release's add-on file at path, checking it against GitHub's SHA-256.

	A download that fails or does not match is removed, so no partial or damaged file is left behind.
	"""
	digest = hashlib.sha256()
	try:
		try:
			with (
				_open(release.url, "application/octet-stream", timeout) as response,
				open(path, "wb") as file,
			):
				while chunk := response.read(64 * 1024):
					digest.update(chunk)
					file.write(chunk)
		except (OSError, http.client.HTTPException) as e:
			# A connection that drops partway raises IncompleteRead, which is no OSError.
			raise UpdateError(f"network: {e}") from e
		if digest.hexdigest() != release.sha256:
			raise UpdateError("badChecksum")
		check_package(path, release.version)
	except BaseException:
		with contextlib.suppress(OSError):
			os.remove(path)
		raise
	return path
