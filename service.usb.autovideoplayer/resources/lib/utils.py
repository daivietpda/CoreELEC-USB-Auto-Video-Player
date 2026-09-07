# -*- coding: utf-8 -*-
"""Utility functions for logging, notifications, and string sorting."""

import re
import traceback
import xbmc
import xbmcgui
from resources.lib.constants import LOG_PREFIX


def natural_sort_key(s):
    """
    Returns a key for natural sorting of strings containing numbers.
    E.g. ['1.mp4', '2.mp4', '10.mp4'] instead of ['1.mp4', '10.mp4', '2.mp4'].
    """
    if not isinstance(s, str):
        s = str(s)
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]


def log(msg, level=xbmc.LOGINFO):
    """Logs message with standard prefix."""
    try:
        xbmc.log(f"{LOG_PREFIX} {msg}", level)
    except Exception:
        pass


def log_debug(msg, is_debug_enabled=False):
    """Logs debug message if debug logging is enabled."""
    if is_debug_enabled:
        log(f"[DEBUG] {msg}", xbmc.LOGDEBUG)


def log_error(msg, exc=None):
    """Logs error message with standard prefix and optional traceback."""
    try:
        if exc:
            tb = traceback.format_exc()
            xbmc.log(f"{LOG_PREFIX}[ERROR] {msg}: {exc}\n{tb}", xbmc.LOGERROR)
        else:
            xbmc.log(f"{LOG_PREFIX}[ERROR] {msg}", xbmc.LOGERROR)
    except Exception:
        pass


def notify(heading, message, duration=3000, icon=xbmcgui.NOTIFICATION_INFO, enabled=True):
    """Displays a notification dialog if enabled."""
    if not enabled:
        return
    try:
        xbmcgui.Dialog().notification(heading, message, icon, duration)
    except Exception as e:
        log_error(f"Failed to display notification: {e}")
