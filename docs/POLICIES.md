<!-- SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Toolchain policy

Python 3.11 is the floor (`requires-python = ">=3.11"` in
`pyproject.toml`), with Linux CI on 3.11, 3.12, 3.13 and 3.14. The
floor is the camt053 suite's: it moves for every member together, as a
maintainer decision recorded in the changelog, and never below what the
`camt053` core supports. No distro-system Python is supported.

The runtime dependency floor (`camt053 >= X, < 1`) is raised to the newest
released core in each suite release. The suite ships one version number,
so a member and the core it was released with share a version.
