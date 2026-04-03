#!/usr/bin/env python3
"""
YouTube Channel Batch Transcriber
----------------------------------
Fetches all videos from a YouTube channel, transcribes each one using
local Whisper, and saves transcripts + an Obsidian index note.

Usage:
    python batch_channel.py <channel_url>
    python batch_channel.py <channel_url> --model medium --no-timestamps
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
import datetime

# Prioritize Homebrew over conda
os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")


def slugify(title: str) -> str:
    """Convert a video title to a safe filename slug."""
    title = title.lower()
    title = re.sub(r"[^\w\s-]", "", title)
    title = re.sub(r"[\s_]+", "-", title)
    title = re.sub(r"-+", "-", title)
    title = title.strip("-")
    return title[:60].strip("-")


def format_video_filename(upload_date: str, title: str) -> str:
    """Return filename like YT-YYYY-MM-DD-slug.txt from YYYYMMDD date and title."""
    date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    return f"YT-{date}-{slugify(title)}.txt"
