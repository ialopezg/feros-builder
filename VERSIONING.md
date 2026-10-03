# Versioning Policy

The package version in `pyproject.toml` is authoritative. Git release tags use
`vMAJOR.MINOR.PATCH` and must match it exactly. The release workflow checks this
match and records the full source commit in each package.

## Before 1.0

`0.x` is experimental. A minor increment may change CLI options, accepted input
layouts, or generated image bytes. Patch versions normally fix bugs or update
documentation/build dependencies without intentionally changing the CLI.
A security or correctness fix may reject inputs previously accepted; document
that effect even when shipping a patch.

## From 1.0

Major versions identify incompatible public CLI or supported-format contract
changes. Minor versions add compatible functionality. Patch versions contain
compatible corrections. Document observable changes and migration guidance.

The public interface is the documented CLI, exit success/failure, and supported
image contracts. Python modules are implementation details, not a supported
import API. Human-readable output is not a stable machine-readable format.
Firmware versions, Core versions, and image payload versions are independent
of the Builder version.

Published tags and assets are immutable by policy. Publish a new version to
correct an error; do not silently move a published tag or replace its binaries.
Unpublished candidates may be revised before the tag is created.
