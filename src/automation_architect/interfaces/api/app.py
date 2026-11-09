from fastapi import FastAPI

from automation_architect.interfaces.api.health import build_health_router


def build_api(*, title: str, version: str) -> FastAPI:
    """Assemble the HTTP API from its routers.

    Use cases are passed in as arguments by `bootstrap` as routers are added;
    this module never constructs adapters itself.
    """
    app = FastAPI(title=title, version=version)
    app.include_router(build_health_router())
    return app
