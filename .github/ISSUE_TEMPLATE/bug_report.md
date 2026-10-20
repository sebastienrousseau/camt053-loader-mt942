---
name: Bug report
about: Report a defect so we can reproduce and fix it
title: "bug: "
labels: ["bug"]
assignees: []
---
<!-- SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

## Summary

A clear and concise description of the bug.

## Steps to Reproduce

```python
from camt053_loader_mt942 import parse_mt942

# The smallest MT942 payload that shows the problem, with account numbers,
# names and amounts replaced by dummy values.
document = parse_mt942(""":20:...""")
```

## Expected Behaviour

What you expected `parse_mt942` to return or raise.

## Actual Behaviour

What it returned instead, or the full traceback.

## Environment

- camt053-loader-mt942 version:
- camt053 version:
- Python version:
- Operating system:
- The bank or system that produced the MT942, if you can say:
