# -*- coding: utf-8 -*-
"""USB storage monitor for CoreELEC / Linux."""

import os
from resources.lib.constants import SYSTEM_MOUNT_PREFIXES
from resources.lib.utils import log_debug, log_error


def is_system_path(path):
    """Checks if a mountpoint belongs to CoreELEC system partitions."""
    norm = os.path.normpath(path)
    if norm == "/" or norm.startswith(SYSTEM_MOUNT_PREFIXES):
        return True
    return False


def is_usb_block_device(dev_path):
    """
    Checks if a block device (/dev/sdX, etc.) is a removable/USB device.
    Uses /sys/block to verify removable status or USB subsystem path.
    """
    if not dev_path.startswith("/dev/"):
        return False

    dev_name = os.path.basename(dev_path)
    # Extract parent disk name (e.g., 'sdb1' -> 'sdb', 'sda' -> 'sda')
    disk_name = "".join([c for c in dev_name if not c.isdigit()])
    sys_block_path = os.path.join("/sys/block", disk_name)

    if not os.path.exists(sys_block_path):
        return False

    try:
        # Check removable attribute
        rem_file = os.path.join(sys_block_path, "removable")
        if os.path.exists(rem_file):
            with open(rem_file, "r") as f:
                if f.read().strip() == "1":
                    return True

        # Check realpath for USB bus
        real_sys = os.path.realpath(sys_block_path)
        if "usb" in real_sys.lower():
            return True
    except Exception:
        pass

    return False


def get_active_usb_mounts(debug=False):
    """
    Scans /proc/mounts for actively mounted external USB storage devices.
    Returns dict: {mount_path: {'device': dev, 'fstype': fstype, 'label': label}}
    """
    mounts = {}
    proc_mounts_file = "/proc/mounts"

    if not os.path.exists(proc_mounts_file):
        log_debug("Proc mounts file does not exist", debug)
        return mounts

    try:
        with open(proc_mounts_file, "r") as f:
            lines = f.readlines()
    except Exception as e:
        log_error("Failed to read /proc/mounts", e)
        return mounts

    for line in lines:
        parts = line.strip().split()
        if len(parts) < 3:
            continue

        dev, mount_point, fstype = parts[0], parts[1], parts[2]

        # Ignore system mounts
        if is_system_path(mount_point):
            continue

        # Ignore pseudo/virtual filesystems
        if fstype in ("tmpfs", "devtmpfs", "proc", "sysfs", "cgroup", "cgroup2", "squashfs", "debugfs", "tracefs"):
            continue

        # Verify device node actually exists in /dev (filters out stale unmount entries)
        if dev.startswith("/dev/") and not os.path.exists(dev):
            continue

        # Check if mount point is located in CoreELEC's external media directory
        # (/var/media or /media) OR device is identified as removable USB
        is_media_path = mount_point.startswith("/var/media/") or mount_point.startswith("/media/")
        is_removable = is_usb_block_device(dev) or dev.startswith("/dev/sd")

        if is_media_path or is_removable:
            # Verify the directory is accessible and currently mounted
            try:
                if os.path.exists(mount_point) and os.path.isdir(mount_point):
                    label = os.path.basename(mount_point.rstrip("/"))
                    mounts[mount_point] = {
                        "device": dev,
                        "fstype": fstype,
                        "label": label,
                    }
            except OSError as e:
                log_debug(f"Mount point {mount_point} not accessible: {e}", debug)

    return mounts


class USBMonitor:
    """Monitors USB mount and unmount events with state tracking."""

    def __init__(self, debug=False):
        self.debug = debug
        self.active_mounts = {}

    def initial_scan(self):
        """Scans and records currently active mounts on startup."""
        self.active_mounts = get_active_usb_mounts(self.debug)
        return dict(self.active_mounts)

    def check_changes(self):
        """
        Polls for mount changes.
        Returns tuple: (added_dict, removed_dict)
        """
        current = get_active_usb_mounts(self.debug)

        added = {
            m: info for m, info in current.items()
            if m not in self.active_mounts
        }
        removed = {
            m: info for m, info in self.active_mounts.items()
            if m not in current
        }

        self.active_mounts = current
        return added, removed
