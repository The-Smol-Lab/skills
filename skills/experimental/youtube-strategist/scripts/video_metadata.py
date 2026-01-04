#!/usr/bin/env python3
"""Fetch detailed metadata for YouTube videos using yt-dlp."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any, Dict, List


def _fetch(url: str) -> Dict[str, Any]:
    cmd = [
        "yt-dlp",
        url,
        "--dump-json",
        "--skip-download",
        "--no-warnings",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"yt-dlp failed for {url}")
    return json.loads(result.stdout)


def _normalize(item: Dict[str, Any]) -> Dict[str, Any]:
    view_count = item.get("view_count") or 0
    like_count = item.get("like_count") or 0
    engagement_rate = (like_count / view_count) if view_count else None
    return {
        "video_id": item.get("id"),
        "title": item.get("title"),
        "channel": item.get("uploader") or item.get("channel"),
        "channel_id": item.get("channel_id") or item.get("uploader_id"),
        "view_count": item.get("view_count"),
        "like_count": item.get("like_count"),
        "comment_count": item.get("comment_count"),
        "upload_date": item.get("upload_date"),
        "duration": item.get("duration"),
        "tags": item.get("tags"),
        "categories": item.get("categories"),
        "description": item.get("description"),
        "thumbnail": item.get("thumbnail"),
        "webpage_url": item.get("webpage_url"),
        "engagement_rate": engagement_rate,
    }


def _read_inputs(args: List[str]) -> List[str]:
    if args:
        return args
    data = sys.stdin.read().strip()
    if not data:
        return []
    return [line.strip() for line in data.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch YouTube video metadata.")
    parser.add_argument("urls", nargs="*", help="Video URLs or IDs")
    args = parser.parse_args()

    inputs = _read_inputs(args.urls)
    if not inputs:
        print("[]")
        return 0

    results = []
    for url in inputs:
        item = _fetch(url)
        results.append(_normalize(item))

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
