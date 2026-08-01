#!/usr/bin/env python3
"""Minimal repository consistency checks without third-party packages."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "content" / "catalog.json"
REQUIRED_TOP_LEVEL = [
    ROOT / "README.md",
    ROOT / "ROADMAP.md",
    ROOT / "CITATION.cff",
    ROOT / "docs" / "legacy" / "forum-191-index.md",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in REQUIRED_TOP_LEVEL:
        if not path.is_file():
            fail(f"missing required file: {path.relative_to(ROOT)}")

    try:
        data = json.loads(CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read catalog: {exc}")

    items = data.get("items")
    if not isinstance(items, list):
        fail("catalog.items must be a list")

    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            fail(f"catalog item {index} is not an object")
        content_id = item.get("id")
        title = item.get("title")
        if not isinstance(content_id, str) or not content_id.startswith("KONTAKTS-UNO-"):
            fail(f"invalid content id at item {index}: {content_id!r}")
        if content_id in seen:
            fail(f"duplicate content id: {content_id}")
        seen.add(content_id)
        if not isinstance(title, str) or not title.strip():
            fail(f"missing title for {content_id}")
        github_path = item.get("github_path")
        if github_path and not (ROOT / github_path).exists():
            fail(f"github_path does not exist for {content_id}: {github_path}")

    print(f"OK: {len(items)} catalog items, {len(seen)} unique IDs")


if __name__ == "__main__":
    main()
