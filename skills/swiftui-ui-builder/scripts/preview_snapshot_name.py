#!/usr/bin/env python3
"""Generate and optionally save SwiftUI preview snapshot filenames."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

PREVIEW_PATTERN = re.compile(r"#Preview\s*(?:\((.*?)\))?\s*\{", re.DOTALL)
STRING_PATTERN = re.compile(r'"((?:\\.|[^"\\])*)"')


def sanitize_preview_name(name: str) -> str:
    value = re.sub(r"\s+", "-", name.strip())
    value = re.sub(r"[^A-Za-z0-9_-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-_")
    return value


def extract_preview_names(source_text: str) -> list[str | None]:
    names: list[str | None] = []
    for match in PREVIEW_PATTERN.finditer(source_text):
        args = (match.group(1) or "").strip()
        if not args:
            names.append(None)
            continue
        name_match = STRING_PATTERN.search(args)
        if not name_match:
            names.append(None)
            continue
        names.append(name_match.group(1).replace('\\"', '"').strip() or None)
    return names


def build_records(source_file: Path) -> list[dict[str, str | int | None]]:
    text = source_file.read_text(encoding="utf-8")
    raw_names = extract_preview_names(text)
    if not raw_names:
        return []

    normalized: list[str] = []
    for index, raw_name in enumerate(raw_names):
        candidate = sanitize_preview_name(raw_name or "")
        if not candidate:
            candidate = f"Preview{index}"
        normalized.append(candidate)

    counts = Counter(normalized)
    records: list[dict[str, str | int | None]] = []
    for index, (raw_name, normalized_name) in enumerate(zip(raw_names, normalized)):
        unique_name = normalized_name
        if counts[normalized_name] > 1:
            unique_name = f"{normalized_name}-{index}"
        filename = f"{source_file.stem}_{unique_name}.png"
        destination = source_file.parent / filename
        records.append(
            {
                "index": index,
                "raw_name": raw_name,
                "preview_name": unique_name,
                "filename": filename,
                "destination_path": str(destination),
            }
        )
    return records


def print_result(payload: object, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=False))
        return

    if isinstance(payload, list):
        for item in payload:
            print(f"{item['index']}\t{item['preview_name']}\t{item['filename']}")
        return

    if isinstance(payload, dict):
        print(payload["destination_path"])
        return

    print(payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate and optionally save SwiftUI preview snapshot filenames."
    )
    parser.add_argument("--source", required=True, help="Path to Swift source file")
    parser.add_argument("--index", type=int, help="Preview index to resolve")
    parser.add_argument("--list", action="store_true", help="List all preview entries")
    parser.add_argument("--snapshot", help="Path of RenderPreview snapshot PNG to copy")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_file = Path(args.source)

    if not source_file.exists():
        print(f"Source file not found: {source_file}", file=sys.stderr)
        return 1
    if source_file.suffix != ".swift":
        print(f"Source file must be a .swift file: {source_file}", file=sys.stderr)
        return 1

    records = build_records(source_file)
    if not records:
        print(f"No #Preview macros found in {source_file}", file=sys.stderr)
        return 1

    if args.list:
        print_result(records, args.format)
        return 0

    if args.index is None:
        print("Provide --index (or use --list).", file=sys.stderr)
        return 1
    if args.index < 0 or args.index >= len(records):
        print(
            f"Preview index out of range: {args.index} (available 0..{len(records)-1})",
            file=sys.stderr,
        )
        return 1

    selected = records[args.index]
    destination_path = Path(str(selected["destination_path"]))

    if args.snapshot:
        snapshot_path = Path(args.snapshot)
        if not snapshot_path.exists():
            print(f"Snapshot not found: {snapshot_path}", file=sys.stderr)
            return 1
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(snapshot_path, destination_path)

    print_result(selected, args.format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
