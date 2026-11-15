"""New versions come from the add-on's GitHub releases, checked before they are installed."""

import hashlib
import io
import zipfile

import pytest
from nusaNewsID import updates

DOWNLOAD = "https://github.com/InfiArtt/nusa-news-id/releases/download/v1.2.0/"


def release_data(tag="v1.2.0", **changes):
	data = {
		"tag_name": tag,
		"draft": False,
		"prerelease": False,
		"body": "### Ditambahkan\n\n- Sistem pembaruan.\n\nSHA256 checksum:\n\n```\nabc  ./x.nvda-addon\n```\n",
		"assets": [
			{"name": "notes.txt", "browser_download_url": DOWNLOAD + "notes.txt"},
			{
				"name": f"nusaNewsID-{tag.lstrip('v')}.nvda-addon",
				"browser_download_url": DOWNLOAD + f"nusaNewsID-{tag.lstrip('v')}.nvda-addon",
				"digest": "sha256:ABCDEF",
			},
		],
	}
	data.update(changes)
	return data


def test_versions_compare_by_number():
	assert updates.is_newer("v1.10.0", "1.9.9")
	assert updates.is_newer("1.2", "1.1.9")
	assert not updates.is_newer("1.1.0", "1.1")
	assert not updates.is_newer("v1.0.2", "1.1.0")
	assert updates.version_tuple("v1.2.3-beta") == (1, 2, 3)
	with pytest.raises(updates.UpdateError):
		updates.version_tuple("latest")


def test_release_takes_the_addon_file_its_checksum_and_the_changes():
	release = updates.parse_release(release_data())
	assert release.version == "1.2.0"
	assert release.file_name == "nusaNewsID-1.2.0.nvda-addon"
	assert release.sha256 == "abcdef"
	# The update window shows the changelog section, without the checksum the release notes end with.
	assert release.notes == "### Ditambahkan\n\n- Sistem pembaruan."


def test_files_from_elsewhere_prereleases_and_missing_checksums_are_refused():
	elsewhere = release_data(
		assets=[{"name": "x.nvda-addon", "browser_download_url": "https://example.com/x.nvda-addon"}]
	)
	with pytest.raises(updates.UpdateError):
		updates.parse_release(elsewhere)
	with pytest.raises(updates.UpdateError):
		updates.parse_release(release_data(prerelease=True))
	data = release_data()
	del data["assets"][1]["digest"]
	with pytest.raises(updates.UpdateError, match="noChecksum"):
		updates.parse_release(data)


def test_newest_release_with_its_file_is_chosen():
	no_file = release_data("v1.3.0", assets=[])
	releases = [release_data("v1.1.0"), no_file, release_data("v1.2.0"), release_data("v2.0.0", draft=True)]
	assert updates.newest_release(releases).version == "1.2.0"
	with pytest.raises(updates.UpdateError, match="noRelease"):
		updates.newest_release([release_data(draft=True)])


def _package(name="nusaNewsID", version="1.2.0") -> bytes:
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w") as archive:
		archive.writestr("manifest.ini", f'name = "{name}"\nversion = "{version}"\n')
	return buffer.getvalue()


class _Response(io.BytesIO):
	def __enter__(self):
		return self

	def __exit__(self, *args):
		self.close()


@pytest.mark.parametrize(
	("content", "checksum", "error"),
	[
		(_package(), None, None),
		(_package(), "0" * 64, "badChecksum"),
		(_package(name="otherAddon"), None, "badPackage"),
		(_package(version="1.1.0"), None, "badPackage"),
	],
)
def test_download_is_checked_and_removed_when_wrong(tmp_path, monkeypatch, content, checksum, error):
	release = updates.Release(
		"1.2.0",
		"",
		DOWNLOAD + "x.nvda-addon",
		"x.nvda-addon",
		checksum or hashlib.sha256(content).hexdigest(),
	)
	monkeypatch.setattr(updates, "_open", lambda url, accept, timeout: _Response(content))
	path = tmp_path / "x.nvda-addon"
	if error is None:
		assert updates.download(release, str(path)) == str(path)
		assert path.read_bytes() == content
	else:
		with pytest.raises(updates.UpdateError, match=error):
			updates.download(release, str(path))
		assert not path.exists()
