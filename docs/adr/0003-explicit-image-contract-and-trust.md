# ADR 0003: Explicit image contract and trust

Status: Accepted

## Context

A correct hash can cover malicious payloads. X55 bring-up evidence must not become an implied guarantee for arbitrary hardware.

## Decision

Keep RK3566 constants in its image implementation, require explicit inputs, and distinguish structural integrity from authenticity and physical boot success. Forensic captures are evidence, not production inputs.

## Consequences

Validation is not an authorization decision. Document parser and filesystem limitations. Changes to layout require public hardware evidence or recorded measurements and regression tests.
