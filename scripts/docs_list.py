#!/usr/bin/env python3
"""List active project documentation and its routing metadata."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
WORKING_MATERIAL_DIRS = {"plans", "specs"}
HISTORICAL_DIRS = {"archive", "legacy"}


@dataclass(frozen=True)
class DocMetadata:
    """Small front-matter contract used to route agent reading."""

    summary: str
    read_when: list[str]


def walk_markdown_files(root: Path, *, include_all: bool = False) -> list[Path]:
    """Return Markdown files visible in the requested discovery mode."""
    files: list[Path] = []
    for path in root.rglob("*.md"):
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if any(part in WORKING_MATERIAL_DIRS for part in relative.parts):
            continue
        if not include_all and any(
            part in HISTORICAL_DIRS for part in relative.parts
        ):
            continue
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def extract_metadata(path: Path) -> tuple[DocMetadata | None, str | None]:
    """Read the summary and routing hints from one Markdown document."""
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        return None, "missing front matter"

    end_index = content.find("\n---\n", 4)
    if end_index == -1:
        return None, "unterminated front matter"

    summary: str | None = None
    read_when: list[str] = []
    in_read_when = False
    for raw_line in content[4:end_index].splitlines():
        line = raw_line.strip()
        if line.startswith("summary:"):
            summary = line.split(":", 1)[1].strip().strip("'\"")
            in_read_when = False
        elif line.startswith("read_when:"):
            in_read_when = True
        elif in_read_when and line.startswith("- "):
            read_when.append(line[2:].strip())
        elif line:
            in_read_when = False

    if not summary:
        return None, "summary is missing or empty"
    if not read_when:
        return None, "read_when is missing or empty"
    return DocMetadata(summary=summary, read_when=read_when), None


def validate_active_docs(root: Path) -> list[str]:
    """Return metadata errors for active, non-historical documents."""
    errors: list[str] = []
    for path in walk_markdown_files(root):
        _, error = extract_metadata(path)
        if error:
            errors.append(f"{path.relative_to(root).as_posix()}: {error}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="List ACC telemetry documentation metadata."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="include legacy and archive docs",
    )
    args = parser.parse_args(argv)

    errors = validate_active_docs(DOCS_DIR)
    for path in walk_markdown_files(DOCS_DIR, include_all=args.all):
        relative = path.relative_to(DOCS_DIR).as_posix()
        metadata, error = extract_metadata(path)
        if error:
            print(f"{relative} - [{error}]")
            continue
        print(f"{relative} - {metadata.summary}")
        print(f"  Read when: {'; '.join(metadata.read_when)}")

    if errors:
        print("\nActive documentation metadata errors:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
