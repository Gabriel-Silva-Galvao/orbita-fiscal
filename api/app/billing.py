"""Cobrança da Órbita: assinatura, forma de pagamento, cancelamento, reembolso e o webhook do Asaas.

Regra de acesso (planejamento de 24/11/2026):
- libera (ativo) com PAYMENT_CONFIRMED (cartão) ou PAYMENT_RECEIVED (Pix e boleto), o que chegar primeiro;
- nunca libera com PAYMENT_CREATED;
- suspende com PAYMENT_OVERDUE, PAYMENT_CHARGEBACK_REQUESTED ou PAYMENT_REPROVED_BY_RISK_ANALYSIS;
- encerra com PAYMENT_REFUNDED (reembolsado) ou SUBSCRIPTION_DELETED (cancelado).
Etapa 7c: todas as rotas do assinante identificam a pessoa pela sessão (cookie orbita_sessao), nunca
por um id no endereço ou no corpo. Rotas: /billing/assinatura (POST cria, GET consulta, DELETE cancela),
/billing/assinatura/forma (PUT), /billing/assinatura/reembolso (POST), /billing/assinatura/reativar (POST) e,
só com a simulação ligada,
/billing/assinatura/simular-pagamento (POST), que faz o papel do banco confirmando Pix ou boleto.

Passo 2 da preparação (27/11/2026): as regras moram em app/servicos/assinaturas.py; aqui ficam só as rotas HTTP,
que identificam o cliente pela sessão e chamam o serviço com Ator.cliente. Os nomes reexportados abaixo continuam
disponíveis aqui para quem já os importava (alertas, plugin, testes).
"""
from __future__ import annotations

import hmac
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.asaas.client import AsaasClient
from app.auth import usuario_logado
from app.config import get_settings
from app.db import Banco
from app.servicos import assinaturas as servico
from app.servicos.assinaturas import (  # noqa: F401  (reexportados para quem importava de app.billing)
    FORMA_DE,
    FORMAS,
    LIBERA,
    OPERACAO_MAX_SEGUNDOS,
    ORDEM,
    PLANOS,
    PRAZO_REEMBOLSO_DIAS,
    STATUS_FINAIS,
    SUSPENDE,
    proxima_cobranca,
    tem_acesso,
    uma_operacao_por_vez,
)
from app.servicos.base import Ator


class Cartao(BaseModel):
    titular: str = Field(max_length=120)
    numero: str = Field(max_length=25)
    mes: str = Field(max_length=2)
    ano: str = Field(max_length=4)
    cvv: str = Field(max_length=4)
    cep: str = Field(default="00000000", max_length=9)
    numero_endereco: str = Field(default="S/N", max_length=20)
    telefone: str | None = Field(default=None, max_length=20)


class NovaAssinatura(BaseModel):
    # Nome ou razão social e CPF/CNPJ da nota fiscal; o e-mail vem da conta.
    nome: str = Field(max_length=160)
    cpf_cnpj: str = Field(max_length=20)
    plano: Literal["bronze", "prata", "ouro"]
    forma: Literal["cartao", "pix", "boleto"]
    cartao: Cartao | None = None


class Nota(BaseModel):
    nome: str = Field(max_length=160)
    cpf_cnpj: str = Field(max_length=20)
    endereco: str | None = Field(default=None, max_length=300)


class TrocaPlano(BaseModel):
    plano: Literal["bronze", "prata", "ouro"]


class PedidoReembolso(BaseModel):
    """Questionário do reembolso: tudo opcional. O reembolso em 7 dias (CDC, art. 49) não depende de motivo."""
    motivo: Literal["caro", "nao_usei", "dificil", "resultado", "outra_ferramenta", "outro"] | None = None
    melhorar: str | None = Field(default=None, max_length=1000)


class TrocaForma(BaseModel):
    forma: Literal["pix", "boleto"]


def get_banco(request: Request) -> Banco:
    return request.app.state.banco


def get_asaas(request: Request) -> AsaasClient:
    return request.app.state.asaas


def criar_router() -> APIRouter:
    router = APIRouter(tags=["Cobrança"])

    @router.get("/billing/plano")
    def plano_atual(u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco)):
        """Leve, para o header (item 24): só o plano e se dá acesso, sem consultar o Asaas."""
        return servico.plano_atual(banco, u["id"])

    @router.post("/billing/assinatura", status_code=201)
    def criar_assinatura(dados: NovaAssinatura, request: Request, u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        return servico.assinar(
            banco, asaas, Ator.cliente(u["id"]), u["id"], u["email"],
            nome=dados.nome, cpf_cnpj=dados.cpf_cnpj, plano=dados.plano, forma=dados.forma,
            cartao=dados.cartao.model_dump() if dados.cartao else None,
            ip=request.client.host if request.client else "127.0.0.1",
        )

    @router.get("/billing/assinatura")
    def obter(u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        return servico.resumo(banco, asaas, u["id"])

    @router.get("/billing/nota")
    def nota(u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco)):
        """Item 9: dados da nota fiscal (vêm do checkout; null se ainda não houve compra)."""
        return servico.nota(banco, u["id"])

    @router.put("/billing/nota")
    def salvar_nota(dados: Nota, u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        return servico.salvar_nota(banco, asaas, Ator.cliente(u["id"]), u["id"], nome=dados.nome, cpf_cnpj=dados.cpf_cnpj, endereco=dados.endereco)

    @router.put("/billing/assinatura/plano")
    def trocar_plano(dados: TrocaPlano, u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        return servico.trocar_plano(banco, asaas, Ator.cliente(u["id"]), u["id"], dados.plano)

    @router.put("/billing/assinatura/forma")
    def trocar_forma(dados: TrocaForma, u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        return servico.trocar_forma(banco, asaas, Ator.cliente(u["id"]), u["id"], dados.forma)

    @router.delete("/billing/assinatura")
    def cancelar(u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        return servico.cancelar(banco, asaas, Ator.cliente(u["id"]), u["id"])

    @router.post("/billing/assinatura/reativar")
    def reativar(u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        return servico.reativar(banco, asaas, Ator.cliente(u["id"]), u["id"])

    @router.post("/billing/assinatura/reembolso")
    def reembolsar(pedido: PedidoReembolso | None = None, u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        return servico.reembolsar(
            banco, asaas, Ator.cliente(u["id"]), u["id"],
            motivo=pedido.motivo if pedido else None, melhorar=pedido.melhorar if pedido else None,
        )

    @router.post("/billing/assinatura/simular-pagamento")
    def simular_pagamento(u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        """Só na simulação: a liberação segue pelo caminho real (a simulação dispara o webhook e o webhook libera)."""
        if not get_settings().asaas_sim_enabled:
            raise HTTPException(404, detail={"codigo": "indisponivel", "mensagem": "Disponível só na simulação."})
        return servico.simular_pagamento(banco, asaas, Ator.cliente(u["id"]), u["id"])

    @router.post("/webhooks/asaas", tags=["Webhooks"])
    async def webhook(request: Request, asaas_access_token: str | None = Header(default=None, alias="asaas-access-token"), banco: Banco = Depends(get_banco)):
        # Comparação em tempo constante (item 17, S2): não vaza quanto do token acertou.
        if not asaas_access_token or not hmac.compare_digest(asaas_access_token, get_settings().asaas_webhook_token):
            raise HTTPException(401, detail={"codigo": "token_invalido", "mensagem": "Token do webhook inválido."})
        evento = await request.json()
        eid, nome = evento.get("id"), evento.get("event")
        if not eid or not nome:
            raise HTTPException(400, detail={"codigo": "evento_invalido", "mensagem": "Evento sem id ou nome."})
        # Grava antes de processar: se o mesmo evento chegar de novo, responde 200 sem repetir nada.
        if banco.executar("INSERT OR IGNORE INTO eventos_webhook (id, evento) VALUES (?, ?)", eid, nome) == 0:
            return {"ok": True, "duplicado": True}
        servico.aplicar_evento(banco, nome, evento.get("payment") or {}, evento.get("subscription") or {})
        return {"ok": True, "evento": nome, "processado_em": datetime.now().isoformat(timespec="seconds")}

    return router
