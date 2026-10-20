<!-- SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->
<!--
Shape: ~/Code/PR-TEMPLATE.md. Open with the two-line BLUF: line 1 begins
"This PR " and says what it does, line 2 says why it matters; a blank line
between them. No em dashes anywhere in the body. Keep the sections and
their order, and fill every placeholder from real evidence. Title in
Conventional Commit style, e.g. "fix: keep :61: supplementary details".
-->

This PR <what it does, in one plain line>.

<why it matters or the outcome, in one plain line>

## Highlights ⭐️

* **<Headline>**: <one or two plain sentences on what changed for the user>.
* **<Headline>**: <one or two plain sentences>.

## What's Changed

* `<commit subject>` by @<author>

<optional: a few detail bullets naming files and the concrete change>

## Validation

* `make check`: <result, with numbers: tests passed, coverage, gates>.
* `make build`: <sdist and wheel built, `twine check --strict` result>.

## Checksums

SHA-256 of the artifacts produced by `make build` on this branch:

```text
<sha256>  dist/camt053_loader_mt942-<version>-py3-none-any.whl
<sha256>  dist/camt053_loader_mt942-<version>.tar.gz
```

**Full Changelog**: https://github.com/sebastienrousseau/camt053-loader-mt942/compare/<previous tag>...<branch or tag>
