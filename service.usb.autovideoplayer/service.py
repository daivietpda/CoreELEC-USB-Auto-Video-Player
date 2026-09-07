# -*- coding: utf-8 -*-
"""Background service for USB Auto Video Player."""

import os
import time
import xbmc
from resources.lib.constants import (
    ADDON_ID,
    MODE_SINGLE_LOOP,
    MODE_MULTIPLE_LOOP,
    MODE_MANUAL,
)
from resources.lib.settings import SettingsManager
from resources.lib.usb_monitor import USBMonitor, get_active_usb_mounts
from resources.lib.video_scanner import (
    scan_videos,
    resolve_relative_path,
)
from resources.lib.player import AutoVideoPlayer
from resources.lib.playlist import (
    play_single_video,
    play_multiple_videos,
    stop_playback,
)
from resources.lib.utils import log, log_debug, log_error, notify


class USBAutoPlayerService:
    """Core service controller managing lifecycle, state transitions, and playback."""

    def __init__(self):
        self.settings = SettingsManager()
        self.monitor = None
        self.usb_monitor = USBMonitor(debug=self.settings.is_debug_log_enabled())
        self.player = None

        # Current playback tracking
        self.current_usb_mount = ""
        self.current_playlist_files = []
        self.active_mode = None

        # State tracking: pending insertion debounce
        self.pending_mounts = {}  # {mount_path: timestamp_detected}

    def on_settings_changed(self):
        """Called by monitor when addon settings are modified."""
        log("Settings changed. Reloading configuration.")
        self.settings.reload()
        self.usb_monitor.debug = self.settings.is_debug_log_enabled()
        if self.player:
            self.player.debug = self.settings.is_debug_log_enabled()

    def on_kodi_notification(self, sender, method, data):
        """Catches custom notification triggers from addon.py."""
        if sender == ADDON_ID and method == "manual_trigger":
            log("Manual trigger received from user interface.")
            self.trigger_manual_playback()

    def trigger_manual_playback(self):
        """Forces scan and playback on first active USB mount."""
        mounts = get_active_usb_mounts(self.settings.is_debug_log_enabled())
        if not mounts:
            notify(
                "USB Auto Video Player",
                "Không tìm thấy USB nào đang cắm.",
                enabled=self.settings.is_notifications_enabled(),
            )
            return
        # Use first available mount
        first_mount = list(mounts.keys())[0]
        if self.player:
            self.player.user_stopped = False
            self.player.playback_ended = False
        self.start_autoplay_for_mount(first_mount)

    def start_autoplay_for_mount(self, mount_path):
        """Scans video files on mount_path and starts playback according to active mode."""
        if not self.settings.is_enabled():
            log_debug("Add-on is disabled in settings. Skipping autoplay.", self.settings.is_debug_log_enabled())
            return

        if not os.path.isdir(mount_path):
            log_debug(f"Mount path is not a directory: {mount_path}", self.settings.is_debug_log_enabled())
            return

        label = os.path.basename(mount_path.rstrip("/"))
        log(f"Processing USB volume: '{label}' ({mount_path})")

        mode = self.settings.get_playback_mode()
        scan_subfolders = self.settings.is_scan_subfolders()
        sort_order = self.settings.get_sort_order()
        fullscreen = self.settings.is_fullscreen()
        repeat = self.settings.is_repeat()
        notifications = self.settings.is_notifications_enabled()
        debug = self.settings.is_debug_log_enabled()

        if mode == MODE_MANUAL:
            # Mode 3: Manual selection
            selected_rel = self.settings.get_manual_selected_files()
            if not selected_rel:
                log("Mode 3 active but no video files are configured in settings.")
                notify(
                    "USB Auto Video Player",
                    "Chưa chọn video cho Chế độ Thủ công (Mode 3).",
                    enabled=notifications,
                )
                return

            # Map relative paths to current mount point
            resolved = []
            for rel in selected_rel:
                full_p = resolve_relative_path(mount_path, rel)
                if os.path.isfile(full_p):
                    resolved.append(full_p)
                else:
                    log_debug(f"Manual file not found on USB: {full_p}", debug)

            if not resolved:
                log(f"None of the {len(selected_rel)} manual videos were found on {mount_path}.")
                notify(
                    "USB Auto Video Player",
                    "Không tìm thấy video đã chọn trên USB này.",
                    enabled=notifications,
                )
                return

            notify(
                "USB Auto Video Player",
                f"Phát {len(resolved)} video đã chọn.",
                enabled=notifications,
            )
            self.current_usb_mount = mount_path
            self.current_playlist_files = list(resolved)
            self.active_mode = mode

            if len(resolved) == 1:
                play_single_video(resolved[0], self.player, fullscreen, repeat, debug)
            else:
                play_multiple_videos(resolved, self.player, fullscreen, repeat, debug)

        else:
            # Scan all videos on mount
            videos = scan_videos(
                mount_path,
                scan_subfolders=scan_subfolders,
                sort_order=sort_order,
                debug=debug,
            )

            if not videos:
                log(f"No supported video files (.mp4, .mpg, ...) found on {mount_path}.")
                notify(
                    "USB Auto Video Player",
                    "Không tìm thấy video trên USB.",
                    enabled=notifications,
                )
                return

            log(f"Found {len(videos)} video(s) on {mount_path}.")
            notify(
                "USB Auto Video Player",
                f"Tìm thấy {len(videos)} video. Bắt đầu phát...",
                enabled=notifications,
            )

            self.current_usb_mount = mount_path
            self.active_mode = mode

            if mode == MODE_SINGLE_LOOP:
                # Mode 1: Single Video Loop
                if len(videos) > 1:
                    log(f"Mode 1 active: USB has {len(videos)} videos. Playing first sorted video: {os.path.basename(videos[0])}")
                self.current_playlist_files = [videos[0]]
                play_single_video(videos[0], self.player, fullscreen, repeat, debug)

            elif mode == MODE_MULTIPLE_LOOP:
                # Mode 2: Multiple Video Loop
                self.current_playlist_files = list(videos)
                play_multiple_videos(videos, self.player, fullscreen, repeat, debug)

    def handle_unmounted(self, mount_path):
        """Handles safe removal of USB storage."""
        log(f"USB storage unmounted/removed: {mount_path}")
        notifications = self.settings.is_notifications_enabled()

        # If currently playing media located on removed USB
        if self.current_usb_mount and (self.current_usb_mount == mount_path or not os.path.exists(self.current_usb_mount)):
            log("Active playback was from removed USB. Stopping playback cleanly.")
            stop_playback(self.player)
            self.current_usb_mount = ""
            self.current_playlist_files = []
            notify(
                "USB Auto Video Player",
                "Đã rút USB. Dừng phát video.",
                enabled=notifications,
            )

    def watchdog_check(self):
        """
        Watchdog to ensure seamless repeat looping if native Kodi loop
        fails to restart, respecting user explicit stop.
        """
        if not self.settings.is_enabled():
            return

        if not self.settings.is_repeat():
            return

        if not self.current_usb_mount or not self.current_playlist_files:
            return

        # If user explicitly pressed STOP, do NOT restart
        if self.player.user_stopped:
            return

        # Check if playback finished naturally and has been idle for >= 2 seconds
        if self.player.playback_ended and not self.player.isPlayingVideo():
            if time.time() - self.player.playback_ended_time >= 2.0:
                if os.path.isdir(self.current_usb_mount):
                    log("Watchdog: Playback reached natural end. Re-triggering repeat loop.")
                    self.player.playback_ended = False
                    fullscreen = self.settings.is_fullscreen()
                    repeat = self.settings.is_repeat()
                    debug = self.settings.is_debug_log_enabled()

                    if len(self.current_playlist_files) == 1:
                        play_single_video(
                            self.current_playlist_files[0],
                            self.player,
                            fullscreen,
                            repeat,
                            debug,
                        )
                    else:
                        play_multiple_videos(
                            self.current_playlist_files,
                            self.player,
                            fullscreen,
                            repeat,
                            debug,
                        )

    def run(self):
        """Main service loop running with Kodi."""
        log("Service started.")

        class ServiceMonitor(xbmc.Monitor):
            def __init__(self, svc):
                super().__init__()
                self.svc = svc

            def onSettingsChanged(self):
                self.svc.on_settings_changed()

            def onNotification(self, sender, method, data):
                self.svc.on_kodi_notification(sender, method, data)

        self.monitor = ServiceMonitor(self)
        self.player = AutoVideoPlayer(
            debug=self.settings.is_debug_log_enabled()
        )

        # Initial scan on startup (Case: USB already plugged in before Kodi boots)
        initial_mounts = self.usb_monitor.initial_scan()
        if initial_mounts:
            log(f"Found {len(initial_mounts)} USB mount(s) already attached on startup.")
            if self.settings.is_enabled() and self.settings.is_autoplay_on_insert():
                # Allow Kodi startup to settle
                self.monitor.waitForAbort(1.0)
                if not self.monitor.abortRequested():
                    first_mount = list(initial_mounts.keys())[0]
                    self.start_autoplay_for_mount(first_mount)

        # Main service loop
        while not self.monitor.abortRequested():
            try:
                # 1. Check for mount additions and removals
                added, removed = self.usb_monitor.check_changes()

                # Handle removed USBs
                for rm_mount in removed:
                    if rm_mount in self.pending_mounts:
                        del self.pending_mounts[rm_mount]
                    self.handle_unmounted(rm_mount)

                # Queue new USBs for debounce delay
                if added:
                    delay = self.settings.get_usb_delay()
                    now = time.time()
                    for add_mount in added:
                        label = os.path.basename(add_mount.rstrip("/"))
                        log(f"Detected USB insertion: '{label}' ({add_mount}). Delaying {delay}s for mount stability.")
                        notify(
                            "USB Auto Video Player",
                            f"Phát hiện USB: {label}",
                            enabled=self.settings.is_notifications_enabled(),
                        )
                        # Reset user_stopped flag for newly plugged USB
                        self.player.user_stopped = False
                        self.player.playback_ended = False
                        self.pending_mounts[add_mount] = now + delay

                # Process pending mounts whose delay has elapsed
                if self.pending_mounts:
                    now = time.time()
                    ready_mounts = [
                        m for m, ready_time in self.pending_mounts.items()
                        if now >= ready_time
                    ]
                    for m in ready_mounts:
                        del self.pending_mounts[m]
                        if self.settings.is_enabled() and self.settings.is_autoplay_on_insert():
                            self.start_autoplay_for_mount(m)

                # 2. Watchdog check for loop continuity
                self.watchdog_check()

            except Exception as e:
                log_error("Error in service main loop", e)

            # Wait 1 second before next cycle (clean, instant exit on Kodi shutdown)
            self.monitor.waitForAbort(1.0)

        log("Service stopping.")
        if self.player and self.player.isPlaying():
            stop_playback(self.player)


if __name__ == "__main__":
    service = USBAutoPlayerService()
    service.run()
