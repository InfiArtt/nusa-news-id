"""Downloads: what is retried and what is not."""

import gzip
import ssl
import threading
import time
import urllib.error

import pytest

from nusaNewsID import networkUtils


class _Response:
	def __init__(self, body: bytes, headers: dict | None = None) -> None:
		self._body = body
		self.headers = headers or {}

	def read(self) -> bytes:
		return self._body

	def __enter__(self) -> "_Response":
		return self

	def __exit__(self, *args) -> None:
		return None


@pytest.fixture
def calls(monkeypatch):
	"""Replace urlopen; each test sets ``calls.outcomes`` to responses or exceptions, used in order."""
	state = type("State", (), {"count": 0, "outcomes": []})()

	def fakeUrlopen(request, timeout, context):
		state.count += 1
		outcome = state.outcomes[min(state.count, len(state.outcomes)) - 1]
		if isinstance(outcome, BaseException):
			raise outcome
		return outcome

	monkeypatch.setattr(networkUtils.urllib.request, "urlopen", fakeUrlopen)
	monkeypatch.setattr(networkUtils, "FIRST_BACKOFF_SECONDS", 0.01)
	return state


def test_certificate_error_is_not_retried(calls):
	calls.outcomes = [urllib.error.URLError(ssl.SSLCertVerificationError("unable to get local issuer certificate"))]
	assert networkUtils.fetch_http_data("https://www.antaranews.com/nasional") is None
	assert calls.count == 1


def test_client_error_is_not_retried(calls):
	calls.outcomes = [urllib.error.HTTPError("https://www.tempo.co/politik", 403, "Forbidden", {}, None)]
	assert networkUtils.fetch_http_data("https://www.tempo.co/politik") is None
	assert calls.count == 1


def test_network_error_is_retried_then_succeeds(calls):
	calls.outcomes = [urllib.error.URLError("timed out"), _Response(b"<html></html>")]
	assert networkUtils.fetch_http_data("https://news.detik.com") == b"<html></html>"
	assert calls.count == 2


def test_gzip_body_is_decompressed(calls):
	calls.outcomes = [_Response(gzip.compress(b"berita"), {"Content-Encoding": "gzip"})]
	assert networkUtils.fetch_http_data("https://news.detik.com") == b"berita"


def test_stop_event_ends_the_backoff_at_once(calls, monkeypatch):
	monkeypatch.setattr(networkUtils, "FIRST_BACKOFF_SECONDS", 30.0)
	calls.outcomes = [urllib.error.URLError("timed out")]
	stopEvent = threading.Event()
	threading.Timer(0.1, stopEvent.set).start()
	started = time.monotonic()
	assert networkUtils.fetch_http_data("https://news.detik.com", stop_event=stopEvent) is None
	assert time.monotonic() - started < 5
	assert calls.count == 1


def test_no_request_after_stop(calls):
	calls.outcomes = [_Response(b"x")]
	stopEvent = threading.Event()
	stopEvent.set()
	assert networkUtils.fetch_http_data("https://news.detik.com", stop_event=stopEvent) is None
	assert calls.count == 0


def test_ssl_context_trusts_certifi():
	certifi = pytest.importorskip("certifi")
	context = networkUtils._createSslContext()
	assert context.verify_mode == ssl.CERT_REQUIRED
	assert context.cert_store_stats()["x509_ca"] > 0
	assert certifi.where()
