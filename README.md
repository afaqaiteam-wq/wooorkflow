# Automation Architect

AI agent that turns a plain-language automation request into an n8n workflow and a
cost/time proposal. See [CLAUDE.md](CLAUDE.md) for architecture, conventions and phases,
and [docs/adr/](docs/adr/) for decisions.

## Development

```bash
uv sync
cp .env.example .env
uv run pre-commit install

uv run ruff check && uv run ruff format --check
uv run mypy
uv run lint-imports
uv run pytest

uv run automation-architect   # serves the API, GET /health
```
