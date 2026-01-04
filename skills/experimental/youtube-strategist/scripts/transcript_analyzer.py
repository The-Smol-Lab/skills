#!/usr/bin/env python3
"""Analyze a transcript for hooks, topics, and structure cues."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from typing import List

STOPWORDS = {
    "the",
    "and",
    "a",
    "to",
    "of",
    "in",
    "is",
    "it",
    "that",
    "for",
    "on",
    "you",
    "with",
    "as",
    "this",
    "are",
    "be",
    "or",
    "we",
    "i",
    "they",
    "was",
    "at",
    "by",
    "from",
    "an",
    "have",
    "has",
    "but",
    "not",
    "if",
    "so",
    "your",
    "our",
    "their",
    "my",
}


def _read_text(path: str | None) -> str:
    if path:
        return open(path, "r", encoding="utf-8").read()
    return sys.stdin.read()


def _tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Z0-9']+", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def _hook_excerpt(text: str, word_limit: int = 120) -> str:
    words = text.strip().split()
    return " ".join(words[:word_limit])


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a transcript.")
    parser.add_argument("--file", help="Path to transcript text")
    parser.add_argument("--top", type=int, default=15, help="Top keywords count")
    args = parser.parse_args()

    text = _read_text(args.file).strip()
    if not text:
        print("{}")
        return 0

    tokens = _tokenize(text)
    counts = Counter(tokens)
    top_keywords = counts.most_common(args.top)

    output = {
        "word_count": len(text.split()),
        "top_keywords": [{"keyword": k, "count": v} for k, v in top_keywords],
        "hook_excerpt": _hook_excerpt(text),
        "section_count_estimate": max(1, len(text.split()) // 350),
    }

    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
