"""FastAPI application entry point (deployed to Cloud Run).

Wires CORS and the routers. Adapters are constructed lazily by the dependency layer, so importing
this module never touches Plaid/Firebase — keeping cold starts cheap and tests light.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    routes_accounts,
    routes_alerts,
    routes_budgets,
    routes_items,
    routes_receipts,
    routes_recurring,
    routes_rules,
    routes_settings,
    routes_transactions,
)
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Personal Finance Assistant API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz", tags=["meta"])
    def healthz() -> dict[str, str]:
        return {"status": "ok", "env": settings.app_env}

    app.include_router(routes_transactions.router)
    app.include_router(routes_accounts.router)
    app.include_router(routes_rules.router)
    app.include_router(routes_budgets.router)
    app.include_router(routes_alerts.router)
    app.include_router(routes_settings.router)
    app.include_router(routes_recurring.router)
    app.include_router(routes_receipts.router)
    app.include_router(routes_receipts.internal_router)
    app.include_router(routes_items.router)
    app.include_router(routes_items.internal_router)
    return app


app = create_app()
