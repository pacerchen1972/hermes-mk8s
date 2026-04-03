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
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

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


def get_next_prj_number(projects_dir: Path) -> int:
    """Scan PRJ-PERSONAL-NNN-* files and return the next available number."""
    numbers = []
    for f in projects_dir.glob("PRJ-PERSONAL-*-*.md"):
        m = re.match(r"PRJ-PERSONAL-(\d+)-", f.name)
        if m:
            numbers.append(int(m.group(1)))
    return max(numbers) + 1 if numbers else 1


def find_or_create_project_note(vault_dir: Path) -> Path:
    """Return path to the vongoval project index note, creating it if needed."""
    projects_dir = vault_dir / "200 - Projects" / "Personal"
    projects_dir.mkdir(parents=True, exist_ok=True)

    # Create transcripts subfolder
    (projects_dir / "vongoval").mkdir(exist_ok=True)

    # Return existing note if found
    existing = list(projects_dir.glob("*vongoval-research.md"))
    if existing:
        return existing[0]

    prj_num = get_next_prj_number(projects_dir)
    note_path = projects_dir / f"PRJ-PERSONAL-{prj_num:03d}-vongoval-research.md"
    today = datetime.date.today().isoformat()

    content = f"""---
title: "vongoval Research"
type: project
tags: [youtube, research, vongoval]
updated: {today}
---

# vongoval Research

YouTube channel: https://www.youtube.com/@vongoval/videos

## Videos

"""
    note_path.write_text(content, encoding="utf-8")
    return note_path


def append_to_index(note_path: Path, title: str, filename: str, date_str: str) -> None:
    """Append a markdown link entry to the project index note (idempotent)."""
    content = note_path.read_text(encoding="utf-8")
    link = f"- [{title}](vongoval/{filename}) — {date_str}"
    if link in content:
        return
    if not content.endswith("\n"):
        content += "\n"
    content += link + "\n"
    note_path.write_text(content, encoding="utf-8")


def fetch_channel_videos(channel_url: str) -> list:
    """Return list of video dicts from a YouTube channel using yt-dlp."""
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--no-warnings",
        channel_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("yt-dlp error:\n" + result.stderr, file=sys.stderr)
        sys.exit(1)

    videos = []
    for line in result.stdout.strip().splitlines():
        if line.strip():
            try:
                videos.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return videos
