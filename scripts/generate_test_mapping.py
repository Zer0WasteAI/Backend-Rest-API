#!/usr/bin/env python3
"""
Generate a per-file test mapping report for the repository.

The report is written to COMPREHENSIVE_TEST_COVERAGE_ANALYSIS.md and includes:
- Totals for source and test files
- Files with no direct reference from tests (by import-path search)
- A heuristic mapping of source files to likely test files (by filename matching)

Notes:
- This is a static analysis that searches for `src.<module.path>` strings in test files.
- Some files may be covered indirectly without explicit imports; treat this as guidance.
"""
from __future__ import annotations

import os
import re
from typing import Dict, List, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
SRC_ROOT = os.path.join(REPO_ROOT, "src")
TEST_ROOT = os.path.join(REPO_ROOT, "test")
OUTPUT_FILE = os.path.join(REPO_ROOT, "COMPREHENSIVE_TEST_COVERAGE_ANALYSIS.md")


def list_py_files(root: str) -> List[str]:
    files: List[str] = []
    for r, d, fns in os.walk(root):
        if "__pycache__" in r:
            continue
        for f in fns:
            if f.endswith(".py") and f != "__init__.py":
                files.append(os.path.join(r, f))
    return files


def build_test_index(test_files: List[str]) -> Dict[str, str]:
    idx: Dict[str, str] = {}
    for p in test_files:
        # Skip backup/disabled helpers
        if p.endswith(".backup") or p.endswith(".disabled"):
            continue
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                idx[p] = fh.read()
        except Exception:
            idx[p] = ""
    return idx


def module_path(sf: str) -> str:
    rel = os.path.relpath(sf, SRC_ROOT)
    return "src." + rel[:-3].replace(os.sep, ".")


def find_import_matches(sf: str, test_index: Dict[str, str]) -> List[str]:
    mod = module_path(sf)
    matches = [tf for tf, content in test_index.items() if mod in content]
    return sorted(set(matches))


def find_name_matches(sf: str, test_files: List[str]) -> List[str]:
    base = os.path.basename(sf)
    name = base[:-3]
    # Exact filename substring match first
    matches = [tf for tf in test_files if name in os.path.basename(tf)]
    # Then token-based heuristic
    if not matches:
        tokens = [t for t in re.split(r"[_]+", name) if t]
        for tf in test_files:
            tbase = os.path.basename(tf)
            for tok in tokens:
                if re.search(rf"\b{re.escape(tok)}\b", tbase):
                    matches.append(tf)
                    break
    return sorted(set(matches))


def main() -> None:
    src_files = list_py_files(SRC_ROOT)
    test_files = list_py_files(TEST_ROOT)
    test_index = build_test_index(test_files)

    by_import: List[Tuple[str, List[str]]] = []
    by_name_only: List[Tuple[str, List[str]]] = []
    missing: List[str] = []

    for sf in sorted(src_files):
        imp = find_import_matches(sf, test_index)
        if imp:
            by_import.append((sf, imp))
            continue
        name_matches = find_name_matches(sf, list(test_index.keys()))
        if name_matches:
            by_name_only.append((sf, name_matches))
        else:
            missing.append(sf)

    lines: List[str] = []
    lines.append("# Comprehensive Test Coverage Analysis")
    lines.append("")
    lines.append(f"Total source files: {len(src_files)}")
    lines.append(f"Total test files: {len(test_files)}")
    lines.append(f"Directly referenced by tests (import match): {len(by_import)}")
    lines.append(f"Heuristic name-only matches: {len(by_name_only)}")
    lines.append(f"No obvious match: {len(missing)}")
    lines.append("")

    lines.append("## No Obvious Match")
    for sf in missing:
        lines.append(f"- {os.path.relpath(sf, REPO_ROOT)}")
    lines.append("")

    lines.append("## Import Matches (strong signal)")
    for sf, tests in by_import:
        lines.append(f"- {os.path.relpath(sf, REPO_ROOT)}")
        for t in tests:
            lines.append(f"  - {os.path.relpath(t, REPO_ROOT)}")
    lines.append("")

    lines.append("## Name-only Matches (weak signal)")
    for sf, tests in by_name_only:
        lines.append(f"- {os.path.relpath(sf, REPO_ROOT)}")
        for t in tests:
            lines.append(f"  - {os.path.relpath(t, REPO_ROOT)}")
    lines.append("")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print(
        f"Report written to {os.path.relpath(OUTPUT_FILE, REPO_ROOT)} "
        f"(direct matches: {len(by_import)}, name matches: {len(by_name_only)}, missing: {len(missing)})"
    )


if __name__ == "__main__":
    main()

