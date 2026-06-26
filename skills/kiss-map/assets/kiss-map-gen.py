#!/usr/bin/env python3
"""KISS map generator — writes .kiss/inert.md, the project's distilled index.

Dependency-free (Python 3 stdlib). Heuristic and multi-language: it harvests
declaration signatures, banner sections, and one-line synopses into a compact
markdown map the agent consults FIRST (grep it; don't read it whole).

It is a STRUCTURAL index — exact and deterministic, not semantic. It reports
what exists and where, so the agent never has to guess or grep the whole tree.

Usage:
    python kiss-map-gen.py <repo-root> [--out PATH]   (default <root>/.kiss/inert.md)
"""
import argparse
import os
import re
import sys

EXCLUDE_DIRS = {
    ".git", "node_modules", "bin", "obj", "dist", "build", "out",
    ".vs", ".venv", "venv", "__pycache__", "vendor", "packages", ".kiss",
}

# Declaration patterns by extension group. Each captures the symbol name in group(1).
COMMON = [
    re.compile(r"^\s*(?:export\s+)?(?:public\s+|private\s+|protected\s+|internal\s+|static\s+|abstract\s+|sealed\s+|partial\s+|final\s+)*"
               r"(?:class|interface|struct|enum|trait)\s+(\w+)"),
]
PATTERNS = {
    "py": [re.compile(r"^\s*(?:async\s+)?def\s+(\w+)"),
           re.compile(r"^\s*class\s+(\w+)")],
    "js": [re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)"),
           re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*=>"),
           re.compile(r"^\s*(?:export\s+)?(?:default\s+)?class\s+(\w+)")],
    "cs": COMMON + [re.compile(r"^\s*(?:public|private|protected|internal)\s+(?:static\s+|async\s+|virtual\s+|override\s+|sealed\s+)*"
                               r"[\w<>\[\],\.\?]+\s+(\w+)\s*\(")],
    "go": [re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?(\w+)\s*\("),
           re.compile(r"^\s*type\s+(\w+)\s+(?:struct|interface)")],
    "rs": [re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)"),
           re.compile(r"^\s*(?:pub\s+)?(?:struct|enum|trait)\s+(\w+)")],
    "rb": [re.compile(r"^\s*def\s+(\w+)"), re.compile(r"^\s*class\s+(\w+)")],
    "php": [re.compile(r"^\s*(?:public\s+|private\s+|protected\s+|static\s+)*function\s+(\w+)"),
            re.compile(r"^\s*class\s+(\w+)")],
}
EXT_GROUP = {
    ".py": "py", ".js": "js", ".jsx": "js", ".ts": "js", ".tsx": "js",
    ".cs": "cs", ".java": "cs", ".kt": "cs", ".swift": "cs",
    ".go": "go", ".rs": "rs", ".rb": "rb", ".php": "php",
}

# A banner/section divider: a comment line with a run of >= 5 separator chars.
BANNER = re.compile(r"[─═=\-*~_#·—]{5,}")
COMMENT_LEAD = re.compile(r"^\s*(?://+|#+|--|;+|/\*+|\*+)\s?")


def is_comment(line):
    return bool(COMMENT_LEAD.match(line))


def clean_comment(line):
    text = COMMENT_LEAD.sub("", line.strip())
    text = re.sub(r"\*/\s*$", "", text).strip()
    return text


def banner_title(line):
    text = clean_comment(line)
    text = re.sub(r"[─═=\-*~_#·—]{2,}", " ", text).strip()
    return text  # may be "" for a pure rule with no title


def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for name in filenames:
            ext = os.path.splitext(name)[1]
            if ext in EXT_GROUP:
                yield os.path.join(dirpath, name), ext


def scan_file(path, ext):
    """Return (sections, entries). entries: (section, symbol, line_no, signature, synopsis)."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return []
    patterns = PATTERNS.get(EXT_GROUP[ext], [])
    entries = []
    section = ""
    for i, raw in enumerate(lines):
        if is_comment(raw) and BANNER.search(raw):
            title = banner_title(raw)
            if title:
                section = title
            continue
        for pat in patterns:
            m = pat.match(raw)
            if m:
                symbol = m.group(1)
                signature = raw.strip()
                if len(signature) > 100:
                    signature = signature[:100].rstrip() + "..."
                # synopsis: the full run of comment lines directly above the declaration
                # (skip blanks, then gather the contiguous non-banner comment block).
                synopsis = ""
                j = i - 1
                while j >= 0 and not lines[j].strip():
                    j -= 1
                block = []
                while j >= 0 and is_comment(lines[j]) and not BANNER.search(lines[j]):
                    block.append(clean_comment(lines[j]))
                    j -= 1
                if block:
                    synopsis = " ".join(reversed(block)).strip()
                    if len(synopsis) > 140:
                        synopsis = synopsis[:140].rstrip() + "..."
                entries.append((section, symbol, i + 1, signature, synopsis))
                break
    return entries


def main(argv=None):
    parser = argparse.ArgumentParser(description="KISS map generator -> .kiss/inert.md")
    parser.add_argument("root", help="repo root to scan")
    parser.add_argument("--out", default=None, help="output path (default <root>/.kiss/inert.md)")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.root)
    out = args.out or os.path.join(root, ".kiss", "inert.md")
    out_dir = os.path.dirname(out)
    if out_dir:  # a bare filename (no directory) needs no makedirs
        os.makedirs(out_dir, exist_ok=True)

    by_file = {}
    total = 0
    for path, ext in iter_files(root):
        entries = scan_file(path, ext)
        if entries:
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            by_file[rel] = entries
            total += len(entries)

    lines = [
        "# .kiss/inert.md — KISS function map",
        "",
        "> GENERATED by kiss-map-gen.py — do not edit by hand; regenerate when stale.",
        "> Source of truth for *what exists and where*. **Grep this file for a symbol; do not read it whole.**",
        "> Before creating: check for a twin here first. If reality disagrees with the map, the map is stale — regenerate.",
        f"> Symbols: {total} across {len(by_file)} files.",
        "",
    ]
    for rel in sorted(by_file):
        lines.append(f"## {rel}")
        current = None
        for section, symbol, ln, sig, syn in by_file[rel]:
            if section != current:
                current = section
                if section:
                    lines.append(f"### {section}")
            tail = f" — {syn}" if syn else ""
            lines.append(f"- `{symbol}` · L{ln} · `{sig}`{tail}")
        lines.append("")

    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"Wrote {out} — {total} symbols across {len(by_file)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
