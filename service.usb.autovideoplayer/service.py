# -*- coding: utf-8 -*-
"""Background service for USB Auto Video Player with HLS stream support."""

import os
import time
import xbmc
import xbmcgui
from resources.lib.constants import (
    ADDON_ID,
    MODE_SINGLE_LOOP,
    MODE_MULTIPLE_LOOP,
    MODE_MANUAL,
    HLS_PRIORITY_FIRST,
    HLS_PRIORITY_USB_FIRST,
    HLS_PRIORITY_ONLY,
)
from resources.lib.settings import SettingsManager
from resources.lib.usb_monitor import USBMonitor, get_active_usb_mounts
from resources.lib.video_scanner import (
    scan_videos,
    resolve_relative_path,
)
from resources.lib.stream_monitor import StreamMonitor
from resources.lib.player import AutoVideoPlayer
from resources.lib.playlist import (
    play_single_video,
    play_multiple_videos,
    play_hls_stream,
    stop_playback,
)
from resources.lib.utils import log, log_debug, log_error, notify, get_string


class USBAutoPlayerService:
    """Core service controller managing lifecycle, state transitions, USB, and HLS playback."""

    def __init__(self):
        self.settings = SettingsManager()
        self.monitor = None
        self.usb_monitor = USBMonitor(debug=self.settings.is_debug_log_enabled())
        self.stream_monitor = StreamMonitor(debug=self.settings.is_debug_log_enabled())
        self.player = None

        # Playback tracking
        self.active_source = "IDLE"  # "HLS", "USB", "USB_FALLBACK", "IDLE"
        self.hls_play_start_time = 0
        self.current_usb_mount = ""
        self.current_playlist_files = []
        self.active_mode = None

        # State tracking: pending insertion debounce
        self.pending_mounts = {}  # {mount_path: timestamp_detected}

    def on_settings_changed(self):
        """Called by monitor when addon settings are modified."""
        log("Settings changed. Reloading configuration.")
        self.settings.reload()
        debug = self.settings.is_debug_log_enabled()
        self.usb_monitor.debug = debug
        self.stream_monitor.debug = debug
        self.stream_monitor.reset()
        if self.player:
            self.player.debug = debug

    def on_hls_interrupted(self, file_path):
        """Called immediately when player detects HLS stream connection was dropped."""
        log(f"HLS stream interrupted: {file_path}")
        if self.active_source == "HLS":
            if (time.time() - self.hls_play_start_time) > 5.0:
                self.active_source = "IDLE"

    def trigger_manual_playback(self, target_mount=None):
        """Forces scan and playback on specified or first active USB mount."""
        mounts = get_active_usb_mounts(self.settings.is_debug_log_enabled())
        if not mounts:
            notify(
                get_string(30030),
                get_string(30031),
                enabled=self.settings.is_notifications_enabled(),
            )
            return

        if not target_mount or target_mount not in mounts:
            target_mount = list(mounts.keys())[0]

        if self.player:
            self.player.user_stopped = False
            self.player.playback_ended = False

        self.active_source = "USB"
        self.start_autoplay_for_mount(target_mount)

    def trigger_hls_playback(self):
        """Forces probe and playback of configured HLS stream."""
        hls_url = self.settings.get_hls_url()
        timeout = self.settings.get_hls_timeout()
        fullscreen = self.settings.is_fullscreen()
        debug = self.settings.is_debug_log_enabled()

        log(f"Manual HLS playback requested for URL: {hls_url}")
        is_online, reason = self.stream_monitor.probe(hls_url, timeout=timeout)

        if is_online:
            notify(get_string(30030), get_string(30066), enabled=self.settings.is_notifications_enabled())
            if self.player:
                self.player.user_stopped = False
                self.player.playback_ended = False
            self.active_source = "HLS"
            self.hls_play_start_time = time.time()
            play_hls_stream(hls_url, self.player, fullscreen, debug)
        else:
            log(f"Cannot play HLS stream: {reason}")
            notify(get_string(30030), f"{get_string(30067)} ({reason})", enabled=True)

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
                    get_string(30030),
                    get_string(30043),
                    enabled=notifications,
                )
                return

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
                    get_string(30030),
                    get_string(30044),
                    enabled=notifications,
                )
                return

            notify(
                get_string(30030),
                get_string(30045) % len(resolved),
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
                    get_string(30030),
                    get_string(30032),
                    enabled=notifications,
                )
                return

            log(f"Found {len(videos)} video(s) on {mount_path}.")
            notify(
                get_string(30030),
                get_string(30035) % len(videos),
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

        if self.current_usb_mount and (self.current_usb_mount == mount_path or not os.path.exists(self.current_usb_mount)):
            log("Active playback was from removed USB. Stopping playback cleanly.")
            stop_playback(self.player)
            if self.player:
                self.player.user_stopped = False
            self.current_usb_mount = ""
            self.current_playlist_files = []
            if self.active_source in ("USB", "USB_FALLBACK"):
                self.active_source = "IDLE"
            notify(
                get_string(30030),
                get_string(30034),
                enabled=notifications,
            )

    def watchdog_check(self):
        """
        Watchdog to ensure seamless repeat looping for USB videos if native Kodi loop
        fails to restart, respecting user explicit stop.
        """
        if not self.settings.is_enabled():
            return

        if self.active_source == "HLS":
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

    def hls_process_cycle(self):
        """Coordinates HLS stream polling, detection, playback, and fallback."""
        if not self.settings.is_enabled() or not self.settings.is_hls_enabled():
            return

        # If user pressed stop manually, do not force-play
        if self.player.user_stopped:
            return

        hls_url = self.settings.get_hls_url()
        if not hls_url:
            return

        priority = self.settings.get_hls_priority()
        retry_interval = self.settings.get_hls_retry_interval()
        timeout = self.settings.get_hls_timeout()
        fullscreen = self.settings.is_fullscreen()
        debug = self.settings.is_debug_log_enabled()
        notifications = self.settings.is_notifications_enabled()

        if self.active_source == "HLS":
            # Check if USB has priority and a USB is attached
            if priority == HLS_PRIORITY_USB_FIRST:
                mounts = self.usb_monitor.active_mounts
                if mounts:
                    log("USB attached while playing HLS. Switching priority to USB.")
                    self.active_source = "USB"
                    first_mount = list(mounts.keys())[0]
                    self.start_autoplay_for_mount(first_mount)
                    return

            # Grace period: allow 5.0 seconds after triggering playback for Kodi to open & buffer stream
            if (time.time() - self.hls_play_start_time) > 5.0 and not self.player.isPlayingVideo():
                log("HLS playback dropped. Probing stream availability...")
                is_online, reason = self.stream_monitor.probe(hls_url, timeout=timeout)
                if is_online:
                    log("HLS stream is still online. Reconnecting...")
                    self.hls_play_start_time = time.time()
                    play_hls_stream(hls_url, self.player, fullscreen, debug)
                else:
                    log(f"HLS stream went OFFLINE ({reason}). Halting playback.")
                    notify(get_string(30030), get_string(30067), enabled=notifications)
                    self.active_source = "IDLE"
                    if priority != HLS_PRIORITY_ONLY:
                        mounts = self.usb_monitor.active_mounts
                        if mounts:
                            log("Switching to USB video fallback.")
                            notify(get_string(30030), get_string(30068), enabled=notifications)
                            self.active_source = "USB_FALLBACK"
                            first_mount = list(mounts.keys())[0]
                            self.start_autoplay_for_mount(first_mount)

        else:
            # self.active_source != "HLS"
            if priority == HLS_PRIORITY_FIRST:
                if self.stream_monitor.should_check(retry_interval):
                    is_online, reason = self.stream_monitor.probe(hls_url, timeout=timeout)
                    if is_online:
                        log(f"HLS stream is ONLINE. Starting HLS stream: {hls_url}")
                        notify(get_string(30030), get_string(30066), enabled=notifications)
                        self.active_source = "HLS"
                        self.hls_play_start_time = time.time()
                        play_hls_stream(hls_url, self.player, fullscreen, debug)
                    else:
                        log_debug(f"HLS stream offline: {reason}. Skipping play.", debug)
                        if self.active_source != "USB_FALLBACK" and not self.player.isPlayingVideo():
                            mounts = self.usb_monitor.active_mounts
                            if mounts:
                                log("HLS stream offline. Falling back to active USB storage.")
                                notify(get_string(30030), get_string(30068), enabled=notifications)
                                self.active_source = "USB_FALLBACK"
                                first_mount = list(mounts.keys())[0]
                                self.start_autoplay_for_mount(first_mount)

            elif priority == HLS_PRIORITY_USB_FIRST:
                mounts = self.usb_monitor.active_mounts
                if not mounts:
                    if self.stream_monitor.should_check(retry_interval):
                        is_online, reason = self.stream_monitor.probe(hls_url, timeout=timeout)
                        if is_online:
                            log("No USB attached. HLS is online, starting stream.")
                            self.active_source = "HLS"
                            self.hls_play_start_time = time.time()
                            play_hls_stream(hls_url, self.player, fullscreen, debug)

            elif priority == HLS_PRIORITY_ONLY:
                if self.stream_monitor.should_check(retry_interval):
                    is_online, reason = self.stream_monitor.probe(hls_url, timeout=timeout)
                    if is_online:
                        log("HLS Only mode: Stream is online, starting playback.")
                        self.active_source = "HLS"
                        self.hls_play_start_time = time.time()
                        play_hls_stream(hls_url, self.player, fullscreen, debug)

    def run(self):
        """Main service loop running with Kodi."""
        log("Service started.")

        class ServiceMonitor(xbmc.Monitor):
            def __init__(self, svc):
                super().__init__()
                self.svc = svc

            def onSettingsChanged(self):
                self.svc.on_settings_changed()

        self.monitor = ServiceMonitor(self)
        self.player = AutoVideoPlayer(
            on_hls_interrupted=self.on_hls_interrupted,
            debug=self.settings.is_debug_log_enabled(),
        )

        # Initial startup scan
        initial_mounts = self.usb_monitor.initial_scan()
        if initial_mounts:
            log(f"Found {len(initial_mounts)} USB mount(s) already attached on startup.")

        # Check HLS stream on startup if HLS is enabled and set to HLS First
        if self.settings.is_enabled() and self.settings.is_hls_enabled() and self.settings.get_hls_priority() == HLS_PRIORITY_FIRST:
            hls_url = self.settings.get_hls_url()
            timeout = self.settings.get_hls_timeout()
            is_online, reason = self.stream_monitor.probe(hls_url, timeout=timeout)
            if is_online:
                log(f"Startup: HLS stream is ONLINE. Launching {hls_url}")
                notify(get_string(30030), get_string(30066), enabled=self.settings.is_notifications_enabled())
                self.active_source = "HLS"
                self.hls_play_start_time = time.time()
                play_hls_stream(hls_url, self.player, self.settings.is_fullscreen(), self.settings.is_debug_log_enabled())
            else:
                log(f"Startup: HLS stream is OFFLINE ({reason}). Will not attempt to play HLS.")
                if initial_mounts and self.settings.is_autoplay_on_insert():
                    log("Startup: Fallback to existing USB drive.")
                    first_mount = list(initial_mounts.keys())[0]
                    self.active_source = "USB_FALLBACK"
                    self.start_autoplay_for_mount(first_mount)
        else:
            # Standard USB startup
            if initial_mounts and self.settings.is_enabled() and self.settings.is_autoplay_on_insert():
                self.monitor.waitForAbort(1.0)
                if not self.monitor.abortRequested():
                    first_mount = list(initial_mounts.keys())[0]
                    self.active_source = "USB"
                    self.start_autoplay_for_mount(first_mount)

        # Main service loop
        while not self.monitor.abortRequested():
            try:
                # Check for manual triggers via Window(10000) property
                win = xbmcgui.Window(10000)
                trigger = win.getProperty("service.usb.autovideoplayer.trigger")
                if trigger:
                    win.clearProperty("service.usb.autovideoplayer.trigger")
                    if trigger == "play_hls":
                        log("Manual play_hls trigger received from Window IPC.")
                        self.trigger_hls_playback()
                    elif trigger.startswith("play"):
                        parts = trigger.split(":", 1)
                        target_mount = parts[1] if len(parts) > 1 and parts[1] else None
                        log(f"Manual play trigger received via Window property: target={target_mount}")
                        self.trigger_manual_playback(target_mount)

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
                            get_string(30030),
                            get_string(30033) % label,
                            enabled=self.settings.is_notifications_enabled(),
                        )
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
                        # If HLS is active with HLS First priority, don't interrupt active HLS stream
                        if self.settings.is_hls_enabled() and self.settings.get_hls_priority() == HLS_PRIORITY_FIRST and self.active_source == "HLS" and self.player.isPlayingVideo():
                            log("USB inserted, but HLS stream has priority and is currently playing. Keeping HLS.")
                        else:
                            if self.settings.is_enabled() and self.settings.is_autoplay_on_insert():
                                self.active_source = "USB"
                                self.start_autoplay_for_mount(m)

                # 2. HLS stream process cycle
                self.hls_process_cycle()

                # 3. Watchdog check for loop continuity
                self.watchdog_check()

            except Exception as e:
                log_error("Error in service main loop", e)

            # Wait 0.5s before next cycle
            self.monitor.waitForAbort(0.5)

        log("Service stopping.")
        if self.player and self.player.isPlaying():
            stop_playback(self.player)


if __name__ == "__main__":
    service = USBAutoPlayerService()
    service.run()
