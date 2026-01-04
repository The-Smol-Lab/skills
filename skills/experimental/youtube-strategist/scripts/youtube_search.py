#!/usr/bin/env python3
"""Search YouTube by keyword using yt-dlp and return metadata."""

from __future__ import annotations

import argparse
import json
import subprocess
from typing import Any, Dict, List


def _run_search(keyword: str, max_results: int) -> List[Dict[str, Any]]:
    query = f"ytsearch{max_results}:{keyword}"
    cmd = [
        "yt-dlp",
        query,
        "--dump-json",
        "--skip-download",
        "--no-warnings",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "yt-dlp failed")

    items = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        items.append(json.loads(line))
    return items


def _normalize(item: Dict[str, Any]) -> Dict[str, Any]:
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
        "description": (item.get("description") or "")[:500],
        "thumbnail": item.get("thumbnail"),
        "webpage_url": item.get("webpage_url"),
    }


def _sort_items(items: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
    if sort_by == "views":
        return sorted(items, key=lambda x: x.get("view_count") or 0, reverse=True)
    if sort_by == "date":
        return sorted(items, key=lambda x: int(x.get("upload_date") or 0), reverse=True)
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Search YouTube by keyword.")
    parser.add_argument("keyword", help="Search keyword")
    parser.add_argument("--max-results", type=int, default=10)
    parser.add_argument("--sort-by", choices=["relevance", "views", "date"], default="relevance")
    args = parser.parse_args()

    items = _run_search(args.keyword, args.max_results)
    normalized = [_normalize(item) for item in items]
    sorted_items = _sort_items(normalized, args.sort_by)

    print(json.dumps(sorted_items, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
