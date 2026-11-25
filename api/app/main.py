"""API da Órbita (Python/FastAPI).

- /auth: conta, login com código por e-mail e sessão (etapa 7a).
- /billing e /webhooks/asaas: cobrança da Órbita e liberação do acesso (etapa 4).
- /asaas-sim: simulação do Asaas, enquanto não há conta (etapa 3).
Rodar: uvicorn app.main:app --reload --port 8000 (dentro de api/).
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import auth, billing, contato, plugin
from app.asaas.client import AsaasClient
from app.asaas_sim.router import criar_router, erro
from app.asaas_sim.store import SimError, Store
from app.config import get_settings, problemas_de_producao
from app.db import Banco

# Eventos que a Órbita assina no webhook do Asaas.
EVENTOS_WEBHOOK = [
    "PAYMENT_CREATED",
    "PAYMENT_CONFIRMED",
    "PAYMENT_RECEIVED",
    "PAYMENT_OVERDUE",
    "PAYMENT_REFUNDED",
    "PAYMENT_PARTIALLY_REFUNDED",
    "PAYMENT_CHARGEBACK_REQUESTED",
    "PAYMENT_REPROVED_BY_RISK_ANALYSIS",
    "PAYMENT_DELETED",
    "SUBSCRIPTION_DELETED",
    "SUBSCRIPTION_INACTIVATED",
]


def create_app(store: Store | None = None, banco: Banco | None = None, asaas: AsaasClient | None = None) -> FastAPI:
    settings = get_settings()
    # Item 17: a API se recusa a subir com configuração perigosa (simulação em produção, segredos de exemplo).
    erros = problemas_de_producao(settings)
    if erros:
        raise RuntimeError("Configuração insegura da API:\n- " + "\n- ".join(erros))
    app = FastAPI(title="API da Órbita", version="0.2.0")
    app.state.banco = banco or Banco(settings.database_path)
    with app.state.banco.trava:
        app.state.banco.con.executescript(auth.ESQUEMA)
        auth.migrar(app.state.banco.con)
        app.state.banco.con.executescript(plugin.ESQUEMA)
        app.state.banco.con.executescript(contato.ESQUEMA)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.site_url],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )
    app.state.asaas = asaas or AsaasClient(settings.asaas_base_url, settings.asaas_api_key)

    @app.exception_handler(SimError)
    async def _sim_error(_: Request, exc: SimError) -> JSONResponse:
        return erro(exc.status, exc.code, exc.description)

    @app.get("/saude", tags=["Sistema"])
    def saude():
        return {"ok": True, "asaas": "simulacao" if settings.asaas_sim_enabled else settings.asaas_base_url}

    if settings.asaas_sim_enabled:
        app.state.asaas_sim = store or Store()
        # Na simulação, o webhook da Órbita já nasce cadastrado. No Asaas real, cadastre pelo painel
        # (Integrações > Webhooks) ou por POST /v3/webhooks, com a mesma URL, token e eventos.
        app.state.asaas_sim.cadastrar_webhook(
            {
                "name": "Órbita",
                "url": f"{settings.api_public_url}/webhooks/asaas",
                "email": "dev@orbita.local",
                "enabled": True,
                "interrupted": False,
                "sendType": "SEQUENTIALLY",
                "events": EVENTOS_WEBHOOK,
                "authToken": settings.asaas_webhook_token,
            }
        )
        app.include_router(criar_router(app.state.asaas_sim))

    app.include_router(auth.criar_router())
    app.include_router(billing.criar_router())
    app.include_router(plugin.criar_router())
    app.include_router(contato.criar_router())
    return app


app = create_app()
