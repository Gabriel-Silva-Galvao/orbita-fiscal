"""Rotas HTTP da simulação do Asaas, montadas em /asaas-sim.

Mesmos caminhos do Asaas real a partir de /v3. As rotas de /v3/sandbox imitam as ações
que só existem no sandbox; /_eventos é uma extensão da simulação, para inspecionar o que foi gerado.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import JSONResponse

from app.config import get_settings

from .store import SimError, Store


def erro(status: int, code: str, description: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"errors": [{"code": code, "description": description}]})


def lista(itens: list[dict], offset: int, limit: int) -> dict:
    pagina = itens[offset : offset + limit]
    return {"object": "list", "hasMore": offset + limit < len(itens), "totalCount": len(itens), "limit": limit, "offset": offset, "data": pagina}


def criar_router(store: Store) -> APIRouter:
    router = APIRouter(prefix="/asaas-sim", tags=["Asaas (simulação)"])

    # O Asaas usa o cabeçalho "access_token" com sublinhado; sem convert_underscores=False o FastAPI procuraria "access-token".
    def autenticar(access_token: str | None = Header(default=None, convert_underscores=False)) -> None:
        if not access_token:
            raise SimError(401, "access_token_not_found", "O cabeçalho de autenticação 'access_token' é obrigatório.")
        if not access_token.startswith("$aact_"):
            raise SimError(401, "invalid_access_token_format", "O valor do cabeçalho 'access_token' não tem o formato de uma chave do Asaas.")
        if access_token != get_settings().asaas_api_key:
            raise SimError(401, "invalid_access_token", "A chave de API fornecida é inválida.")

    v3 = APIRouter(prefix="/v3", dependencies=[Depends(autenticar)])

    async def corpo(request: Request) -> dict[str, Any]:
        try:
            dados = await request.json()
        except ValueError:
            dados = {}
        return dados if isinstance(dados, dict) else {}

    @v3.post("/customers")
    def criar_cliente(dados: dict = Depends(corpo)):
        with store.trava:
            return store.criar_cliente(dados)

    @v3.get("/customers/{cid}")
    def obter_cliente(cid: str):
        return store.cliente(cid)

    @v3.post("/subscriptions")
    def criar_assinatura(dados: dict = Depends(corpo)):
        with store.trava:
            return store.criar_assinatura(dados)

    @v3.get("/subscriptions/{sid}")
    def obter_assinatura(sid: str):
        return store.assinatura(sid)

    @v3.put("/subscriptions/{sid}")
    def atualizar_assinatura(sid: str, dados: dict = Depends(corpo)):
        with store.trava:
            return store.atualizar_assinatura(sid, dados)

    @v3.delete("/subscriptions/{sid}")
    def cancelar_assinatura(sid: str):
        with store.trava:
            return store.cancelar_assinatura(sid)

    @v3.get("/subscriptions/{sid}/payments")
    def cobrancas_da_assinatura(sid: str, offset: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
        return lista(store.cobrancas_da_assinatura(sid), offset, limit)

    @v3.get("/payments/{pid}")
    def obter_cobranca(pid: str):
        return store.cobranca(pid)

    @v3.get("/payments/{pid}/pixQrCode")
    def pix(pid: str):
        return store.pix_qrcode(pid)

    @v3.get("/payments/{pid}/identificationField")
    def linha(pid: str):
        return store.linha_digitavel(pid)

    @v3.post("/payments/{pid}/refund")
    def estornar(pid: str, dados: dict = Depends(corpo)):
        with store.trava:
            return store.estornar(pid, dados)

    @v3.post("/sandbox/payment/{pid}/confirm")
    def confirmar(pid: str):
        with store.trava:
            return store.confirmar_no_sandbox(pid)

    @v3.post("/sandbox/payment/{pid}/overdue")
    def vencer(pid: str):
        """Extensão da simulação: força o vencimento de uma cobrança pendente."""
        with store.trava:
            return store.forcar_vencimento(pid)

    @v3.post("/webhooks")
    def cadastrar_webhook(dados: dict = Depends(corpo)):
        with store.trava:
            return store.cadastrar_webhook(dados)

    @v3.get("/webhooks")
    def listar_webhooks(offset: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
        itens = [{k: v for k, v in w.items() if not k.startswith("_") and k != "authToken"} for w in store.webhooks.values()]
        return lista(itens, offset, limit)

    router.include_router(v3)

    @router.get("/_eventos", tags=["Asaas (simulação)"])
    def eventos():
        """Extensão da simulação: todos os eventos gerados e as tentativas de entrega."""
        return {"eventos": store.eventos, "entregas": store.entregas}

    return router
