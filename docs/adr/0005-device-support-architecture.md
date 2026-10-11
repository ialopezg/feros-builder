# ADR 0005: Device Support Architecture

**Status:** Accepted

## Context

FeROS Builder requires hardware-specific resources to construct operating system images for different devices.

Repositories, device catalogs, and component releases are managed by FeROS Sources. Builder consumes these resources on demand and prepares the minimum local support required for image construction.

Individual hardware components may evolve independently. Their discovery, installation, and selection must not compromise existing build configurations.

## Decision

FeROS Builder will implement a device support architecture based on the following principles:

1. **Independent ownership:** FeROS Sources owns repository certification, device catalogs, and component publication. Builder remains a consumer.
2. **On-demand consumption:** Builder retrieves device metadata and resources as required, without maintaining authoritative source information.
3. **Non-destructive fetching:** Fetch operations follow `git fetch` semantics for Git-backed resources and report available changes without adopting them.
4. **Independent component versioning:** Bootloaders, DDR initialization resources, firmware, and other components may be installed and versioned independently.
5. **Version coexistence:** Multiple versions of the same component may remain installed locally.
6. **Explicit selection:** Installing a version does not automatically activate it. Updates to the selected configuration require explicit user action.
7. **Compatibility and integrity:** Builder validates component integrity, dependencies, and compatibility before use, without silently updating unrelated components.
8. **Product separation:** Builder prepares resources for image construction. Physical device flashing and verification remain responsibilities of FeROS Flasher.

## Consequences

Device support can evolve independently across hardware targets and components.

Users can discover updates without adopting them, retain known-working configurations, and reproduce builds using selected component versions.

Builder must manage local version state and enforce compatibility constraints, increasing implementation complexity while reducing unintended changes.

The contracts between Sources and Builder require explicit versioning and error handling. Failures in consumed source information must be reported without transferring ownership of Sources responsibilities to Builder.
