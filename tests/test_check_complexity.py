# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The complexity gate catches each ceiling, and the baseline only shrinks."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _gate(root: Path | None = None) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "check_complexity", ROOT / "scripts" / "check_complexity.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if root is not None:
        module.ROOT = root
    return module


def _branchy() -> str:
    body = "".join(f"    if x == {i}:\n        return {i}\n" for i in range(11))
    return f"def branchy(x):\n{body}    return -1\n"


def _nested() -> str:
    # Cognitive complexity charges nesting; cyclomatic does not.
    return (
        "def nested(a, b, c, d):\n"
        "    for i in a:\n"
        "        for j in b:\n"
        "            if i and j:\n"
        "                while c:\n"
        "                    if d or c:\n"
        "                        return 1\n"
        "    return 0\n"
    )


def _long() -> str:
    body = "".join(f"    y{i} = {i}\n" for i in range(60))
    return f"def long():\n{body}    return 0\n"


def _difficult() -> str:
    # Halstead difficulty is (distinct operators / 2) * (operands /
    # distinct operands): one operand under twelve operators.
    ops = ["+", "-", "*", "/", "//", "%", "**", "<<", ">>", "&", "|", "^"]
    body = "".join(f"    c = c {op} c\n" for op in ops * 2)
    return f"def difficult(c):\n{body}    return c\n"


@pytest.mark.parametrize(
    ("source", "key", "metric"),
    [
        (_branchy(), "offender.py::branchy", "cyclomatic"),
        (_nested(), "offender.py::nested", "cognitive"),
        (_long(), "offender.py::long", "lines"),
        (_difficult(), "offender.py::difficult", "halstead"),
        ("x = 1\n" * 501, "offender.py", "file_lines"),
    ],
    ids=["cyclomatic", "cognitive", "function-lines", "halstead", "file"],
)
def test_each_ceiling_is_caught(
    tmp_path: Path, source: str, key: str, metric: str
) -> None:
    path = tmp_path / "offender.py"
    path.write_text(source, encoding="utf-8")
    report = _gate(tmp_path).measure_file(path)
    assert metric in report.get(key, {}), report


def test_a_new_offender_fails() -> None:
    problems = _gate().compare({"a.py::f": {"cyclomatic": 11}}, {})
    assert problems == ["a.py::f: cyclomatic 11 is over the ceiling"]


def test_a_baselined_offender_may_not_get_worse() -> None:
    baseline = {"a.py::f": {"cyclomatic": 11}}
    problems = _gate().compare({"a.py::f": {"cyclomatic": 12}}, baseline)
    assert problems == ["a.py::f: cyclomatic rose from 11 to 12"]


def test_an_improvement_must_shrink_the_baseline() -> None:
    baseline = {"a.py::f": {"cyclomatic": 12, "lines": 70}}
    problems = _gate().compare({"a.py::f": {"cyclomatic": 11}}, baseline)
    assert problems == [
        (
            "a.py::f: cyclomatic improved from 12 to 11; "
            "run with --update to shrink the baseline"
        ),
        (
            "a.py::f: lines improved from 70 to within the ceiling; "
            "run with --update to shrink the baseline"
        ),
    ]


def test_the_tree_matches_its_baseline(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _gate().main([]) == 0
    assert "none worse" in capsys.readouterr().out


def test_an_offender_fails_the_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    gate = _gate(tmp_path)
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "bad.py").write_text(_branchy(), encoding="utf-8")
    gate.PATHS = ("pkg",)
    gate.BASELINE = tmp_path / "baseline.json"
    gate.BASELINE.write_text("{}\n", encoding="utf-8")
    assert gate.main([]) == 1
    assert "over the ceiling" in capsys.readouterr().err


def test_update_rewrites_the_baseline(tmp_path: Path) -> None:
    gate = _gate(tmp_path)
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "bad.py").write_text(_branchy(), encoding="utf-8")
    gate.PATHS = ("pkg",)
    gate.BASELINE = tmp_path / "baseline.json"
    assert gate.main(["--update"]) == 0
    assert '"pkg/bad.py::branchy"' in gate.BASELINE.read_text("utf-8")
    assert gate.main([]) == 0
