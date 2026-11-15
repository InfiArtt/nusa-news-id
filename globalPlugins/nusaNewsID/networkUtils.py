# -*- coding: utf-8 -*-
# networkUtils.py
#
# Documentation Compliance Notes:
# - Extracted from baseProvider to prevent circular dependencies.
# - Uses standard urllib.request and ssl libraries to fetch data.

import ssl
import time
import urllib.request
import urllib.error
import gzip
import logHandler
from typing import Optional

def fetch_http_data(url: str, bypass_ssl: bool = False, timeout: int = 10) -> Optional[bytes]:
	"""
	Helper method performing HTTP GET requests with strict validation defaults and exponential retries.
	"""
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
	}
	req = urllib.request.Request(url, headers=headers)
	
	# Enforce strict SSL verification by default. Fall back to unverified context only if opt-in checkbox is checked.
	context = ssl._create_unverified_context() if bypass_ssl else None
	
	retries = 2
	backoff = 2.0  # Seconds
	
	for attempt in range(retries + 1):
		try:
			# Synchronous request execution inside background MonitorThread
			with urllib.request.urlopen(req, timeout=timeout, context=context) as response:
				data = response.read()
				if response.info().get('Content-Encoding') == 'gzip' or data.startswith(b'\x1f\x8b'):
					data = gzip.decompress(data)
				return data
		except (urllib.error.URLError, ssl.SSLError) as e:
			logHandler.log.warning(
				f"NusaNews: Failed to retrieve {url} (Attempt {attempt+1}/{retries+1}) - Error: {e}"
			)
			if attempt < retries:
				time.sleep(backoff)
				backoff *= 2.0  # 2s -> 4s
			else:
				logHandler.log.error(f"NusaNews: Final retry failed. Network connection unavailable for {url}.")
		except Exception as e:
			logHandler.log.error(f"NusaNews: Non-network error occurred while requesting {url} - Error: {e}")
			break
			
	return None
