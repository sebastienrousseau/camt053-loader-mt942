#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Fail when the release version is restated differently anywhere.

Single source of truth: ``version`` in ``pyproject.toml``. The same string
must appear as the package's ``__version__``, as a ``## [X.Y.Z]`` heading in
``CHANGELOG.md``, as ``releases/vX.Y.Z.md`` (the release workflow publishes
it as the GitHub release notes), in ``CITATION.cff`` (``version``), in the
README's ``Latest release: vX.Y.Z`` line (PyPI renders the README as the
project page) and as the supported row of ``SECURITY.md``.

The README said "Latest release: v0.0.14" through 0.0.16 and 0.0.20, and
SECURITY.md named a version nobody checked, because nothing compared them.
Standard library only, so the workflow needs no install.

Usage: python3 scripts/verify_versions.py
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

Check = tuple[list[str], list[str]]


def _read(name: str) -> str | None:
    path = ROOT / name
    return path.read_text(encoding="utf-8") if path.exists() else None


def _first(pattern: str, text: str | None) -> str | None:
    if text is None:
        return None
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1) if match else None


def _pyproject_version() -> str:
    found = _first(r'^version\s*=\s*"([^"]+)"', _read("pyproject.toml"))
    if found is None:
        raise SystemExit("pyproject.toml has no version field")
    return found


def _compare(label: str, found: str | None, expected: str) -> Check:
    line = f"  {label:<22} = {found}"
    return [line], [] if found == expected else [f"{label} differs"]


def _check_package(expected: str) -> Check:
    init = _read("camt053_loader_mt942/__init__.py")
    found = _first(r'^__version__\s*=\s*"([^"]+)"', init)
    return _compare("__version__", found, expected)


def _check_changelog(expected: str) -> Check:
    text = _read("CHANGELOG.md") or ""
    headings = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", text, re.MULTILINE)
    newest = headings[0] if headings else None
    return _compare("CHANGELOG.md newest", newest, expected)


def _check_release_notes(expected: str) -> Check:
    name = f"releases/v{expected}.md"
    title = _first(r"^# camt053-loader-mt942 v(\S+)$", _read(name))
    return _compare(name, title, expected)


def _check_citation(expected: str) -> Check:
    found = _first(r'^version:\s*"?([^"\s]+)"?\s*$', _read("CITATION.cff"))
    return _compare("CITATION.cff", found, expected)


def _check_readme(expected: str) -> Check:
    found = _first(r"Latest release: v(\d+\.\d+\.\d+)", _read("README.md"))
    return _compare("README.md", found, expected)


def _check_security(expected: str) -> Check:
    found = _first(r"^\| `(\d+\.\d+\.\d+)` \| Latest", _read("SECURITY.md"))
    return _compare("SECURITY.md", found, expected)


CHECKS: tuple[Callable[[str], Check], ...] = (
    _check_package,
    _check_changelog,
    _check_release_notes,
    _check_citation,
    _check_readme,
    _check_security,
)


def main() -> int:
    """Compare every restatement of the version and report."""
    expected = _pyproject_version()
    problems: list[str] = []
    print(f"  {'pyproject.toml':<22} = {expected}")
    for check in CHECKS:
        lines, found = check(expected)
        for line in lines:
            print(line)
        problems.extend(found)
    for problem in problems:
        print(f"ERROR: {problem}")
    if problems:
        return 1
    print("OK: every source agrees on", expected)
    return 0


if __name__ == "__main__":
    sys.exit(main())
