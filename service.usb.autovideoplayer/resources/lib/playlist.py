# -*- coding: utf-8 -*-
"""Playlist creation and playback control functions."""

import os
import xbmc
import xbmcgui
from resources.lib.utils import log, log_debug, log_error


def create_video_listitem(filepath):
    """
    Creates a Kodi ListItem configured to start from beginning (00:00:00)
    and avoid the Kodi 'Resume from ...' dialog.
    """
    item = xbmcgui.ListItem(path=filepath, offscreen=True)
    try:
        tag = item.getVideoInfoTag()
        tag.setResumePoint(0.0)
    except Exception:
        pass

    item.setProperty("StartOffset", "0.0")
    item.setLabel(os.path.basename(filepath))
    return item


def play_single_video(filepath, player, is_fullscreen=True, is_repeat=True, debug=False):
    """Plays a single video in a 1-item playlist with repeat support."""
    log(f"Playing single video: {os.path.basename(filepath)}")
    try:
        pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        pl.clear()

        item = create_video_listitem(filepath)
        pl.add(filepath, item)

        if player:
            if hasattr(player, "user_stopped"):
                player.user_stopped = False
            if hasattr(player, "playback_ended"):
                player.playback_ended = False
            player.play(pl)

        if is_repeat:
            xbmc.sleep(200)
            xbmc.executebuiltin("PlayerControl(RepeatAll)")

        if is_fullscreen:
            xbmc.sleep(300)
            xbmc.executebuiltin("ActivateWindow(fullscreenvideo)")

        return True
    except Exception as e:
        log_error(f"Failed to play single video {filepath}", e)
        return False


def play_multiple_videos(file_list, player, is_fullscreen=True, is_repeat=True, debug=False):
    """Loads all videos into the Kodi video playlist and starts continuous playback."""
    if not file_list:
        return False

    log(f"Starting playlist with {len(file_list)} video(s)")
    try:
        pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        pl.clear()

        for f in file_list:
            item = create_video_listitem(f)
            pl.add(f, item)
            log_debug(f"Added to playlist: {os.path.basename(f)}", debug)

        if player:
            if hasattr(player, "user_stopped"):
                player.user_stopped = False
            if hasattr(player, "playback_ended"):
                player.playback_ended = False
            player.play(pl)

        if is_repeat:
            xbmc.sleep(200)
            xbmc.executebuiltin("PlayerControl(RepeatAll)")

        if is_fullscreen:
            xbmc.sleep(300)
            xbmc.executebuiltin("ActivateWindow(fullscreenvideo)")

        return True
    except Exception as e:
        log_error("Failed to start video playlist", e)
        return False


def stop_playback(player):
    """Safely stops playback and clears playlist."""
    try:
        if player and player.isPlaying():
            player.stop()
        pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        pl.clear()
        if player:
            if hasattr(player, "user_stopped"):
                player.user_stopped = True
            if hasattr(player, "playback_ended"):
                player.playback_ended = False
    except Exception as e:
        log_error("Failed to cleanly stop playback", e)
