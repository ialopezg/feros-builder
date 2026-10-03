# ADR 0001: Independent product boundaries

Status: Accepted

## Context

The image generator originated inside FeROS Core. A standalone tool must work without a neighboring source checkout.

## Decision

Builder owns image construction and validation from explicit payload paths. The workspace owns orchestration and firmware selection; Core owns OS implementation; Flasher owns physical-media operations. Keep sources directly under src/.

## Consequences

The CLI receives paths from its caller. Product tests cannot depend on Core, firmware bundles, privileged operations, or a workspace layout.
