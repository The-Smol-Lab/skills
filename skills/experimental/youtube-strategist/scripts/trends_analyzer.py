#!/usr/bin/env python3
"""Analyze Google Trends for YouTube searches."""

from __future__ import annotations

import argparse
import json
import warnings
from typing import Any, Dict, List

try:
    from pytrends.request import TrendReq
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "pytrends is required. Install with: python -m pip install pytrends"
    ) from exc


def _interest_over_time(pytrends: TrendReq, keywords: List[str], timeframe: str) -> List[Dict[str, Any]]:
    pytrends.build_payload(kw_list=keywords, timeframe=timeframe, gprop="youtube")
    df = pytrends.interest_over_time()
    if df is None or df.empty:
        return []
    df = df.reset_index()
    records = df.to_dict(orient="records")
    for row in records:
        row["date"] = row["date"].isoformat()
        row.pop("isPartial", None)
    return records


def _related_queries(pytrends: TrendReq, keywords: List[str]) -> Dict[str, Any]:
    related = pytrends.related_queries()
    result: Dict[str, Any] = {}
    for kw in keywords:
        entry = related.get(kw, {})
        rising = entry.get("rising")
        top = entry.get("top")
        result[kw] = {
            "rising": rising.to_dict(orient="records") if rising is not None else [],
            "top": top.to_dict(orient="records") if top is not None else [],
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze Google Trends for YouTube.")
    parser.add_argument("keywords", nargs="+", help="Keywords to analyze")
    parser.add_argument("--timeframe", default="today 3-m")
    args = parser.parse_args()

    warnings.filterwarnings("ignore", category=FutureWarning)
    pytrends = TrendReq(hl="en-US", tz=360)
    interest = _interest_over_time(pytrends, args.keywords, args.timeframe)
    related = _related_queries(pytrends, args.keywords)

    output = {
        "keywords": args.keywords,
        "timeframe": args.timeframe,
        "interest_over_time": interest,
        "related_queries": related,
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
