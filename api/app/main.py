"""API da Órbita (Python/FastAPI).

Etapa 3 do planejamento: por enquanto, só a simulação do Asaas e o cliente que fala com ela.
As rotas de cobrança da Órbita e o webhook entram na etapa 4.
Rodar: uvicorn app.main:app --reload --port 8000 (dentro de api/).
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.asaas_sim.router import criar_router, erro
from app.asaas_sim.store import SimError, Store
from app.config import get_settings


def create_app(store: Store | None = None) -> FastAPI:
    app = FastAPI(title="API da Órbita", version="0.1.0")
    settings = get_settings()

    @app.exception_handler(SimError)
    async def _sim_error(_: Request, exc: SimError) -> JSONResponse:
        return erro(exc.status, exc.code, exc.description)

    @app.get("/saude", tags=["Sistema"])
    def saude():
        return {"ok": True, "asaas": "simulacao" if settings.asaas_sim_enabled else settings.asaas_base_url}

    if settings.asaas_sim_enabled:
        app.state.asaas_sim = store or Store()
        app.include_router(criar_router(app.state.asaas_sim))

    return app


app = create_app()
