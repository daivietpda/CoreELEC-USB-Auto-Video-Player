# -*- coding: utf-8 -*-
"""Video file scanner with recursive search and natural sorting."""

import os
import random
from resources.lib.constants import (
    SUPPORTED_EXTENSIONS,
    EXCLUDED_DIR_NAMES,
    SORT_A_TO_Z,
    SORT_Z_TO_A,
    SORT_RANDOM,
)
from resources.lib.utils import natural_sort_key, log_debug


def is_video_file(filename):
    """Checks if file has a supported video extension (case-insensitive)."""
    lower = filename.lower()
    return lower.endswith(SUPPORTED_EXTENSIONS) and not filename.startswith(".")


def scan_videos(root_dir, scan_subfolders=True, sort_order=SORT_A_TO_Z, debug=False):
    """
    Scans root_dir for video files.
    Returns sorted list of absolute paths.
    """
    video_files = []
    if not os.path.isdir(root_dir):
        return video_files

    if scan_subfolders:
        for current_root, dirs, files in os.walk(root_dir):
            # Prune excluded and hidden directories
            dirs[:] = [
                d for d in dirs
                if not d.startswith(".") and d.lower() not in EXCLUDED_DIR_NAMES
            ]

            for fname in files:
                if is_video_file(fname):
                    full_path = os.path.normpath(os.path.join(current_root, fname))
                    video_files.append(full_path)
    else:
        try:
            for fname in os.listdir(root_dir):
                full_path = os.path.normpath(os.path.join(root_dir, fname))
                if os.path.isfile(full_path) and is_video_file(fname):
                    video_files.append(full_path)
        except OSError as e:
            log_debug(f"Error listing directory {root_dir}: {e}", debug)

    # Sort files according to setting
    if sort_order == SORT_A_TO_Z:
        video_files.sort(key=lambda p: natural_sort_key(os.path.basename(p)))
    elif sort_order == SORT_Z_TO_A:
        video_files.sort(key=lambda p: natural_sort_key(os.path.basename(p)), reverse=True)
    elif sort_order == SORT_RANDOM:
        random.shuffle(video_files)

    return video_files


def to_relative_path(base_dir, full_path):
    """Converts absolute path to relative path with forward slashes."""
    try:
        rel = os.path.relpath(full_path, base_dir)
        return rel.replace("\\", "/")
    except Exception:
        return os.path.basename(full_path)


def resolve_relative_path(base_dir, rel_path):
    """Resolves relative path against base directory."""
    clean_rel = rel_path.replace("/", os.sep).replace("\\", os.sep)
    return os.path.normpath(os.path.join(base_dir, clean_rel))
