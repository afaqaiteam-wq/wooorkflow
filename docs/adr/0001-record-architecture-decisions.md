# ADR 0001: Record architecture decisions

- Status: Accepted
- Date: 2026-11-09

## Context

`CLAUDE.md` defines a hexagonal architecture whose rules are non-negotiable. Any change
to those rules, or anything that does not fit the structure, must be decided explicitly.

## Decision

Architecture decisions are recorded as numbered Markdown files in `docs/adr/`
(`NNNN-short-title.md`) with the sections Context, Decision and Consequences.
An approved ADR that changes the architecture is reflected in `CLAUDE.md` in the same change.

## Consequences

Deviations from `CLAUDE.md` are proposed as an ADR before any code is written.
