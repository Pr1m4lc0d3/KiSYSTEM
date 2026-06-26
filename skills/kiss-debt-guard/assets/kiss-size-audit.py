#!/usr/bin/env python3
"""KISS size-budget audit — dependency-free (Python 3 stdlib only).

Walks a repo, counts lines per source file, and classifies each against the
size tiers in kiss-budget.config.json (review / extract / hard-stop).

Exit code is non-zero when any non-waived file exceeds the hard-stop tier, so
this can gate a pre-commit hook or CI step. Use --report to print the full
breakdown without failing.

Usage:
    python kiss-size-audit.py <repo-root> [--config PATH] [--report]
"""
import argparse
import fnmatch
import json
import os
import sys

DEFAULT_CONFIG = {
    "tiers": {"review": 300, "extract": 500, "hard_stop": 800},
    "include_extensions": [
        ".py", ".js", ".jsx", ".ts", ".tsx", ".cs", ".java", ".go",
        ".rb", ".rs", ".cpp", ".cc", ".c", ".h", ".hpp", ".php", ".kt", ".swift",
    ],
    "exclude_dirs": [
        ".git", "node_modules", "bin", "obj", "dist", "build", "out",
        ".vs", ".venv", "venv", "__pycache__", "vendor", "packages", ".kiss",
    ],
    "exclude_globs": ["*.min.js", "*.designer.cs", "*.g.cs", "*.g.i.cs"],
    "waivers": {},  # "relative/path.ext": {"reason": "...", "expires": "YYYY-MM-DD"}
}


# Backup/copy artifacts that belong in git history, not the working tree (duplicate-surface bloat).
CLUTTER_PATTERNS = ["*backup*", "*.bak", "*.orig", "*.old", "*-old", "*_old", "* copy*", "*copy.*"]


def load_config(path):
    if path and os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as fh:
            user = json.load(fh)
        cfg = dict(DEFAULT_CONFIG)
        cfg.update(user)
        tiers = dict(DEFAULT_CONFIG["tiers"])
        tiers.update(user.get("tiers", {}))
        cfg["tiers"] = tiers
        return cfg
    return dict(DEFAULT_CONFIG)


def count_lines(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def iter_source_files(root, cfg):
    exts = tuple(cfg["include_extensions"])
    exclude_dirs = set(cfg["exclude_dirs"])
    exclude_globs = cfg["exclude_globs"]
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for name in filenames:
            if not name.endswith(exts):
                continue
            if any(fnmatch.fnmatch(name, g) for g in exclude_globs):
                continue
            yield os.path.join(dirpath, name)


def iter_clutter(root):
    """Yield backup/copy artifacts — keep backups in git, not the tree."""
    exclude_dirs = set(DEFAULT_CONFIG["exclude_dirs"])
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        kept = []
        for d in dirnames:
            if any(fnmatch.fnmatch(d.lower(), p) for p in CLUTTER_PATTERNS):
                yield os.path.relpath(os.path.join(dirpath, d), root).replace(os.sep, "/") + "/"
            else:
                kept.append(d)
        dirnames[:] = kept  # report a backup dir but don't descend into it
        for name in filenames:
            if any(fnmatch.fnmatch(name.lower(), p) for p in CLUTTER_PATTERNS):
                yield os.path.relpath(os.path.join(dirpath, name), root).replace(os.sep, "/")


def main(argv=None):
    parser = argparse.ArgumentParser(description="KISS size-budget audit")
    parser.add_argument("root", help="repo root to scan")
    parser.add_argument("--config", default=None,
                        help="path to kiss-budget.config.json")
    parser.add_argument("--report", action="store_true",
                        help="print full breakdown and exit 0 regardless")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.root)
    config_path = args.config or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "kiss-budget.config.json")
    cfg = load_config(config_path)
    tiers = cfg["tiers"]
    waivers = cfg.get("waivers", {})

    review, extract, hard = [], [], []
    for path in iter_source_files(root, cfg):
        n = count_lines(path)
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        if n >= tiers["hard_stop"]:
            hard.append((rel, n))
        elif n >= tiers["extract"]:
            extract.append((rel, n))
        elif n >= tiers["review"]:
            review.append((rel, n))

    clutter = list(iter_clutter(root))
    if clutter:
        print(f"\nCLUTTER — backup/copy artifacts ({len(clutter)}); keep backups in git, not the tree:")
        for c in sorted(clutter):
            print(f"  {c}")

    def show(label, items):
        if not items:
            return
        print(f"\n{label} ({len(items)}):")
        for rel, n in sorted(items, key=lambda x: -x[1]):
            tag = "  [waived]" if rel in waivers else ""
            print(f"  {n:6}  {rel}{tag}")

    if args.report:
        show(f"REVIEW (>= {tiers['review']})", review)
        show(f"EXTRACT (>= {tiers['extract']})", extract)
        show(f"HARD-STOP (>= {tiers['hard_stop']})", hard)
        print(f"\nTotals: review={len(review)} extract={len(extract)} "
              f"hard_stop={len(hard)}")
        return 0

    violations = [(rel, n) for rel, n in hard if rel not in waivers]
    if violations:
        print(f"KISS size audit FAILED — {len(violations)} file(s) over the "
              f"hard-stop tier ({tiers['hard_stop']} lines):")
        for rel, n in sorted(violations, key=lambda x: -x[1]):
            print(f"  {n:6}  {rel}")
        print("\nExtract before adding more, or add a waiver with an expiry date.")
        return 1

    print(f"KISS size audit passed (hard-stop tier = {tiers['hard_stop']} lines).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
