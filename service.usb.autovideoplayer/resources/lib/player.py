# -*- coding: utf-8 -*-
"""Custom Kodi Player to track playback lifecycle and user stop events."""

import time
import xbmc
from resources.lib.utils import log, log_debug, log_error


class AutoVideoPlayer(xbmc.Player):
    """
    Subclasses xbmc.Player to accurately detect when playback ends naturally
    versus when the user explicitly stops playback, supporting both local files
    and live HLS streams.
    """

    def __init__(self, on_ended=None, on_stopped=None, on_started=None, on_error=None, on_hls_interrupted=None, debug=False):
        super().__init__()
        self.on_ended_cb = on_ended
        self.on_stopped_cb = on_stopped
        self.on_started_cb = on_started
        self.on_error_cb = on_error
        self.on_hls_interrupted_cb = on_hls_interrupted
        self.debug = debug

        self.is_playing_video = False
        self.is_playing_hls = False
        self.user_stopped = False
        self.playback_ended = False
        self.playback_ended_time = 0
        self.current_file = ""

    def onAVStarted(self):
        self.is_playing_video = True
        self.user_stopped = False
        self.playback_ended = False
        try:
            self.current_file = self.getPlayingFile()
            if self.current_file.startswith("http://") or self.current_file.startswith("https://"):
                self.is_playing_hls = True
        except Exception:
            pass
        log_debug(f"Player onAVStarted: {self.current_file} (is_hls={self.is_playing_hls})", self.debug)
        if self.on_started_cb:
            try:
                self.on_started_cb(self.current_file)
            except Exception as e:
                log_error("Error in on_started_cb", e)

    def onPlayBackEnded(self):
        """Called when video finishes playing naturally."""
        log_debug(f"Player onPlayBackEnded: {self.current_file} (is_hls={self.is_playing_hls})", self.debug)
        self.is_playing_video = False
        self.playback_ended = True
        self.playback_ended_time = time.time()

        if self.is_playing_hls:
            self.is_playing_hls = False
            log("HLS stream ended or connection dropped.")
            if self.on_hls_interrupted_cb:
                try:
                    self.on_hls_interrupted_cb(self.current_file)
                except Exception as e:
                    log_error("Error in on_hls_interrupted_cb", e)

        # Natural end does NOT count as user stopped
        if self.on_ended_cb:
            try:
                self.on_ended_cb(self.current_file)
            except Exception as e:
                log_error("Error in on_ended_cb", e)

    def onPlayBackStopped(self):
        """Called when user presses STOP or playback is manually aborted."""
        log("User stopped playback. Autoplay session suspended.")
        self.is_playing_video = False
        self.is_playing_hls = False
        self.user_stopped = True
        self.playback_ended = False
        if self.on_stopped_cb:
            try:
                self.on_stopped_cb(self.current_file)
            except Exception as e:
                log_error("Error in on_stopped_cb", e)

    def onPlayBackError(self):
        """Called on playback error."""
        log_error(f"Playback error occurred for: {self.current_file} (is_hls={self.is_playing_hls})")
        self.is_playing_video = False
        self.playback_ended = False

        if self.is_playing_hls:
            self.is_playing_hls = False
            if self.on_hls_interrupted_cb:
                try:
                    self.on_hls_interrupted_cb(self.current_file)
                except Exception as e:
                    log_error("Error in on_hls_interrupted_cb", e)

        if self.on_error_cb:
            try:
                self.on_error_cb(self.current_file)
            except Exception as e:
                log_error("Error in on_error_cb", e)
