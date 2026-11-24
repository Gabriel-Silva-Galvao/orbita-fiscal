"""Cobrança da Órbita: assinatura, forma de pagamento, cancelamento, reembolso e o webhook do Asaas.

Regra de acesso (planejamento de 24/11/2026):
- libera (ativo) com PAYMENT_CONFIRMED (cartão) ou PAYMENT_RECEIVED (Pix e boleto), o que chegar primeiro;
- nunca libera com PAYMENT_CREATED;
- suspende com PAYMENT_OVERDUE, PAYMENT_CHARGEBACK_REQUESTED ou PAYMENT_REPROVED_BY_RISK_ANALYSIS;
- encerra com PAYMENT_REFUNDED (reembolsado) ou SUBSCRIPTION_DELETED (cancelado).
TODO (login): hoje o usuário vem no corpo da requisição; depois virá da sessão.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.asaas.client import AsaasClient, AsaasError
from app.config import get_settings
from app.db import Banco

PLANOS = {"pro": {"nome": "Pro", "valor": 50.00}, "max": {"nome": "Max", "valor": 75.90}}
FORMAS = {"cartao": "CREDIT_CARD", "pix": "PIX", "boleto": "BOLETO"}
FORMA_DE = {v: k for k, v in FORMAS.items()}
PRAZO_REEMBOLSO_DIAS = 7  # CDC, art. 49
STATUS_FINAIS = {"cancelado", "reembolsado"}

LIBERA = {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"}
SUSPENDE = {"PAYMENT_OVERDUE", "PAYMENT_CHARGEBACK_REQUESTED", "PAYMENT_REPROVED_BY_RISK_ANALYSIS"}


class Cartao(BaseModel):
    titular: str
    numero: str
    mes: str
    ano: str
    cvv: str
    cep: str = Field(default="00000000")
    numero_endereco: str = Field(default="S/N")
    telefone: str | None = None


class NovaAssinatura(BaseModel):
    usuario_id: str
    nome: str
    email: str
    cpf_cnpj: str
    plano: Literal["pro", "max"]
    forma: Literal["cartao", "pix", "boleto"]
    cartao: Cartao | None = None
    ip: str | None = None


class TrocaForma(BaseModel):
    forma: Literal["pix", "boleto"]


def get_banco(request: Request) -> Banco:
    return request.app.state.banco


def get_asaas(request: Request) -> AsaasClient:
    return request.app.state.asaas


def _erro_asaas(e: AsaasError) -> HTTPException:
    status = 400 if e.status < 500 else 502
    return HTTPException(status, detail={"codigo": e.codigo, "mensagem": e.descricao})


def _resumo_cobranca(asaas: AsaasClient, cob: dict) -> dict:
    out = {
        "id": cob["id"],
        "status": cob["status"],
        "valor": cob["value"],
        "vencimento": cob["dueDate"],
        "pago_em": cob.get("paymentDate"),
        "forma": FORMA_DE.get(cob["billingType"], cob["billingType"]),
        "fatura_url": cob.get("invoiceUrl"),
    }
    if cob["status"] in ("PENDING", "OVERDUE"):
        if cob["billingType"] == "PIX":
            qr = asaas.pix_qrcode(cob["id"])
            out["pix"] = {"copia_e_cola": qr["payload"], "imagem_base64": qr["encodedImage"], "expira_em": qr["expirationDate"]}
        elif cob["billingType"] == "BOLETO":
            linha = asaas.linha_digitavel(cob["id"])
            out["boleto"] = {"linha_digitavel": linha["identificationField"], "codigo_barras": linha["barCode"], "pdf_url": cob.get("bankSlipUrl")}
    return out


def _resumo(banco: Banco, asaas: AsaasClient, usuario_id: str) -> dict:
    a = banco.um("SELECT * FROM assinaturas WHERE usuario_id = ?", usuario_id)
    if not a:
        raise HTTPException(404, detail={"codigo": "sem_assinatura", "mensagem": "Esta conta ainda não tem assinatura."})
    try:
        cobrancas = asaas.cobrancas_da_assinatura(a["subscription_id"]) if a["status_acesso"] != "cancelado" else []
        cobrancas_out = [_resumo_cobranca(asaas, c) for c in cobrancas]
    except AsaasError as e:
        if e.status != 404:
            raise _erro_asaas(e)
        cobrancas_out = []
    return {
        "usuario_id": usuario_id,
        "assinatura_id": a["subscription_id"],
        "plano": a["plano"],
        "valor": PLANOS[a["plano"]]["valor"],
        "forma": a["forma"],
        "status_acesso": a["status_acesso"],
        "primeira_paga_em": a["primeira_paga_em"],
        "cobrancas": cobrancas_out,
    }


def _mudar_status(banco: Banco, subscription_id: str, novo: str, pago_em: str | None = None) -> None:
    a = banco.um("SELECT status_acesso FROM assinaturas WHERE subscription_id = ?", subscription_id)
    if not a or a["status_acesso"] in STATUS_FINAIS:
        return  # cancelado e reembolsado não voltam por evento atrasado
    banco.executar(
        "UPDATE assinaturas SET status_acesso = ?, primeira_paga_em = COALESCE(primeira_paga_em, ?), atualizado_em = datetime('now') WHERE subscription_id = ?",
        novo,
        pago_em,
        subscription_id,
    )


def criar_router() -> APIRouter:
    router = APIRouter(tags=["Cobrança"])

    @router.post("/billing/assinaturas", status_code=201)
    def criar_assinatura(dados: NovaAssinatura, banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        atual = banco.um("SELECT status_acesso FROM assinaturas WHERE usuario_id = ?", dados.usuario_id)
        if atual and atual["status_acesso"] not in STATUS_FINAIS:
            raise HTTPException(409, detail={"codigo": "ja_assinante", "mensagem": "Esta conta já tem uma assinatura. Troque o plano ou a forma de pagamento no Portal."})
        if dados.forma == "cartao" and not dados.cartao:
            raise HTTPException(422, detail={"codigo": "cartao_obrigatorio", "mensagem": "Informe os dados do cartão."})

        plano = PLANOS[dados.plano]
        hoje = date.today()
        vencimento = hoje + timedelta(days=3) if dados.forma == "boleto" else hoje
        try:
            cliente = banco.um("SELECT customer_id FROM assinantes WHERE usuario_id = ?", dados.usuario_id)
            if not cliente:
                novo = asaas.criar_cliente(name=dados.nome, email=dados.email, cpfCnpj=dados.cpf_cnpj, externalReference=dados.usuario_id)
                banco.executar(
                    "INSERT INTO assinantes (usuario_id, email, nome, cpf_cnpj, customer_id) VALUES (?, ?, ?, ?, ?)",
                    dados.usuario_id, dados.email, dados.nome, novo["cpfCnpj"], novo["id"],
                )
                cliente = {"customer_id": novo["id"]}
            corpo = {
                "customer": cliente["customer_id"],
                "billingType": FORMAS[dados.forma],
                "value": plano["valor"],
                "nextDueDate": vencimento.isoformat(),
                "cycle": "MONTHLY",
                "description": f"Assinatura Órbita {plano['nome']}",
                "externalReference": dados.usuario_id,
            }
            if dados.cartao:
                c = dados.cartao
                corpo["creditCard"] = {"holderName": c.titular, "number": c.numero, "expiryMonth": c.mes, "expiryYear": c.ano, "ccv": c.cvv}
                corpo["creditCardHolderInfo"] = {"name": dados.nome, "email": dados.email, "cpfCnpj": dados.cpf_cnpj, "postalCode": c.cep, "addressNumber": c.numero_endereco, "phone": c.telefone}
                corpo["remoteIp"] = dados.ip or "127.0.0.1"
            sub = asaas.criar_assinatura(**corpo)
        except AsaasError as e:
            raise _erro_asaas(e)

        banco.executar(
            "INSERT OR REPLACE INTO assinaturas (usuario_id, subscription_id, plano, forma, status_acesso) VALUES (?, ?, ?, ?, 'pendente')",
            dados.usuario_id, sub["id"], dados.plano, dados.forma,
        )
        # O webhook é quem libera. Se o pagamento já veio confirmado na resposta (cartão), aplica a mesma regra
        # na hora, de forma idempotente: o evento que chegar depois não muda nada.
        for cob in asaas.cobrancas_da_assinatura(sub["id"]):
            if cob["status"] in ("CONFIRMED", "RECEIVED"):
                _mudar_status(banco, sub["id"], "ativo", cob.get("paymentDate"))
        return _resumo(banco, asaas, dados.usuario_id)

    @router.get("/billing/assinaturas/{usuario_id}")
    def obter(usuario_id: str, banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        return _resumo(banco, asaas, usuario_id)

    @router.put("/billing/assinaturas/{usuario_id}/forma")
    def trocar_forma(usuario_id: str, dados: TrocaForma, banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        # Para o cartão, a decisão entre a página segura do Asaas e o formulário próprio ainda está em aberto.
        a = banco.um("SELECT * FROM assinaturas WHERE usuario_id = ?", usuario_id)
        if not a or a["status_acesso"] in STATUS_FINAIS:
            raise HTTPException(404, detail={"codigo": "sem_assinatura", "mensagem": "Não há assinatura ativa para trocar a forma de pagamento."})
        try:
            asaas.atualizar_assinatura(a["subscription_id"], billingType=FORMAS[dados.forma], updatePendingPayments=True)
        except AsaasError as e:
            raise _erro_asaas(e)
        banco.executar("UPDATE assinaturas SET forma = ?, atualizado_em = datetime('now') WHERE usuario_id = ?", dados.forma, usuario_id)
        return _resumo(banco, asaas, usuario_id)

    @router.delete("/billing/assinaturas/{usuario_id}")
    def cancelar(usuario_id: str, banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        a = banco.um("SELECT * FROM assinaturas WHERE usuario_id = ?", usuario_id)
        if not a or a["status_acesso"] in STATUS_FINAIS:
            raise HTTPException(404, detail={"codigo": "sem_assinatura", "mensagem": "Não há assinatura para cancelar."})
        try:
            asaas.cancelar_assinatura(a["subscription_id"])
        except AsaasError as e:
            raise _erro_asaas(e)
        banco.executar("UPDATE assinaturas SET status_acesso = 'cancelado', atualizado_em = datetime('now') WHERE usuario_id = ?", usuario_id)
        return {"usuario_id": usuario_id, "status_acesso": "cancelado"}

    @router.post("/billing/assinaturas/{usuario_id}/reembolso")
    def reembolsar(usuario_id: str, banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        a = banco.um("SELECT * FROM assinaturas WHERE usuario_id = ?", usuario_id)
        if not a or not a["primeira_paga_em"]:
            raise HTTPException(400, detail={"codigo": "nada_pago", "mensagem": "Ainda não há pagamento confirmado para reembolsar."})
        if a["status_acesso"] == "reembolsado":
            raise HTTPException(409, detail={"codigo": "ja_reembolsado", "mensagem": "O reembolso desta assinatura já foi pedido."})
        pago_em = date.fromisoformat(a["primeira_paga_em"])
        if (date.today() - pago_em).days > PRAZO_REEMBOLSO_DIAS:
            fim = (pago_em + timedelta(days=PRAZO_REEMBOLSO_DIAS)).strftime("%d/%m/%Y")
            raise HTTPException(400, detail={"codigo": "fora_do_prazo", "mensagem": f"O prazo de 7 dias para reembolso terminou em {fim}. Você ainda pode cancelar, sem multa."})
        try:
            pagas = [c for c in asaas.cobrancas_da_assinatura(a["subscription_id"]) if c["status"] in ("CONFIRMED", "RECEIVED")]
            for cob in pagas:
                asaas.estornar(cob["id"], descricao="Reembolso em até 7 dias (CDC, art. 49)")
            asaas.cancelar_assinatura(a["subscription_id"])
        except AsaasError as e:
            raise _erro_asaas(e)
        banco.executar("UPDATE assinaturas SET status_acesso = 'reembolsado', atualizado_em = datetime('now') WHERE usuario_id = ?", usuario_id)
        return {"usuario_id": usuario_id, "status_acesso": "reembolsado", "cobrancas_estornadas": [c["id"] for c in pagas]}

    @router.post("/webhooks/asaas", tags=["Webhooks"])
    async def webhook(request: Request, asaas_access_token: str | None = Header(default=None, alias="asaas-access-token"), banco: Banco = Depends(get_banco)):
        if asaas_access_token != get_settings().asaas_webhook_token:
            raise HTTPException(401, detail={"codigo": "token_invalido", "mensagem": "Token do webhook inválido."})
        evento = await request.json()
        eid, nome = evento.get("id"), evento.get("event")
        if not eid or not nome:
            raise HTTPException(400, detail={"codigo": "evento_invalido", "mensagem": "Evento sem id ou nome."})
        # Grava antes de processar: se o mesmo evento chegar de novo, responde 200 sem repetir nada.
        if banco.executar("INSERT OR IGNORE INTO eventos_webhook (id, evento) VALUES (?, ?)", eid, nome) == 0:
            return {"ok": True, "duplicado": True}

        pagamento = evento.get("payment") or {}
        assinatura = evento.get("subscription") or {}
        sid = pagamento.get("subscription") or assinatura.get("id")
        if sid:
            if nome in LIBERA:
                _mudar_status(banco, sid, "ativo", pagamento.get("paymentDate") or date.today().isoformat())
            elif nome in SUSPENDE:
                _mudar_status(banco, sid, "suspenso")
            elif nome == "PAYMENT_REFUNDED":
                _mudar_status(banco, sid, "reembolsado")
            elif nome == "SUBSCRIPTION_DELETED":
                _mudar_status(banco, sid, "cancelado")
        return {"ok": True, "evento": nome, "processado_em": datetime.now().isoformat(timespec="seconds")}

    return router
