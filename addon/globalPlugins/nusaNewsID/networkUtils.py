# networkUtils.py
#
# HTTP downloads for the providers and the article reader. Runs only in background threads.

import gzip
import os
import ssl
import threading
import urllib.error
import urllib.request

import logHandler

USER_AGENT = (
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
	"Chrome/140.0 Safari/537.36"
)
RETRIES = 2
FIRST_BACKOFF_SECONDS = 2.0

_sslContext: ssl.SSLContext | None = None
_sslContextLock = threading.Lock()


def _createSslContext() -> ssl.SSLContext:
	"""Trust both certifi's roots and the Windows store.

	Some sites (Antara) chain to roots that Windows only downloads when a Windows program asks for them,
	so Python's view of the Windows store alone fails with CERTIFICATE_VERIFY_FAILED.
	"""
	context = ssl.create_default_context()
	try:
		import certifi

		caFile = certifi.where()
		if caFile and os.path.isfile(caFile):
			context.load_verify_locations(cafile=caFile)
	except Exception as e:
		logHandler.log.warning(f"NusaNews: certifi is not available, using only Windows certificates: {e}")
	return context


def _getSslContext() -> ssl.SSLContext:
	global _sslContext
	with _sslContextLock:
		if _sslContext is None:
			_sslContext = _createSslContext()
		return _sslContext


def _isCertificateError(error: BaseException) -> bool:
	if isinstance(error, ssl.SSLCertVerificationError):
		return True
	reason = getattr(error, "reason", None)
	return isinstance(reason, ssl.SSLCertVerificationError)


def fetch_http_data(
	url: str,
	bypass_ssl: bool = False,
	timeout: int = 10,
	stop_event: threading.Event | None = None,
) -> bytes | None:
	"""Download a URL and return its body, or None when it fails.

	Network errors are retried with a backoff that ends at once when ``stop_event`` is set.
	Certificate errors are not retried: they will not go away by themselves.
	"""
	request = urllib.request.Request(
		url,
		headers={
			"User-Agent": USER_AGENT,
			"Accept": "text/html,application/xhtml+xml",
			"Accept-Language": "id-ID,id;q=0.9,en;q=0.5",
			"Accept-Encoding": "gzip",
		},
	)
	context = ssl._create_unverified_context() if bypass_ssl else _getSslContext()
	backoff = FIRST_BACKOFF_SECONDS
	for attempt in range(RETRIES + 1):
		if stop_event is not None and stop_event.is_set():
			return None
		try:
			with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
				data = response.read()
				if response.headers.get("Content-Encoding") == "gzip" or data.startswith(b"\x1f\x8b"):
					data = gzip.decompress(data)
				return data
		except (urllib.error.URLError, ssl.SSLError, TimeoutError, ConnectionError) as e:
			if _isCertificateError(e):
				logHandler.log.warning(f"NusaNews: Certificate of {url} could not be verified: {e}")
				return None
			if isinstance(e, urllib.error.HTTPError) and 400 <= e.code < 500:
				logHandler.log.warning(f"NusaNews: {url} answered HTTP {e.code}")
				return None
			logHandler.log.warning(
				f"NusaNews: Failed to retrieve {url} (attempt {attempt + 1}/{RETRIES + 1}): {e}"
			)
			if attempt < RETRIES:
				if stop_event is not None:
					if stop_event.wait(backoff):
						return None
				else:
					threading.Event().wait(backoff)
				backoff *= 2.0
		except Exception as e:
			logHandler.log.error(f"NusaNews: Unexpected error while requesting {url}: {e}")
			return None
	logHandler.log.error(f"NusaNews: Giving up on {url} after {RETRIES + 1} attempts.")
	return None
