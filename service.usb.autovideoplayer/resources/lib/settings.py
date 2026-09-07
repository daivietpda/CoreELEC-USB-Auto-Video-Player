# -*- coding: utf-8 -*-
"""Settings manager for USB Auto Video Player."""

import json
import xbmcaddon
from resources.lib.constants import (
    ADDON_ID,
    USB_DELAYS,
    MODE_SINGLE_LOOP,
    SORT_A_TO_Z,
)
from resources.lib.utils import log_error


class SettingsManager:
    """Provides typed access to add-on settings."""

    def __init__(self):
        self._addon = None

    @property
    def addon(self):
        """Lazy load xbmcaddon instance."""
        if self._addon is None:
            self._addon = xbmcaddon.Addon(ADDON_ID)
        return self._addon

    def reload(self):
        """Forces refresh of addon settings instance."""
        self._addon = xbmcaddon.Addon(ADDON_ID)

    def is_enabled(self):
        try:
            return self.addon.getSettingBool("enabled")
        except Exception:
            return True

    def is_autoplay_on_insert(self):
        try:
            return self.addon.getSettingBool("autoplay_on_insert")
        except Exception:
            return True

    def get_playback_mode(self):
        try:
            return self.addon.getSettingInt("playback_mode")
        except Exception:
            return MODE_SINGLE_LOOP

    def get_sort_order(self):
        try:
            return self.addon.getSettingInt("sort_order")
        except Exception:
            return SORT_A_TO_Z

    def is_scan_subfolders(self):
        try:
            return self.addon.getSettingBool("scan_subfolders")
        except Exception:
            return True

    def is_fullscreen(self):
        try:
            return self.addon.getSettingBool("fullscreen")
        except Exception:
            return True

    def is_repeat(self):
        try:
            return self.addon.getSettingBool("repeat")
        except Exception:
            return True

    def get_usb_delay(self):
        """Returns delay in seconds according to selected enum option."""
        try:
            idx = self.addon.getSettingInt("usb_delay")
            if 0 <= idx < len(USB_DELAYS):
                return USB_DELAYS[idx]
            return 2
        except Exception:
            return 2

    def is_notifications_enabled(self):
        try:
            return self.addon.getSettingBool("notifications")
        except Exception:
            return True

    def is_debug_log_enabled(self):
        try:
            return self.addon.getSettingBool("debug_log")
        except Exception:
            return False

    def get_manual_selected_files(self):
        """Returns list of relative video filepaths saved for Manual Mode."""
        try:
            raw = self.addon.getSettingString("manual_selected_files")
            if raw:
                data = json.loads(raw)
                if isinstance(data, list):
                    return data
        except Exception as e:
            log_error("Failed to parse manual_selected_files setting", e)
        return []

    def set_manual_selected_files(self, file_list):
        """Saves list of relative video filepaths for Manual Mode."""
        try:
            serialized = json.dumps(file_list, ensure_ascii=False)
            self.addon.setSettingString("manual_selected_files", serialized)
            return True
        except Exception as e:
            log_error("Failed to save manual_selected_files setting", e)
            return False
