# ADR 0002: Phase 0 structure clarifications

- Status: Accepted
- Date: 2026-11-09

## Context

Building the Phase 0 skeleton surfaced points that `CLAUDE.md` leaves open.

## Decision

1. **Config.** `automation_architect.config` imports nothing from the project, and only
   `bootstrap.py` imports it. Adapters and entry points receive values through constructor
   arguments. Enforced by import-linter.
2. **Fake adapters.** In-memory implementations of the ports live in
   `infrastructure/fakes/`. Production code must not import from `tests/`, and `bootstrap`
   needs fakes for local wiring, so they belong in the adapter layer. Unit tests reuse them.
3. **No speculative ports.** Ports, DTOs and fakes are added in the phase that first needs
   them, so Phase 0 fixes no public API.
4. **`/health` calls no use case.** It is a liveness probe with no business logic.
5. **Server entry point lives in `bootstrap`.** Starting the server requires the composition
   root, which `interfaces` may not import. `bootstrap.serve` is exposed as the
   `automation-architect` console script. `interfaces/cli.py` is added when a real CLI command exists.
6. **Interfaces never import `domain`.** Domain types reach the API only through
   application DTOs.
7. **All stack dependencies are declared from Phase 0**, so import-linter's external-package
   contracts run against real packages. `uvicorn` is added to serve FastAPI. WeasyPrint's
   system libraries (Pango) are installed in Phase 3.

## Consequences

- `CLAUDE.md` section 3 gains `infrastructure/fakes/` and the config rule.
- Still open, to decide before Phase 1: Pydantic vs dataclasses for domain models, and
  `structlog` vs stdlib `logging` for structured logs.
