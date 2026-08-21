"""The version must be identical everywhere it is stated.

`pyproject.toml` and `camt053_loader_mt942/__init__.py` each carry the version
independently, and nothing compared them. That is not hypothetical: the
0.0.16 release landed `__init__.py` at 0.0.16 against a
`pyproject.toml` still on 0.0.14, and every check in CI passed. The
package would have been published with its metadata and its own
`__version__` disagreeing.
"""

from __future__ import annotations

import re
from pathlib import Path

import camt053_loader_mt942

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"

_VERSION_RE = re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE)
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _pyproject_version() -> str:
    """Return the version declared in pyproject.toml."""
    match = _VERSION_RE.search(PYPROJECT.read_text(encoding="utf-8"))
    assert match, "pyproject.toml has no version field"
    return match.group(1)


def test_dunder_version_is_semver() -> None:
    """The package version must be a plain X.Y.Z."""
    assert _SEMVER_RE.match(camt053_loader_mt942.__version__), (
        f"__version__ is {camt053_loader_mt942.__version__!r}, which is not X.Y.Z"
    )


def test_dunder_version_matches_pyproject() -> None:
    """The two declarations must not drift apart."""
    assert camt053_loader_mt942.__version__ == _pyproject_version(), (
        f"__version__ is {camt053_loader_mt942.__version__!r} but pyproject.toml says "
        f"{_pyproject_version()!r} — one of them was bumped and the other "
        f"was not"
    )
