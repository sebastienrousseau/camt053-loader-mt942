# Security Policy

## Supported versions

Security fixes are applied to the latest released version on PyPI and the
`main` branch. The table below tracks which series receive fixes.

| Version | Supported |
|---------|-----------|
| `0.0.20` | Latest released `0.0.x` only |
| < `0.0.20` | No |

A longer-term support window will be announced here once `1.0.0` ships.

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues privately by either:

1. **Preferred:** GitHub's private vulnerability reporting — open a draft
   advisory at <https://github.com/sebastienrousseau/camt053-loader-mt942/security/advisories/new>.
2. **Email:** `contact@sebastienrousseau.com` with the subject line
   `[camt053-loader-mt942 security]`.

Include, where possible:

- A description of the issue and its impact (confidentiality, integrity,
  availability).
- Steps to reproduce, ideally with a minimal proof of concept.
- The affected version(s) and platform(s).
- Any suggested mitigation or fix.

## What to expect

| Stage | Target |
|-------|--------|
| Acknowledgement | Within 3 business days |
| Initial assessment | Within 10 business days |
| Fix or mitigation plan | Within 30 days for high/critical severity |
| Public disclosure | Coordinated with reporter after a fix is available |

For low-severity issues, the timeline may be longer. We will keep you updated
on progress.

## Scope

In scope:

- Code under `camt053_loader_mt942/` shipped to PyPI.
- The example scripts under `examples/`.
- The parsing of untrusted MT942 payloads: a malformed or hostile report
  must raise, not crash the interpreter or consume unbounded memory.

Out of scope:

- Third-party dependencies (please report upstream — we will track the
  advisory and update our pinned ranges). This includes the `camt053`
  library, which has its own policy.
- Vulnerabilities that require local code execution on the host already
  running the server.
- Denial-of-service via deliberately crafted input that exceeds documented
  size limits (open a feature request to add a guard instead).

## Hardening guidance for operators

This is a parsing library, so its whole attack surface is the text it is
handed:

- MT942 payloads arriving from a bank or a correspondent are untrusted
  input. Parse them in the same place you would parse any external file,
  and treat a raised exception as the expected outcome for a malformed
  report rather than something to suppress.
- An intraday report is polled, so its size is not under your control. If
  you parse in a request handler, bound the input size before parsing
  rather than after.
- Parsed reports carry account identifiers and counterparty names — PII
  subject to GDPR/PCI-DSS. Encrypt at rest and in transit, and be careful
  about logging parsed structures verbatim.
- Keep `camt053-loader-mt942`, `camt053`, and the Python interpreter
  patched.

## Credits

We will credit reporters who follow this policy in release notes and the
GitHub advisory, unless they request anonymity.
