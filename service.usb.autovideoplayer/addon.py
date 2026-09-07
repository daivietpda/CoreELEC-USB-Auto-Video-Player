# -*- coding: utf-8 -*-
"""Main script entry point for USB Auto Video Player GUI."""

import os
import sys
import time
import xbmc
import xbmcgui
from resources.lib.settings import SettingsManager
from resources.lib.usb_monitor import get_active_usb_mounts
from resources.lib.video_scanner import (
    scan_videos,
    to_relative_path,
    resolve_relative_path,
)
from resources.lib.stream_monitor import check_hls_stream
from resources.lib.player import AutoVideoPlayer
from resources.lib.playlist import (
    play_single_video,
    play_multiple_videos,
    play_hls_stream,
)
from resources.lib.constants import (
    SORT_A_TO_Z,
    MODE_SINGLE_LOOP,
    MODE_MULTIPLE_LOOP,
    MODE_MANUAL,
)
from resources.lib.utils import log, notify, get_string


def handle_manual_selection(settings):
    """Interactive multi-select dialog to configure video list for Manual Mode."""
    mounts = get_active_usb_mounts(settings.is_debug_log_enabled())
    if not mounts:
        xbmcgui.Dialog().ok(
            get_string(30030),
            f"{get_string(30031)}\n({get_string(30041)})",
        )
        return

    mount_list = list(mounts.keys())
    if len(mount_list) == 1:
        chosen_mount = mount_list[0]
    else:
        labels = [f"{mounts[m]['label']} ({m})" for m in mount_list]
        idx = xbmcgui.Dialog().select(get_string(30042), labels)
        if idx < 0:
            return
        chosen_mount = mount_list[idx]

    # Scan video files on selected USB
    files = scan_videos(
        chosen_mount,
        scan_subfolders=settings.is_scan_subfolders(),
        sort_order=SORT_A_TO_Z,
        debug=settings.is_debug_log_enabled(),
    )

    if not files:
        xbmcgui.Dialog().ok(
            get_string(30030),
            f"{get_string(30032)}:\n{chosen_mount}",
        )
        return

    rel_paths = [to_relative_path(chosen_mount, f) for f in files]
    current_saved = set(settings.get_manual_selected_files())
    preselect = [i for i, r in enumerate(rel_paths) if r in current_saved]

    selected_indices = xbmcgui.Dialog().multiselect(
        get_string(30039),
        rel_paths,
        preselect=preselect,
    )

    if selected_indices is not None:
        selected_rel = [rel_paths[i] for i in selected_indices]
        settings.set_manual_selected_files(selected_rel)
        saved_msg = get_string(30040) % len(selected_rel)
        notify(
            get_string(30030),
            saved_msg,
            enabled=True,
        )
        log(f"Saved {len(selected_rel)} manual video selections.")


def start_playback_direct(mount_path, settings):
    """Fallback playback engine executed directly by addon.py if service is idle."""
    log(f"Starting direct playback for mount: {mount_path}")
    mode = settings.get_playback_mode()
    fullscreen = settings.is_fullscreen()
    repeat = settings.is_repeat()
    debug = settings.is_debug_log_enabled()

    player = AutoVideoPlayer(debug=debug)
    player.user_stopped = False

    if mode == MODE_MANUAL:
        selected_rel = settings.get_manual_selected_files()
        if not selected_rel:
            notify(get_string(30030), get_string(30043), enabled=True)
            return

        resolved = [
            resolve_relative_path(mount_path, r)
            for r in selected_rel
            if os.path.isfile(resolve_relative_path(mount_path, r))
        ]
        if not resolved:
            notify(get_string(30030), get_string(30044), enabled=True)
            return

        notify(get_string(30030), get_string(30045) % len(resolved), enabled=True)
        if len(resolved) == 1:
            play_single_video(resolved[0], player, fullscreen, repeat, debug)
        else:
            play_multiple_videos(resolved, player, fullscreen, repeat, debug)
    else:
        videos = scan_videos(
            mount_path,
            scan_subfolders=settings.is_scan_subfolders(),
            sort_order=settings.get_sort_order(),
            debug=debug,
        )
        if not videos:
            notify(get_string(30030), get_string(30032), enabled=True)
            return

        notify(get_string(30030), get_string(30035) % len(videos), enabled=True)
        if mode == MODE_SINGLE_LOOP:
            play_single_video(videos[0], player, fullscreen, repeat, debug)
        else:
            play_multiple_videos(videos, player, fullscreen, repeat, debug)


def handle_manual_play(settings):
    """Triggers immediate playback from USB, notifying service and falling back to direct play."""
    mounts = get_active_usb_mounts(settings.is_debug_log_enabled())
    if not mounts:
        xbmcgui.Dialog().ok(
            get_string(30030),
            get_string(30031),
        )
        return

    mount_list = list(mounts.keys())
    if len(mount_list) == 1:
        chosen_mount = mount_list[0]
    else:
        labels = [f"{mounts[m]['label']} ({m})" for m in mount_list]
        idx = xbmcgui.Dialog().select(get_string(30042), labels)
        if idx < 0:
            return
        chosen_mount = mount_list[idx]

    notify(get_string(30030), get_string(30046), enabled=True)
    log(f"Manual play requested for USB mount: {chosen_mount}")

    win = xbmcgui.Window(10000)
    win.setProperty("service.usb.autovideoplayer.trigger", f"play:{chosen_mount}")

    xbmc.sleep(600)
    pending = win.getProperty("service.usb.autovideoplayer.trigger")
    if pending:
        win.clearProperty("service.usb.autovideoplayer.trigger")
        start_playback_direct(chosen_mount, settings)


def handle_play_hls(settings):
    """Probes and plays configured HLS stream on-demand."""
    hls_url = settings.get_hls_url()
    timeout = settings.get_hls_timeout()
    fullscreen = settings.is_fullscreen()
    debug = settings.is_debug_log_enabled()

    if not hls_url:
        xbmcgui.Dialog().ok(
            get_string(30030),
            "Chưa cấu hình địa chỉ luồng HLS.\n(Vui lòng nhập URL trong Cài đặt)",
        )
        return

    notify(get_string(30030), "Đang kiểm tra kết nối luồng HLS...", enabled=True)
    is_online, reason = check_hls_stream(hls_url, timeout=timeout, debug=debug)

    if not is_online:
        xbmcgui.Dialog().ok(
            get_string(30030),
            f"{get_string(30067)}\n\nChi tiết: {reason}\nURL: {hls_url}\n\n(Không cố gắng phát để tránh treo Kodi)",
        )
        return

    log(f"Manual HLS playback triggered for {hls_url}")
    win = xbmcgui.Window(10000)
    win.setProperty("service.usb.autovideoplayer.trigger", "play_hls")

    xbmc.sleep(600)
    pending = win.getProperty("service.usb.autovideoplayer.trigger")
    if pending:
        win.clearProperty("service.usb.autovideoplayer.trigger")
        player = AutoVideoPlayer(debug=debug)
        play_hls_stream(hls_url, player, fullscreen, debug)


def main():
    settings = SettingsManager()

    options = [
        get_string(30036),  # 1. Chọn video cho Chế độ Thủ công (Mode 3)
        get_string(30037),  # 2. Phát video ngay từ USB (Bắt đầu phát)
        get_string(30069),  # 4. Phát ngay luồng HLS
        get_string(30038),  # 3. Mở Cài đặt Add-on
    ]

    choice = xbmcgui.Dialog().select(get_string(30030), options)
    if choice == 0:
        handle_manual_selection(settings)
    elif choice == 1:
        handle_manual_play(settings)
    elif choice == 2:
        handle_play_hls(settings)
    elif choice == 3:
        settings.addon.openSettings()


if __name__ == "__main__":
    main()
