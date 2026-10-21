# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The scheduled suite check holds the camt053 suite to one version.

Every member ships the core's number, in the same release, so a member
published ahead of the core fails exactly like one left behind. The tree
is compared with ``camt053-loader-mt942``'s own release, not the core's.
PyPI is never reached; the published versions are substituted.
"""

from __future__ import annotations

import importlib.util
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "check_suite_consistency.py"
)

MEMBERS = (
    "camt053",
    "camt053-lsp",
    "camt053-mcp",
    "camt053-loader-mt940",
    "camt053-loader-mt942",
    "camt053-writer-xlsx",
)

Check = Callable[[str, dict[str, str | None]], list[str]]


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("suite_check", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def script(monkeypatch: pytest.MonkeyPatch) -> Check:
    """The script's check, with PyPI and the tree substituted."""
    module = _load()

    def use(tree: str, published: dict[str, str | None]) -> list[str]:
        monkeypatch.setattr(module, "tree_version", lambda: tree)
        monkeypatch.setattr(module, "published_version", published.get)
        problems: list[str] = module.check()[0]
        return problems

    return use


def _suite(version: str, **members: str) -> dict[str, str | None]:
    versions: dict[str, str | None] = dict.fromkeys(MEMBERS, version)
    versions.update({k.replace("_", "-"): v for k, v in members.items()})
    return versions


def test_the_script_names_this_distribution() -> None:
    """The shared copy differs from its siblings in this constant only."""
    module = _load()
    assert module.THIS == "camt053-loader-mt942"
    assert module.MEMBERS == MEMBERS


def test_a_suite_on_one_version_is_clean(script: Check) -> None:
    assert script("0.0.23", _suite("0.0.23")) == []


def test_a_member_ahead_of_the_core_fails(script: Check) -> None:
    """The state main is in: camt053-mcp 0.0.22, every other member 0.0.20."""
    problems = script("0.0.20", _suite("0.0.20", camt053_mcp="0.0.22"))
    assert problems == [
        "camt053-mcp: published 0.0.22, but the suite is at 0.0.20"
    ]


def test_a_member_left_behind_fails(script: Check) -> None:
    problems = script("0.0.23", _suite("0.0.23", camt053_lsp="0.0.20"))
    assert problems == [
        "camt053-lsp: published 0.0.20, but the suite is at 0.0.23"
    ]


def test_unreleased_bump_names_this_distribution(script: Check) -> None:
    """A bump that never reached PyPI is reported against this package."""
    problems = script("0.0.23", _suite("0.0.22"))
    assert problems == [
        "camt053-loader-mt942: tree is 0.0.23 but PyPI has 0.0.22. Either "
        "the release was never tagged, or the tree is behind."
    ]


def test_the_core_released_first_and_this_not_yet(script: Check) -> None:
    """Mid-release: the core is out, this member is bumped but not tagged.

    The tree agrees with the core, so a check against the core's release
    passes; it is this package's own release that is missing.
    """
    versions = _suite("0.0.20", camt053="0.0.23")
    problems = script("0.0.23", versions)
    assert problems[0] == (
        "camt053-loader-mt942: tree is 0.0.23 but PyPI has 0.0.20. Either "
        "the release was never tagged, or the tree is behind."
    )


def test_unreadable_index_is_reported(script: Check) -> None:
    """A member PyPI cannot answer for is a problem, never a pass."""
    versions = _suite("0.0.23")
    del versions["camt053-writer-xlsx"]
    assert script("0.0.23", versions) == [
        "camt053-writer-xlsx: could not read PyPI"
    ]


def test_main_prints_the_report_and_fails(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _load()
    monkeypatch.setattr(module, "tree_version", lambda: "0.0.23")
    published = _suite("0.0.23", camt053_lsp="0.0.20")
    monkeypatch.setattr(module, "published_version", published.get)
    monkeypatch.setattr("sys.argv", ["check_suite_consistency.py"])
    assert module.main() == 1
    out = capsys.readouterr().out
    assert "tree version: 0.0.23" in out
    assert "camt053-lsp: published 0.0.20" in out


def test_main_json_reports_a_clean_suite(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    module = _load()
    monkeypatch.setattr(module, "tree_version", lambda: "0.0.23")
    monkeypatch.setattr(module, "published_version", _suite("0.0.23").get)
    monkeypatch.setattr("sys.argv", ["check_suite_consistency.py", "--json"])
    assert module.main() == 0
    assert '"problems": []' in capsys.readouterr().out
