# FeROS Builder

**Build orchestration, artifact inspection, and boot-image generation for FeROS.**

FeROS Builder is an independent host-side product within the FeROS ecosystem.
It prepares the artifacts required to run FeROS on supported targets.

> **Close to the metal.**
>
> **No magic. Every layer is visible.**

---

## Current Status

The repository is being initialized.

The initial implementation will extract the existing Python image tooling
from FeROS Core and establish an independent build and validation workflow.

No Builder release has been published.

---

## Responsibilities

FeROS Builder owns:

- orchestration of FeROS Core builds;
- inspection of generated artifacts;
- target-specific boot-image construction;
- validation of supported image formats;
- packaging of prepared target artifacts.

Source selection, compiler flags, and linker scripts remain with FeROS Core.
Builder orchestrates that build contract without duplicating it.

---

## Product Boundaries

| Product | Responsibility |
| --- | --- |
| FeROS Core | Operating-system sources, platform implementations, and source-build rules |
| FeROS Builder | Build orchestration, artifact inspection, image construction, and validation |
| FeROS Flasher | Physical-device discovery, media writing, read-back verification, and ejection |

Builder consumes explicit source and firmware inputs.

It does not discover storage devices, write physical media, or invoke
Flasher automatically.

---

## Implementation Direction

The initial implementation uses Python.

Target-specific image formats remain separate from generic orchestration.
The PowKiddy X55 / Rockchip RK3566 is the first image-generation target;
its boot requirements do not define the architecture of Builder.

Forensic captures remain research evidence and must not become implicit
production build inputs.

---

## Engineering Principles

- Keep product responsibilities explicit.
- Preserve reproducible artifact generation.
- Validate image structure and integrity.
- Keep hardware-specific assumptions traceable to evidence.
- Report unsupported targets and operations explicitly.
- Distinguish image validation from physical boot verification.
- Maintain independent versions and releases.
- Write code comments, documentation, and command output in English.

---

## Documentation

Implementation details, supported commands, target contracts, and
development instructions will be documented as they are introduced.

---

## Contributing to FeROS Flasher

Thank you for your interest in contributing to **FeROS**.

FeROS Flasher is part of the **FeROS ecosystem** and provides foundational packages shared across FeROS projects.

- **Original Author:** Isidro A. López G.
- **Organization:** FeROS Project
- **Official Repository:** https://github.com/ialopezg/feros

Ideas, experiments, technical review, and contributions are welcome.

---

## License

FeROS Builder is licensed under the [MIT License](LICENSE).