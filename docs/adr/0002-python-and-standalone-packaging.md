# ADR 0002: Python and standalone packaging

Status: Accepted

## Context

The existing Python implementation already expresses the RKNS construction rules. Distribution should not require users to install Python.

## Decision

Preserve the generator and package it with PyInstaller in one-file mode. Use an isolated build environment and test both source and packaged CLI.

## Consequences

Build separately on each host. The runtime is embedded, but host library compatibility, notices, startup extraction, and package size remain relevant. Binary reproducibility is not guaranteed.
