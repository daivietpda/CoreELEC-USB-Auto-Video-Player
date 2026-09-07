# -*- coding: utf-8 -*-
"""Stream availability probe and monitor for HLS streams."""

import time
import urllib.request
import urllib.error

try:
    from resources.lib.utils import log_debug, log_error
except Exception:
    def log_debug(msg, debug=False):
        if debug:
            print(f"[DEBUG] {msg}")
    def log_error(msg, exc=None):
        print(f"[ERROR] {msg}: {exc}")


def check_hls_stream(url, timeout=2.0, debug=False):
    """
    Performs a lightweight probe to verify if the HLS stream is online.
    Returns tuple: (is_online: bool, message: str)
    Guaranteed not to hang or block beyond timeout.
    """
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        return False, "Invalid URL scheme"

    headers = {
        "User-Agent": "Kodi/21.3 (CoreELEC; Amlogic-ne)",
        "Accept": "*/*",
    }

    # Step 1: Try lightweight HTTP HEAD request
    try:
        req = urllib.request.Request(url, headers=headers, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                log_debug(f"HLS HEAD probe 200 OK: {url}", debug)
                return True, "OK"
    except urllib.error.HTTPError as e:
        if e.code == 405:
            # 405 Method Not Allowed - Server does not accept HEAD, fallback to GET
            pass
        else:
            log_debug(f"HLS HEAD probe HTTP {e.code}: {url}", debug)
            return False, f"HTTP Error {e.code}"
    except urllib.error.URLError as e:
        log_debug(f"HLS HEAD probe connection error: {e.reason}", debug)
        return False, f"Connection error: {e.reason}"
    except Exception as e:
        log_debug(f"HLS HEAD probe exception: {e}", debug)
        return False, f"Error: {e}"

    # Step 2: Fallback to small GET request
    try:
        headers["Range"] = "bytes=0-512"
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status in (200, 206):
                content = response.read(512)
                log_debug(f"HLS GET probe success ({len(content)} bytes): {url}", debug)
                return True, "OK"
    except urllib.error.HTTPError as e:
        log_debug(f"HLS GET probe HTTP {e.code}: {url}", debug)
        return False, f"HTTP Error {e.code}"
    except urllib.error.URLError as e:
        log_debug(f"HLS GET probe connection error: {e.reason}", debug)
        return False, f"Connection error: {e.reason}"
    except Exception as e:
        log_debug(f"HLS GET probe exception: {e}", debug)
        return False, f"Error: {e}"

    return False, "Probe failed"


class StreamMonitor:
    """Manages HLS stream health checking and polling schedule."""

    def __init__(self, debug=False):
        self.debug = debug
        self.last_check_time = 0
        self.is_online = False
        self.last_reason = ""
        self.last_url = ""

    def probe(self, url, timeout=2.0):
        """Immediately probes the specified URL and updates state."""
        self.last_url = url
        self.last_check_time = time.time()
        self.is_online, self.last_reason = check_hls_stream(url, timeout, self.debug)
        return self.is_online, self.last_reason

    def should_check(self, interval_seconds):
        """Returns True if the retry interval has elapsed since last probe."""
        return (time.time() - self.last_check_time) >= interval_seconds

    def reset(self):
        """Resets state."""
        self.last_check_time = 0
        self.is_online = False
        self.last_reason = ""
