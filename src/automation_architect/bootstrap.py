"""Composition root: the only module allowed to import from every layer."""

from importlib.metadata import version

import uvicorn
from fastapi import FastAPI

from automation_architect.config.settings import Settings
from automation_architect.interfaces.api.app import build_api

_DISTRIBUTION = "automation-architect"


def create_app(settings: Settings) -> FastAPI:  # noqa: ARG001
    """Wire adapters to ports and return the HTTP application.

    `settings` is unused until Phase 1 wires the first adapters; it is part of
    the signature now so callers do not change when that happens.
    """
    return build_api(title="Automation Architect", version=version(_DISTRIBUTION))


def serve() -> None:
    """Load settings from the environment and run the HTTP server."""
    settings = Settings()
    uvicorn.run(create_app(settings), host=settings.http_host, port=settings.http_port)
