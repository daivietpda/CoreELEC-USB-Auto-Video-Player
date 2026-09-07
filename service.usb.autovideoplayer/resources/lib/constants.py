# -*- coding: utf-8 -*-
"""Constants for USB Auto Video Player."""

ADDON_ID = "service.usb.autovideoplayer"
LOG_PREFIX = "[USB-AutoVideo]"

# Mandatory & extended video formats (all checked case-insensitively)
SUPPORTED_EXTENSIONS = (
    ".mp4",
    ".mpg",
    ".mpeg",
    ".mkv",
    ".avi",
    ".ts",
    ".m2ts",
    ".mov",
)

# Playback Modes
MODE_SINGLE_LOOP = 0      # Tự động phát 1 video và lặp lại
MODE_MULTIPLE_LOOP = 1    # Tự động phát tất cả video và lặp lại
MODE_MANUAL = 2           # Chọn video thủ công

# Sort Orders
SORT_A_TO_Z = 0
SORT_Z_TO_A = 1
SORT_RANDOM = 2

# USB Delay index mapping (in seconds)
USB_DELAYS = [0, 1, 2, 3, 5, 10]

# HLS Priority Modes
HLS_PRIORITY_FIRST = 0        # Ưu tiên HLS (Fallback sang USB khi offline)
HLS_PRIORITY_USB_FIRST = 1    # Ưu tiên USB (Fallback sang HLS khi không có USB)
HLS_PRIORITY_ONLY = 2         # Chỉ phát luồng HLS

# HLS Retry Intervals (in seconds)
HLS_RETRY_INTERVALS = [10, 15, 30, 60]

# HLS Connection Timeouts (in seconds)
HLS_TIMEOUTS = [2, 3, 5]

# System mounts and paths that must never be treated as external USB
SYSTEM_MOUNT_PREFIXES = (
    "/flash",
    "/storage",
    "/run",
    "/dev",
    "/sys",
    "/proc",
    "/tmp",
    "/android",
)

# System and metadata directory names on USB to skip
EXCLUDED_DIR_NAMES = {
    "system volume information",
    "$recycle.bin",
    "lost.dir",
    ".trash",
    ".trashes",
    ".spotlight-v100",
    ".fseventsd",
    ".kodi",
    "android",
}
