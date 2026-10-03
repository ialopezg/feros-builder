# Stability Policy

FeROS Builder is experimental and preparing its first `0.1.0` release.

| Area | Current commitment |
| --- | --- |
| CLI | `build`, `validate`, and help; compatibility governed by VERSIONING.md |
| RK3566 format | Current X55 RKNS layout only; changes require evidence and tests |
| Image determinism | Identical payload inputs and implementation should produce identical bytes |
| Binary reproducibility | Not guaranteed; runtime, dependencies, and build hosts may differ |
| Python API | Internal, no compatibility guarantee |
| Console text | Intended for humans, may change |
| Physical boot | Not established by image-validation success |

The CI and release matrix covers macOS ARM64, Linux x86_64, and Windows
x86_64. Each release commit must pass native build and extracted-package tests
on all three platforms. Windows verification is pending the expanded CI run.
Other architectures accepted by the Makefile remain best effort until tested.

Release metadata records the actual host and Python version. Linux binaries
may require the build host's glibc baseline; macOS binaries may require an OS
version compatible with the packaged runtime. Successful execution on a runner
does not prove compatibility with all older systems. Windows executables are
not Authenticode-signed; macOS executables are not notarized.

Only the latest release is routinely maintained. There is no LTS or availability
SLA. See [SECURITY.md](SECURITY.md) for reporting and [VERSIONING.md](VERSIONING.md)
for compatibility rules.
