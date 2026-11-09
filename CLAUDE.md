# CLAUDE.md — Automation Architect Agent

> Read this file fully before any change. It is the source of truth for this repo.
> The architecture rules below are **non-negotiable**. If a task seems to require breaking one,
> stop and ask — do not work around it.

## 1. What we are building

An AI agent, built entirely on Claude, that turns a client's plain-language automation request
into a ready-to-run n8n workflow plus a cost/time proposal.

Pipeline (every request goes through these stages, in order):

1. **Intake** — receive the request in natural language (Arabic, French or English).
2. **Clarify** — the agent asks follow-up questions until the spec is complete
   (tools involved, triggers, edge cases, data volume).
3. **Design** — produce a structured `WorkflowSpec` (trigger, steps, integrations, error handling).
4. **Generate** — build the n8n workflow JSON from the spec, then validate it automatically.
5. **Propose** — produce a proposal (estimated hours, cost, assumptions) as PDF.
6. **Review gate** — a human on our team approves or rejects. **Nothing is deployed without approval.**
7. **Deploy** — push the approved workflow to n8n via its REST API, created **inactive**.

The team is made of senior developers. Write code a senior reviewer would merge without comments.

## 2. Stack

| Concern | Choice |
| --- | --- |
| Language | Python 3.12 |
| Agent | Claude Agent SDK (`claude-agent-sdk`) — custom tools exposed as an in-process MCP server |
| API | FastAPI |
| Models / validation | Pydantic v2 |
| Config | pydantic-settings, `.env` (never commit secrets) |
| Persistence | SQLite via SQLAlchemy 2.x (behind a repository port, swappable for Postgres) |
| PDF | WeasyPrint + Jinja2 templates |
| Workflow engine | n8n REST API (`/api/v1/workflows`, header `X-N8N-API-KEY`) |
| Tooling | uv, ruff (lint + format), mypy `--strict`, pytest, import-linter, pre-commit |

Do not add a dependency that is not in this table without asking first.
Before using any Claude Agent SDK or n8n API, check the current official docs — do not rely on memory for signatures.

## 3. Architecture — Hexagonal (Ports & Adapters)

```
src/automation_architect/
├── domain/                 # Pure business logic. No I/O, no frameworks, no SDK imports.
│   ├── models.py           # IntakeSession, WorkflowSpec, Step, Integration, Proposal, ReviewDecision
│   ├── value_objects.py    # Money, Hours, SessionId, WorkflowId ...
│   ├── errors.py           # Domain exceptions
│   └── services/           # Pure domain services (e.g. estimation rules)
│
├── application/            # Use cases + ports. Orchestrates the domain.
│   ├── ports/              # typing.Protocol interfaces ONLY
│   │   ├── agent.py            # AgentPort: clarify(), design_spec()
│   │   ├── workflow_engine.py  # WorkflowEnginePort: validate(), deploy()
│   │   ├── workflow_builder.py # WorkflowBuilderPort: build(spec) -> workflow JSON
│   │   ├── proposal_renderer.py
│   │   └── repositories.py     # SessionRepository, ProposalRepository
│   ├── use_cases/          # One class per use case, single public method `execute`
│   │   ├── start_intake.py
│   │   ├── answer_clarification.py
│   │   ├── generate_workflow.py
│   │   ├── build_proposal.py
│   │   ├── review_proposal.py
│   │   └── deploy_workflow.py
│   └── dto.py              # Input/output DTOs for use cases
│
├── infrastructure/         # Adapters implementing the ports. All I/O lives here.
│   ├── claude/
│   │   ├── agent_adapter.py    # Implements AgentPort with Claude Agent SDK
│   │   ├── tools.py            # Custom tools (@tool) + in-process MCP server
│   │   └── prompts/            # System prompts as versioned .md files, never inline strings
│   ├── n8n/
│   │   ├── client.py           # Thin HTTP client
│   │   ├── builder.py          # Implements WorkflowBuilderPort (spec -> n8n JSON)
│   │   └── engine_adapter.py   # Implements WorkflowEnginePort
│   ├── pdf/renderer.py
│   └── persistence/            # SQLAlchemy models + repository implementations
│
├── interfaces/             # Entry points. Thin: parse input, call a use case, format output.
│   ├── api/                # FastAPI routers + request/response schemas
│   └── cli.py
│
├── config/settings.py
└── bootstrap.py            # Composition root: the ONLY place adapters are wired to ports
```

### Dependency rules (enforced by import-linter in CI)

- `domain` imports nothing from the project except itself.
- `application` imports `domain` only. Ports are `Protocol`s; use cases depend on ports, never on adapters.
- `infrastructure` imports `application` (ports) and `domain`. Never `interfaces`.
- `interfaces` imports `application` (use cases, DTOs) only. Never `infrastructure` directly.
- `bootstrap.py` is the only module allowed to import from every layer.
- `claude_agent_sdk`, `httpx`, `sqlalchemy`, `fastapi`, `weasyprint` may only be imported inside
  `infrastructure/` or `interfaces/` (FastAPI only). Never in `domain` or `application`.

### Design rules

- Dependency injection through constructors. No global state, no service locators, no singletons.
- The LLM is an adapter like any other. Business rules (estimation, validation, the review gate)
  live in `domain`/`application` and are deterministic and unit-testable without Claude.
- The agent returns structured output validated into Pydantic models. Never pass raw LLM text
  between layers. On validation failure: retry once with the error fed back, then raise a domain error.
- Every custom tool the agent can call is a thin wrapper that calls a use case or a port — no business logic in tools.
- The review gate is enforced in `DeployWorkflow.execute`: it raises if the proposal is not `APPROVED`.
  The agent has **no** tool that can deploy.
- Deployed workflows are always created inactive. Activation is a manual step in n8n.
- Prompts are files in `infrastructure/claude/prompts/`, loaded at startup, versioned in git.

## 4. Conventions

- Type hints everywhere; `mypy --strict` must pass. No `Any` without a comment explaining why.
- Naming: use cases are verbs (`GenerateWorkflow`), ports end in `Port` or `Repository`, adapters end in `Adapter`.
- Errors: domain errors in `domain/errors.py`; adapters translate external errors into domain errors.
  Never let `httpx` or SDK exceptions leak past `infrastructure`.
- Logging: `structlog`-style structured logs, one event per use case execution, with session id.
  Never log API keys or client data payloads.
- Config only through `config/settings.py`. No `os.environ` elsewhere.
- Small functions, early returns, no comments that restate the code. Docstrings on public ports and use cases.

## 5. Testing

- `tests/unit/` — domain + use cases with fake adapters (in-memory implementations of the ports). No network.
- `tests/integration/` — adapters against real services, marked `@pytest.mark.integration`, skipped in CI by default.
- `tests/fixtures/requests/` — real-looking client requests (AR/FR/EN) and the expected `WorkflowSpec`.
- Every use case ships with unit tests in the same change. Every bug fix starts with a failing test.
- Never call the real Claude API or n8n in unit tests.

## 6. How you (Claude) must work in this repo

1. **Plan before coding.** For any task touching more than one file, write a short plan
   (files to create/change, which layer each belongs to) and wait for approval.
2. **One phase at a time.** Do not start the next phase from section 7 until the current one meets its acceptance criteria.
3. **Respect the layers.** Before creating a file, state which layer it belongs to and why.
   If something does not fit the structure, stop and propose an ADR in `docs/adr/` instead of improvising.
4. **No silent decisions.** New dependency, schema change, public API change, or deviation from this file → ask first.
5. **Definition of done** for every change: `ruff check`, `ruff format --check`, `mypy --strict`,
   `lint-imports`, `pytest` all green. Run them yourself and report the result.
6. **Ambiguity → ask.** Do not guess business rules (pricing, estimation) — ask, then encode them in `domain`.
7. Keep this file up to date when an approved decision changes the architecture.

## 7. Delivery phases

### Phase 0 — Skeleton (half a day)
- uv project, folder structure from section 3, pre-commit, ruff, mypy, import-linter contracts, pytest.
- `bootstrap.py` wiring with fake adapters; `/health` endpoint.
- **Done when:** all checks green, import-linter contracts fail if a forbidden import is added.

### Phase 1 — Intake & clarification (2 days)
- Domain: `IntakeSession`, `WorkflowSpec` and its parts.
- Use cases: `StartIntake`, `AnswerClarification`.
- `ClaudeAgentAdapter` implementing `AgentPort`; the agent asks questions until the spec is complete,
  then returns a validated `WorkflowSpec`.
- API: `POST /sessions`, `POST /sessions/{id}/messages`, `GET /sessions/{id}`.
- **Done when:** 5 fixture requests produce valid specs end to end; unit tests cover the session state machine.

### Phase 2 — Workflow generation (2 days)
- `N8nWorkflowBuilder` (spec → n8n JSON) and `N8nEngineAdapter.validate`.
- Use case `GenerateWorkflow` with validation; on failure, one repair round through the agent.
- **Done when:** generated JSON imports into a local n8n without manual edits for all fixtures.

### Phase 3 — Proposal & review (1 day)
- Domain estimation service (rules provided by the team — ask for them).
- `BuildProposal` → PDF; `ReviewProposal` (approve / reject with comment).
- **Done when:** a proposal PDF is produced per session and review status is persisted.

### Phase 4 — Deploy (half a day)
- `DeployWorkflow` enforcing the approval gate, creating the workflow inactive in n8n.
- **Done when:** deploying an unapproved proposal raises; an approved one appears inactive in n8n.

### Phase 5 — Context via MCP (later, on request)
- Connect external MCP servers (email, Google Drive, CRM) to enrich intake. Read-only first.

## 8. Out of scope for now

Multi-tenant auth, billing, a frontend beyond a minimal page, auto-activation of workflows,
any write access to client systems other than n8n.
