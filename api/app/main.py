"""API da Órbita (Python/FastAPI).

- /auth: conta, login com código por e-mail e sessão (etapa 7a).
- /billing e /webhooks/asaas: cobrança da Órbita e liberação do acesso (etapa 4).
- /asaas-sim: simulação do Asaas, enquanto não há conta (etapa 3).
Rodar: uvicorn app.main:app --reload --port 8000 (dentro de api/).
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import alertas, auth, billing, contato, plugin
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



class LimiteDeCorpo:
    """Recusa com 413 o pedido cujo corpo passa do limite, pelo Content-Length ou contando o que chega aos pedaços."""

    def __init__(self, app, maximo: int):
        self.app, self.maximo = app, maximo

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        for nome, valor in scope.get("headers", []):
            if nome == b"content-length" and valor.isdigit() and int(valor) > self.maximo:
                return await self._recusar(send)
        recebido = 0

        async def receber():
            nonlocal recebido
            msg = await receive()
            if msg["type"] == "http.request":
                recebido += len(msg.get("body", b""))
                if recebido > self.maximo:
                    raise _CorpoGrande()
            return msg

        try:
            await self.app(scope, receber, send)
        except _CorpoGrande:
            await self._recusar(send)

    @staticmethod
    async def _recusar(send):
        corpo = b'{"codigo":"pedido_grande","descricao":"O pedido passou do tamanho permitido."}'
        await send({"type": "http.response.start", "status": 413,
                    "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(corpo)).encode())]})
        await send({"type": "http.response.body", "body": corpo})


class _CorpoGrande(Exception):
    pass


class ConfereOrigem:
    """Risco S8 (CSRF): SameSite=Lax e o CORS fechado barram o ataque comum, mas um subdomínio comprometido do mesmo site
    ainda conseguiria mandar um POST com o cookie. Pedido que muda estado (POST, PUT, PATCH, DELETE) vindo de navegador
    traz o cabeçalho Origin; se ele não for o do site (SITE_URL), a API recusa com 403. Sem Origin (webhook do Asaas,
    servidor MCP, chamadas de servidor), segue como antes."""

    MUDAM_ESTADO = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, app, permitidas: set[str]):
        self.app, self.permitidas = app, {o.rstrip("/").lower() for o in permitidas}

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["method"] in self.MUDAM_ESTADO:
            origem = next((v.decode("latin-1") for n, v in scope.get("headers", []) if n == b"origin"), None)
            if origem is not None and origem.rstrip("/").lower() not in self.permitidas:
                corpo = b'{"codigo":"origem_recusada","descricao":"Pedido de outro site recusado."}'
                await send({"type": "http.response.start", "status": 403,
                            "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(corpo)).encode())]})
                await send({"type": "http.response.body", "body": corpo})
                return
        await self.app(scope, receive, send)


class CabecalhosDeSeguranca:
    """ARES-QA-004 (S7): cabeçalhos de segurança em toda resposta da API. A API só devolve JSON, então a CSP proíbe tudo;
    a exceção é a documentação de desenvolvimento (/docs e /redoc carregam o Swagger de um CDN). HSTS só com HTTPS."""

    BASE = [
        (b"x-content-type-options", b"nosniff"),
        (b"x-frame-options", b"DENY"),
        (b"referrer-policy", b"strict-origin-when-cross-origin"),
    ]
    CSP = (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
    HSTS = (b"strict-transport-security", b"max-age=31536000; includeSubDomains")
    DOCS = ("/docs", "/redoc")

    def __init__(self, app, hsts: bool):
        self.app, self.hsts = app, hsts

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        extras = list(self.BASE)
        if not scope.get("path", "").startswith(self.DOCS):
            extras.append(self.CSP)
        if self.hsts:
            extras.append(self.HSTS)

        async def enviar(msg):
            if msg["type"] == "http.response.start":
                ja = {n.lower() for n, _ in msg.get("headers", [])}
                msg["headers"] = list(msg.get("headers", [])) + [(n, v) for n, v in extras if n not in ja]
            await send(msg)

        await self.app(scope, receive, enviar)

def create_app(store: Store | None = None, banco: Banco | None = None, asaas: AsaasClient | None = None) -> FastAPI:
    settings = get_settings()
    # Item 17: a API se recusa a subir com configuração perigosa (simulação em produção, segredos de exemplo).
    erros = problemas_de_producao(settings)
    if erros:
        raise RuntimeError("Configuração insegura da API:\n- " + "\n- ".join(erros))
    # ARES-QA-005 (S6): em produção, sem /docs, /redoc e /openapi.json (o mapa de todas as rotas fica só no desenvolvimento).
    dev = settings.orbita_env == "development"
    app = FastAPI(
        title="API da Órbita", version="0.2.0",
        docs_url="/docs" if dev else None, redoc_url="/redoc" if dev else None, openapi_url="/openapi.json" if dev else None,
    )
    app.state.banco = banco or Banco(settings.database_path)
    with app.state.banco.trava:
        app.state.banco.con.executescript(auth.ESQUEMA)
        auth.migrar(app.state.banco.con)
        app.state.banco.con.executescript(plugin.ESQUEMA)
        app.state.banco.con.executescript(contato.ESQUEMA)
        app.state.banco.con.executescript(alertas.ESQUEMA)
    # Segurança (26/11/2026): nenhum pedido passa de 64 KB (os maiores, webhook do Asaas e contato, ficam bem abaixo).
    app.add_middleware(LimiteDeCorpo, maximo=64 * 1024)
    app.add_middleware(ConfereOrigem, permitidas={settings.site_url})
    app.add_middleware(CabecalhosDeSeguranca, hsts=settings.cookie_secure)  # por fora: vale até para o 413
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
        if store is None:
            # Uso local: a simulação sobrevive a reinícios da API, guardada ao lado do banco.
            arquivo_sim = str(Path(settings.database_path).with_suffix("")) + "-asaas-sim.json"
            app.state.asaas_sim.carregar(arquivo_sim)

            @app.middleware("http")
            async def _guardar_sim(request: Request, call_next):
                resposta = await call_next(request)
                if request.method != "GET" and request.url.path.startswith("/asaas-sim/"):
                    app.state.asaas_sim.salvar(arquivo_sim)
                return resposta
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

    rotas_auth = auth.criar_router()
    app.state.limitador_login = rotas_auth.limitador
    app.include_router(rotas_auth)
    app.include_router(billing.criar_router())
    app.include_router(plugin.criar_router())
    app.include_router(contato.criar_router())
    app.include_router(alertas.criar_router())
    return app


app = create_app()
