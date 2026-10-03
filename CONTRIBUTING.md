# Contributing to FeROS Builder

Builder owns image construction and validation. Core compilation, workspace
menus, firmware selection, and physical-media operations belong to other
components. Discuss changes to these boundaries before implementing them.

## Development

Use Python 3.10 or newer, GNU Make, and a supported macOS, Linux, or Windows host.
On Windows, use Git Bash with GNU Make and native Windows Python on PATH;
run `make release PYTHON=python`.
Sources live directly under `src/`; keep platform image implementations under
`src/image/`. Use English for code comments, diagnostics, and documentation.

From this repository, run `make test` for source tests and `make release` for
source tests, native packaging, and executable tests. Set `PYTHON` to a suitable
interpreter if the host default is older. These are product development targets;
workspace users continue to enter their workflow through the workspace menu.

Tests must use synthetic data and temporary directories. Do not require real
firmware, privileged access, storage devices, or a neighboring Core checkout.
For input-validation changes, include an independently meaningful rejection
case. For image changes, document offsets, sizes, and evidence; do not update
expected bytes merely to make a test pass.

## Pull requests

Explain the problem, the resulting behavior, and how it was verified. Keep
changes scoped and update the versioned changelog entry for user-visible changes.
Record architectural decisions in `docs/adr/`. Source and packaged CLI tests
must pass on the supported CI matrix before a release is prepared.

Do not include generated binaries, virtual environments, proprietary firmware,
credentials, or identifiable device dumps. Supply minimal reproducible synthetic
fixtures where possible. Preserve existing copyright and license notices.
Contributions are submitted under the repository's MIT license; contributors
must have the right to submit them. No contributor agreement is required.

## Reports and review

Use issues for ordinary bugs and proposals. Follow [SECURITY.md](SECURITY.md)
for suspected vulnerabilities; do not put private exploit details in issues.
Follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) in all project spaces.

The maintainer reviews changes and may request revisions or decline proposals.
Review availability is best effort; there is no promised response time.
