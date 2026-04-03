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


def download_audio(url: str, output_path: str) -> None:
    """Download audio from a YouTube URL. Raises RuntimeError on failure."""
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--no-playlist",
        "--output", output_path,
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr.strip()}")


def transcribe_audio(audio_path: str, model_name: str, timestamps: bool) -> str:
    """Thin wrapper around transcribe() from transcribe.py for easy mocking in tests."""
    from transcribe import transcribe
    return transcribe(audio_path, model_name, timestamps=timestamps)


def process_video(video: dict, output_dir: Path, note_path: Path, model: str, timestamps: bool) -> bool:
    """Download, transcribe, and save one video. Returns False if skipped."""
    title = video["title"]
    upload_date = video.get("upload_date", "00000000")
    url = video.get("webpage_url") or f"https://www.youtube.com/watch?v={video['id']}"

    filename = format_video_filename(upload_date, title)
    txt_path = output_dir / filename

    if txt_path.exists():
        print(f"  ⏭  Skipping (already done): {title}")
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio.mp3")
        download_audio(url, audio_path)
        transcript = transcribe_audio(audio_path, model, timestamps)

    txt_path.write_text(transcript, encoding="utf-8")

    date_str = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    append_to_index(note_path, title, filename, date_str)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Batch transcribe all videos from a YouTube channel into Obsidian notes."
    )
    parser.add_argument("channel_url", help="YouTube channel URL (e.g. https://www.youtube.com/@vongoval/videos)")
    parser.add_argument(
        "--model",
        default="medium",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: medium)",
    )
    parser.add_argument(
        "--no-timestamps",
        action="store_true",
        help="Save plain text transcripts without timestamps",
    )
    parser.add_argument(
        "--vault",
        default=os.path.expanduser("~/Documents/Pandarve"),
        help="Path to Obsidian vault (default: ~/Documents/Pandarve)",
    )
    args = parser.parse_args()

    vault_dir = Path(args.vault)
    if not vault_dir.exists():
        print(f"Error: vault directory not found: {vault_dir}", file=sys.stderr)
        sys.exit(1)

    print("📋 Fetching channel video list...")
    videos = fetch_channel_videos(args.channel_url)
    total = len(videos)
    print(f"   Found {total} videos\n")

    note_path = find_or_create_project_note(vault_dir)
    output_dir = note_path.parent / "vongoval"
    output_dir.mkdir(exist_ok=True)
    print(f"📁 Index note: {note_path}\n")

    failures = []
    skipped = 0
    processed = 0

    for i, video in enumerate(videos, 1):
        title = video.get("title", "Unknown")
        print(f"[{i}/{total}] {title}")
        try:
            result = process_video(video, output_dir, note_path, args.model, timestamps=not args.no_timestamps)
            if result:
                processed += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            failures.append((title, str(e)))

    print(f"\n✅ Done — {processed} transcribed, {skipped} skipped, {len(failures)} failed.")
    if failures:
        print("\nFailed videos:")
        for title, err in failures:
            print(f"  - {title}: {err}")


if __name__ == "__main__":
    main()
