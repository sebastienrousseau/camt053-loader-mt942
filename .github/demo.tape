# SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
# Rendered by `make demo` (vhs) inside a virtualenv where the package is
# installed (`make dev`). It runs the repository's own example against the
# MT942 payload the example ships; nothing leaves the machine.
Output .github/demo.gif

Set FontSize 14
Set Width 1200
Set Height 600
Set Padding 20
Set Theme "Catppuccin Mocha"

Type "sed -n 11,23p examples/01_minimal_parse.py"
Sleep 500ms
Enter
Sleep 3s

Type "python examples/01_minimal_parse.py"
Sleep 500ms
Enter
Sleep 4s
