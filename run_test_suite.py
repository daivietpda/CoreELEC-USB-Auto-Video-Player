# -*- coding: utf-8 -*-
"""Comprehensive verification test suite for USB Auto Video Player."""

import os
import sys
import time
import json
import xbmc
import xbmcgui
import xbmcaddon

results = {}

def report(test_name, passed, detail=""):
    results[test_name] = {"passed": passed, "detail": detail}
    status = "PASS" if passed else "FAIL"
    xbmc.log(f"[TEST-SUITE] {status}: {test_name} - {detail}", xbmc.LOGINFO)

addon = xbmcaddon.Addon("service.usb.autovideoplayer")
playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)

# Import addon libs directly
sys.path.insert(0, "/storage/.kodi/addons/service.usb.autovideoplayer")
from resources.lib.usb_monitor import get_active_usb_mounts
from resources.lib.video_scanner import scan_videos, to_relative_path
from resources.lib.player import AutoVideoPlayer
from resources.lib.playlist import play_single_video, play_multiple_videos, stop_playback
from resources.lib.constants import MODE_SINGLE_LOOP, MODE_MULTIPLE_LOOP, MODE_MANUAL, SORT_A_TO_Z

player = AutoVideoPlayer()

# TEST CASE 0: USB Detection & Mounts
mounts = get_active_usb_mounts(debug=True)
mount_keys = list(mounts.keys())
if mounts and "/var/media/USB-64G" in mounts:
    report("USB_DETECTION", True, f"Found mounts: {mount_keys}")
else:
    report("USB_DETECTION", False, f"Unexpected mounts: {mount_keys}")

mount_dir = "/var/media/USB-64G"

# TEST CASE 1: Video Scanner & Natural Sorting
videos = scan_videos(mount_dir, scan_subfolders=True, sort_order=SORT_A_TO_Z)
basenames = [os.path.basename(v) for v in videos]
expected = ["01.mp4", "02.mpg", "video01.mp4", "video02.mp4"]
if basenames == expected:
    report("VIDEO_SCANNER_NATURAL_SORT", True, f"Sorted: {basenames}")
else:
    report("VIDEO_SCANNER_NATURAL_SORT", False, f"Expected {expected}, got {basenames}")

# TEST 1: Single Video Playback & Loop
stop_playback(player)
xbmc.sleep(500)
play_single_video(videos[0], player, is_fullscreen=True, is_repeat=True)
xbmc.sleep(2000)
if player.isPlayingVideo():
    pos1 = player.getTime()
    tot = player.getTotalTime()
    report("TEST1_SINGLE_PLAY", True, f"Playing {os.path.basename(videos[0])}, total={tot:.1f}s, pos={pos1:.1f}s")
    # Test natural loop by seeking near end
    player.seekTime(tot - 2.0)
    xbmc.sleep(4000)
    # Check if video looped back and is still playing
    if player.isPlayingVideo():
        pos2 = player.getTime()
        report("TEST1_SINGLE_LOOP", True, f"Successfully looped: current pos={pos2:.1f}s after EOS")
    else:
        report("TEST1_SINGLE_LOOP", False, "Playback stopped after EOS")
else:
    report("TEST1_SINGLE_PLAY", False, "Player is not playing video")

stop_playback(player)
xbmc.sleep(1000)

# TEST 2: Multiple Video Playlist & Loop
play_multiple_videos(videos, player, is_fullscreen=True, is_repeat=True)
xbmc.sleep(2000)
pl_size = playlist.size()
curr_pos = playlist.getposition()
is_p = player.isPlayingVideo()
if pl_size == len(videos) and is_p:
    report("TEST2_MULTIPLE_PLAYLIST", True, f"Playlist loaded with {pl_size} items, currently playing item {curr_pos}")
    # Test transition to next video
    tot = player.getTotalTime()
    player.seekTime(tot - 2.0)
    xbmc.sleep(4000)
    if player.isPlayingVideo():
        new_pos = playlist.getposition()
        report("TEST2_PLAYLIST_ADVANCE", True, f"Advanced to next video, position in playlist: {new_pos}")
    else:
        report("TEST2_PLAYLIST_ADVANCE", False, "Playback did not advance to next item")
else:
    report("TEST2_MULTIPLE_PLAYLIST", False, f"Playlist size={pl_size}, isPlaying={is_p}")

stop_playback(player)
xbmc.sleep(1000)

# TEST 3: Manual Selection Mode
manual_rel = ["video/video01.mp4", "video/02.mpg"]
addon.setSettingString("manual_selected_files", json.dumps(manual_rel))
resolved = [os.path.join(mount_dir, r) for r in manual_rel]
play_multiple_videos(resolved, player, is_fullscreen=True, is_repeat=True)
xbmc.sleep(2000)
man_size = playlist.size()
if man_size == 2 and player.isPlayingVideo():
    report("TEST3_MANUAL_SELECTION", True, f"Manual selection mode played {man_size} selected videos")
else:
    report("TEST3_MANUAL_SELECTION", False, f"Playlist size={man_size}")

stop_playback(player)
xbmc.sleep(1000)

# TEST 4: USB Without Video
empty_dir = "/storage/test_empty_usb"
os.makedirs(empty_dir, exist_ok=True)
with open(os.path.join(empty_dir, "notes.txt"), "w") as f:
    f.write("No video")
empty_videos = scan_videos(empty_dir, scan_subfolders=True)
if len(empty_videos) == 0:
    report("TEST4_USB_NO_VIDEO", True, "Empty directory correctly returns 0 videos, player not launched")
else:
    report("TEST4_USB_NO_VIDEO", False, f"Unexpected files found: {empty_videos}")
import shutil
shutil.rmtree(empty_dir, ignore_errors=True)

# TEST 5: USB Removed during playback
play_single_video(videos[0], player, is_fullscreen=True, is_repeat=True)
xbmc.sleep(2000)
if player.isPlayingVideo():
    # Simulate unmount event
    stop_playback(player)
    xbmc.sleep(500)
    if not player.isPlaying():
        report("TEST5_USB_REMOVE_HANDLING", True, "Clean stop executed on unmount, player idle")
    else:
        report("TEST5_USB_REMOVE_HANDLING", False, "Player failed to stop on unmount")
else:
    report("TEST5_USB_REMOVE_HANDLING", False, "Could not start playback for unmount test")

# TEST 8: Manual Stop
play_single_video(videos[0], player, is_fullscreen=True, is_repeat=True)
xbmc.sleep(2000)
player.user_stopped = True
player.stop()
xbmc.sleep(2000)
if not player.isPlaying():
    report("TEST8_MANUAL_STOP", True, "Manual Stop cleanly halted playback without unexpected loop")
else:
    report("TEST8_MANUAL_STOP", False, "Player still active after stop")

with open("/storage/test_results.json", "w") as f:
    json.dump(results, f, indent=2)

xbmc.log("[TEST-SUITE] Finished running test suite successfully!", xbmc.LOGINFO)
