# ADR 0004: Tested draft releases

Status: Proposed

## Context

A public executable needs a traceable source commit, tests, and a reviewable distribution process.

## Decision

Use pinned Actions, read-only build jobs, source and executable tests, archive verification, and a separate narrowly privileged job that creates a draft from an existing version tag. Publish manually after review.

## Consequences

Tags and assets become immutable after publication. First CI execution, private reporting configuration, and third-party notice review remain release tasks. No signing or provenance guarantee is implied.
