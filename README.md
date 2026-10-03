# FeROS Builder

[![CI](https://github.com/ialopezg/feros-builder/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ialopezg/feros-builder/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![macOS](https://img.shields.io/badge/macOS-ARM64-0969da?style=flat-square&logo=apple&logoColor=white)](STABILITY.md)
[![Linux](https://img.shields.io/badge/Linux-x86__64-0969da?style=flat-square&logo=linux&logoColor=white)](STABILITY.md)
[![Windows](https://img.shields.io/badge/Windows-x86__64-0969da?style=flat-square)](STABILITY.md)
[![ADR](https://img.shields.io/badge/ADR-decisions-d1242f?style=flat-square)](docs/adr/)


**Boot-image construction and validation for FeROS.**

FeROS Builder combines caller-provided firmware and compiled payloads into boot
images and validates their structure and integrity. It runs independently or as
part of the FeROS workspace.

> **Close to the metal.**
>
> **No magic. Every layer is visible.**

## Responsibilities

Builder owns image construction and validation. The workspace selects inputs
and orchestrates Core compilation; FeROS Flasher handles physical media.

## Supported Formats

Version `0.1.0` supports **RK3566 RKNS images for PowKiddy X55**.
See the [format reference](src/image/rk3566/README.md) for layout, input constraints,
and hardware evidence.

## Build the Executable

Requires Python 3.10 or newer, `venv`, `pip`, GNU Make, and network access for the
initial dependency installation.

From the Builder repository:

```bash
make release
```

On Windows, run `make release PYTHON=python` from Git Bash with GNU Make and
native Windows Python on PATH.

The Makefile prepares the environment, tests the source, packages the executable,
tests it, and installs it under `bin/<os>/<arch>/builder` (`builder.exe` on
Windows). Set `PYTHON` to select an interpreter and `BIN_ROOT` to override the
installation directory.

The release matrix covers macOS ARM64, Linux x86_64, and Windows x86_64. Build
natively on each platform; see [stability and compatibility](STABILITY.md).
Packaged executables include Python and require neither Python nor build tools
on the destination machine.

## Usage

With the extracted executable and input files for the supported format:

```bash
./builder build --ddr /path/to/ddr.bin --stage0 /path/to/feros.bin --output /path/to/boot.img
./builder validate --image /path/to/boot.img
```

Use `.\builder.exe` in Windows PowerShell. Paths are relative to the caller's
working directory unless absolute. `build` replaces an existing output file.

```bash
./builder --help
./builder build --help
./builder validate --help
```

Validation checks structure and integrity; it does not establish firmware
authenticity or successful physical boot. See [security guidance](SECURITY.md).

## Workspace Integration

From the FeROS workspace root, run `make` and select an operation from the menu.
The workspace supplies inputs and invokes Builder; no neighboring Core checkout
is required to use Builder independently.

## Development

Sources live directly under `src/`. The Makefile owns the build workflow,
`scripts/check.py` runs tests, and `scripts/package.py` creates release archives.

```bash
make test
make clean
```

`clean` removes `target/` while retaining the virtual environment and installed
executables. See [contributing](CONTRIBUTING.md) for development instructions.

## Project Documentation

- [Changelog](CHANGELOG.md) and [release procedure](RELEASE.md)
- [Versioning](VERSIONING.md) and [stability](STABILITY.md)
- [Architecture decisions](docs/adr/README.md)
- [Collaborators](COLLABORATORS.md) and [code of conduct](CODE_OF_CONDUCT.md)
- [Security](SECURITY.md) and [third-party components](THIRD_PARTY.md)

Maintained by **Isidro A. López G.**, FeROS Project.

## License

FeROS Builder is licensed under the [MIT License](LICENSE).
