# -*- coding: utf-8 -*-
"""Main script entry point for USB Auto Video Player GUI."""

import sys
import xbmc
import xbmcgui
from resources.lib.settings import SettingsManager
from resources.lib.usb_monitor import get_active_usb_mounts
from resources.lib.video_scanner import scan_videos, to_relative_path
from resources.lib.constants import SORT_A_TO_Z
from resources.lib.utils import log, notify


def handle_manual_selection(settings):
    """Interactive multi-select dialog to configure video list for Manual Mode."""
    mounts = get_active_usb_mounts(settings.is_debug_log_enabled())
    if not mounts:
        xbmcgui.Dialog().ok(
            "USB Auto Video Player",
            "Không tìm thấy thiết bị USB nào đang cắm.\n(Vui lòng cắm USB trước khi chọn video)."
        )
        return

    mount_list = list(mounts.keys())
    if len(mount_list) == 1:
        chosen_mount = mount_list[0]
    else:
        labels = [f"{mounts[m]['label']} ({m})" for m in mount_list]
        idx = xbmcgui.Dialog().select("Chọn thiết bị USB", labels)
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
            "USB Auto Video Player",
            f"Không tìm thấy file video hợp lệ trên USB:\n{chosen_mount}"
        )
        return

    rel_paths = [to_relative_path(chosen_mount, f) for f in files]
    current_saved = set(settings.get_manual_selected_files())
    preselect = [i for i, r in enumerate(rel_paths) if r in current_saved]

    selected_indices = xbmcgui.Dialog().multiselect(
        "Chọn video cho Chế độ Thủ công (Mode 3)",
        rel_paths,
        preselect=preselect,
    )

    if selected_indices is not None:
        selected_rel = [rel_paths[i] for i in selected_indices]
        settings.set_manual_selected_files(selected_rel)
        notify(
            "USB Auto Video Player",
            f"Đã lưu {len(selected_rel)} video đã chọn.",
            enabled=True,
        )
        log(f"Saved {len(selected_rel)} manual video selections.")


def handle_manual_play():
    """Signals service to trigger an immediate scan & playback."""
    xbmc.executebuiltin("NotifyAll(service.usb.autovideoplayer, manual_trigger)")
    notify("USB Auto Video Player", "Đang quét và phát video từ USB...", enabled=True)


def main():
    settings = SettingsManager()

    options = [
        "1. Chọn video cho Chế độ Thủ công (Mode 3)",
        "2. Phát video ngay từ USB (Test Playback)",
        "3. Mở Cài đặt Add-on",
    ]

    choice = xbmcgui.Dialog().select("USB Auto Video Player", options)
    if choice == 0:
        handle_manual_selection(settings)
    elif choice == 1:
        handle_manual_play()
    elif choice == 2:
        settings.addon.openSettings()


if __name__ == "__main__":
    main()
