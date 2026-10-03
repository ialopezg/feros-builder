# FeROS Builder

**Boot-image construction and validation for FeROS.**

FeROS Builder is an independent host-side tool. It consumes explicit firmware
and compiled payload paths and produces a platform boot image.

> **Close to the metal.**
>
> **No magic. Every layer is visible.**

---

## Current Status

The RK3566 RKNS generator has been extracted from FeROS Core. The CLI supports
`build` and `validate` for the current X55 image format. No Builder release has
been published. The initial package version is `0.1.0`.

Image validation checks structure and hashes. It does not prove hardware
compatibility, firmware provenance, or successful physical boot.

## Responsibilities

| Component     | Responsibility                                                                    |
|---------------|-----------------------------------------------------------------------------------|
| FeROS Core    | Operating-system sources, platform code, and linker contracts                     |
| Workspace     | Bootstrap, Core compilation orchestration, firmware selection, and shared outputs |
| FeROS Builder | Boot-image construction and validation                                            |
| FeROS Flasher | Device discovery, media writing, verification, and ejection                       |

Builder receives `--ddr`, `--stage0`, and `--output` from its caller. It does not
locate a Core checkout, compile Core, select firmware, or invoke Flasher.
Forensic captures remain research evidence, not implicit production inputs.

## Build the Executable

Building requires Python 3.10 or newer with `venv` and `pip`, GNU Make, and
network access for the initial dependency installation. The Makefile currently
supports macOS and Linux on aarch64 and x86_64. Windows packaging is not yet
configured.

From this repository:

```bash
make release
```

This prepares `.venv/`, installs the pinned PyInstaller build dependency,
tests the source CLI, packages a single executable, and runs the same tests
against that executable. Only then is it installed under
`bin/<os>/<arch>/builder`. Tests use synthetic data and never access devices.
The existing installed executable is replaced only after successful checks.

PyInstaller bundles the Python runtime; the destination machine does not need
Python installed. This is a packaged Python application, not a Rust rewrite.
Build on each intended host platform. Host OS libraries and compatibility
still apply; the binary is not a universal or fully static executable.

See [PyInstaller operating mode](https://pyinstaller.org/en/stable/operating-mode.html)
for runtime packaging and platform constraints. Dependency pinning here covers
PyInstaller itself, not a complete transitive dependency lock or bit-for-bit
reproducible executable builds.

## Workspace Integration

The workspace owns its menu, tool installation, firmware selection, and build
orchestration. Enter that workflow with `make` at the workspace root and select
an operation. This standalone repository does not require a workspace checkout.
Its Makefile accepts `BIN_ROOT` when a caller needs a shared installation path.

The host architecture follows the Python process used for packaging. Use a
native ARM64 Python for Apple Silicon.

## Usage

With the extracted executable and caller-provided payloads:

```bash
./builder build --ddr /path/to/ddr.bin --stage0 /path/to/feros.bin --output /path/to/boot.img
./builder validate --image /path/to/boot.img
```

Paths are explicit and relative to the caller's working directory unless
absolute. `build` replaces the requested output file if it exists. Run
`validate` after construction. Builder has no physical-media workflow. The current CLI uses ordinary file
access and does not enforce a device-path or symlink sandbox; see SECURITY.md.

```bash
./builder --help
./builder build --help
./builder validate --help
```

## Development

Sources live directly under `src/`. `main.py` is the entry point, `cli.py`
dispatches arguments, and `image/rk3566/mkimage.py` owns the RKNS implementation.

```bash
python3 src/main.py --help
make test
make clean
```

`clean` removes `target/` packaging intermediates. It retains `.venv/` and
installed executables. It does not clean workspace images or Core outputs.

Format details and hardware evidence are documented in the
[RK3566 image reference](src/image/rk3566/README.md). Its example paths are
relative to this repository unless stated otherwise.

## Engineering Principles

- Keep product responsibilities explicit.
- Preserve deterministic image generation from identical inputs.
- Keep hardware assumptions traceable to evidence.
- Distinguish image validation from physical boot verification.
- Write comments, documentation, and command output in English.

## Contributing to FeROS Builder

Maintained by **Isidro A. López G.**, FeROS Project.

Ideas, experiments, technical review, and contributions are welcome.

## Project Policies

- [Changelog](CHANGELOG.md)
- [Collaborators](COLLABORATORS.md) and [contributing](CONTRIBUTING.md)
- [Code of conduct](CODE_OF_CONDUCT.md) and [security](SECURITY.md)
- [Versioning](VERSIONING.md) and [stability](STABILITY.md)
- [Release procedure](RELEASE.md) and [third-party components](THIRD_PARTY.md)
- [Architecture decisions](docs/adr/README.md)

The release workflow prepares drafts for maintainer review. CI status, private
reporting configuration, and third-party notices must be reviewed before the
first publication. No release has been published merely by adding these files.

## License

FeROS Builder is licensed under the [MIT License](LICENSE).
