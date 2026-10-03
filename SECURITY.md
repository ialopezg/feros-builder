# Security Policy

## Reporting privately

The intended vulnerability-reporting channel is GitHub Private Vulnerability
Reporting at:

https://github.com/ialopezg/feros-builder/security/advisories/new

The maintainer must enable and verify this feature before the first public
release. This file does not enable it. If the private form is unavailable,
request a private channel without disclosing vulnerability details. No email
address has been designated. Do not submit secrets, personal data, proprietary
firmware, or exploit details through a public issue.

Include the affected commit/version, host OS and architecture, minimal
reproduction, expected impact, and a synthetic sample where possible. Allow
coordination of a fix and disclosure. No bounty or response-time commitment is
currently offered.

## Supported versions

No version is released yet. During `0.x`, fixes target `main` and the latest
published release. Older releases receive no routine backports. Fixes can
require upgrading; specific exceptions must be announced in release notes.

## Trust boundaries

Builder constructs and validates image files from caller-selected paths. It
does not authenticate firmware authors, inspect payload intent, or prove that
an image is safe for a device. SHA-256 verifies consistency against embedded
hashes, which a malicious image author can also calculate. It is not a signature.

The existing parser reads entire files into memory and is not hardened against
all resource-exhaustion or adversarial-layout cases. The CLI uses ordinary
filesystem reads and writes; it follows filesystem path semantics, can replace
an existing output, and does not implement a device-path or symlink sandbox.
Its lack of a flashing command is not a filesystem access-control boundary.
Use it without elevated privileges and with inputs and output paths you control.

## Build and distribution

Review workflow and dependency changes carefully. CI uses read-only permissions
and does not run pull-request code with a release token. The release workflow
builds from an existing tag and creates a draft only. Maintainers review assets
before publication. An adjacent checksum detects accidental corruption; it does
not protect against replacement of both archive and checksum.

Current packages do not claim Apple notarization, reproducible binary builds,
or cryptographic provenance attestations. See [RELEASE.md](RELEASE.md) and
[THIRD_PARTY.md](THIRD_PARTY.md) for review requirements.

Use the tool only on data and systems you are authorized to handle. This
expectation does not add a field-of-use restriction to the MIT license.
