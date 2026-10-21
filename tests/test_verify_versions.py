# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""scripts/verify_versions.py catches every restatement that drifts."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_versions.py"

TREE = {
    "pyproject.toml": (
        '[project]\nversion = "0.0.23"\n'
        'dependencies = [\n    "camt053 >= 0.0.23, < 1",\n]\n'
    ),
    "camt053_loader_mt942/__init__.py": '__version__ = "0.0.23"\n',
    "CHANGELOG.md": "# Changelog\n\n## [0.0.23] - 2026-10-20\n\n## [0.0.20]\n",
    "releases/v0.0.23.md": "# camt053-loader-mt942 v0.0.23\n",
    "CITATION.cff": 'cff-version: 1.2.0\nversion: "0.0.23"\n',
    "README.md": "> **Latest release: v0.0.23**: a loader.\n",
    "SECURITY.md": "| `0.0.23` | Latest released `0.0.x` only |\n",
    "requirements/ci.in": "camt053>=0.0.23,<1\n",
}


def _load(root: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_versions", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = root
    return module


def _tree(root: Path, **changes: str) -> ModuleType:
    files = dict(TREE)
    files.update({k.replace("__", "/"): v for k, v in changes.items()})
    for name, text in files.items():
        if text:
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_text(text, encoding="utf-8")
    return _load(root)


def test_a_tree_on_one_version_passes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _tree(tmp_path).main() == 0
    assert "OK: every source agrees on 0.0.23" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("name", "text", "error"),
    [
        (
            "camt053_loader_mt942/__init__.py",
            '__version__ = "0.0.20"\n',
            "__version__ differs",
        ),
        ("CHANGELOG.md", "## [0.0.20]\n", "CHANGELOG.md newest differs"),
        ("releases/v0.0.23.md", "", "releases/v0.0.23.md differs"),
        ("CITATION.cff", 'version: "0.0.20"\n', "CITATION.cff differs"),
        ("CITATION.cff", "", "CITATION.cff differs"),
        (
            "README.md",
            "> **Latest release: v0.0.14.**\n",
            "README.md differs",
        ),
        (
            "SECURITY.md",
            "| `0.0.20` | Latest released `0.0.x` only |\n",
            "SECURITY.md differs",
        ),
        (
            "pyproject.toml",
            '[project]\nversion = "0.0.23"\n'
            'dependencies = [\n    "camt053 >= 0.0.20, < 1",\n]\n',
            "pyproject.toml camt053 floor differs",
        ),
        (
            "pyproject.toml",
            '[project]\nversion = "0.0.23"\n'
            'dependencies = [\n    "camt053",\n]\n',
            "pyproject.toml has no camt053 floor",
        ),
        (
            "requirements/ci.in",
            "camt053>=0.0.20,<1\n",
            "requirements/ci.in camt053 floor differs",
        ),
    ],
)
def test_each_drift_is_caught(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    name: str,
    text: str,
    error: str,
) -> None:
    files = {k: v for k, v in TREE.items() if k != name}
    for path, content in files.items():
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text(content, encoding="utf-8")
    if text:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(text, encoding="utf-8")
    assert _load(tmp_path).main() == 1
    assert f"ERROR: {error}" in capsys.readouterr().out


def test_a_pyproject_without_a_version_is_fatal(tmp_path: Path) -> None:
    module = _tree(tmp_path, **{"pyproject.toml": "[project]\n"})
    with pytest.raises(SystemExit, match="no version field"):
        module.main()


def test_the_real_tree_agrees() -> None:
    assert _load(SCRIPT.parents[1]).main() == 0
