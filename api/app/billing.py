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
"""
from __future__ import annotations

import hmac
import sqlite3
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from typing import Iterator, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.asaas.client import AsaasClient, AsaasError
from app.auth import usuario_logado
from app.config import get_settings
from app.db import Banco
from app.documentos import normalizar_documento

# Item 25 da rodada de testes (25/11/2026): três planos. As especificações de cada um serão definidas depois.
PLANOS = {
    "bronze": {"nome": "Bronze", "valor": 19.90},
    "prata": {"nome": "Prata", "valor": 59.90},
    "ouro": {"nome": "Ouro", "valor": 119.90},
}
FORMAS = {"cartao": "CREDIT_CARD", "pix": "PIX", "boleto": "BOLETO"}
FORMA_DE = {v: k for k, v in FORMAS.items()}
PRAZO_REEMBOLSO_DIAS = 7  # CDC, art. 49
STATUS_FINAIS = {"cancelado", "reembolsado"}


def proxima_cobranca(primeira: str, hoje: date | None = None) -> date:
    """Mesmo dia do mês da primeira cobrança paga, no primeiro mês que ainda está por vir."""
    hoje = hoje or date.today()
    base = date.fromisoformat(primeira)
    n = 1
    while True:
        ano, mes = divmod(base.month - 1 + n, 12)
        ano, mes = base.year + ano, mes + 1
        dia = min(base.day, [31, 29 if ano % 4 == 0 and (ano % 100 or ano % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1])
        d = date(ano, mes, dia)
        if d > hoje:
            return d
        n += 1


def tem_acesso(a: dict, hoje: date | None = None) -> bool:
    """Ativo libera; cancelado a pedido libera até acesso_ate (fim do período pago)."""
    if a["status_acesso"] != "ativo":
        return False
    return not a.get("acesso_ate") or (hoje or date.today()) <= date.fromisoformat(a["acesso_ate"])

LIBERA = {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"}
SUSPENDE = {"PAYMENT_OVERDUE", "PAYMENT_CHARGEBACK_REQUESTED", "PAYMENT_REPROVED_BY_RISK_ANALYSIS"}


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


# Ordem dos planos, do menor ao maior (item 33): só se troca para cima pela API.
ORDEM = ["bronze", "prata", "ouro"]


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
    titular = banco.um("SELECT nome FROM assinantes WHERE usuario_id = ?", usuario_id) or {}
    em_dia = a["status_acesso"] == "ativo" and not a["cancelada_em"]
    return {
        "usuario_id": usuario_id,
        "assinatura_id": a["subscription_id"],
        "plano": a["plano"],
        "valor": PLANOS[a["plano"]]["valor"],
        "forma": a["forma"],
        "final_cartao": a["final_cartao"],
        "nome_nota": titular.get("nome"),
        "status_acesso": a["status_acesso"],
        "tem_acesso": tem_acesso(a),
        "criada_em": a["criada_em"],
        "primeira_paga_em": a["primeira_paga_em"],
        "proxima_cobranca": proxima_cobranca(a["primeira_paga_em"]).isoformat() if em_dia and a["primeira_paga_em"] else None,
        "cancelada_em": a["cancelada_em"],
        "acesso_ate": a["acesso_ate"],
        "reembolso_em": a["reembolso_em"],
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


OPERACAO_MAX_SEGUNDOS = 120  # reserva esquecida (processo caiu no meio) deixa de valer depois disso


@contextmanager
def uma_operacao_por_vez(banco: Banco, usuario_id: str) -> Iterator[None]:
    """ARES-QA-003: conferir e depois agir deixava dois pedidos ao mesmo tempo (clique duplo, duas abas) passarem os
    dois pela conferência e criarem duas assinaturas cobradas no Asaas. A reserva é um INSERT na chave do usuário,
    atômico no SQLite: o segundo pedido falha na hora com 409, antes de qualquer chamada ao Asaas."""
    agora = time.time()
    banco.executar("DELETE FROM operacoes_cobranca WHERE usuario_id = ? AND iniciada < ?", usuario_id, agora - OPERACAO_MAX_SEGUNDOS)
    try:
        banco.executar("INSERT INTO operacoes_cobranca (usuario_id, iniciada) VALUES (?, ?)", usuario_id, agora)
    except sqlite3.IntegrityError:
        raise HTTPException(
            409,
            detail={"codigo": "em_andamento", "mensagem": "Já estamos processando um pedido desta conta. Aguarde alguns segundos e confira em Plano e pagamento."},
        ) from None
    try:
        yield
    finally:
        banco.executar("DELETE FROM operacoes_cobranca WHERE usuario_id = ?", usuario_id)


def criar_router() -> APIRouter:
    router = APIRouter(tags=["Cobrança"])

    @router.get("/billing/plano")
    def plano_atual(u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco)):
        """Leve, para o header (item 24): só o plano e se dá acesso, sem consultar o Asaas."""
        a = banco.um("SELECT * FROM assinaturas WHERE usuario_id = ?", u["id"])
        if not a:
            return {"plano": None, "status_acesso": None, "tem_acesso": False}
        return {"plano": a["plano"], "status_acesso": a["status_acesso"], "tem_acesso": tem_acesso(a)}

    @router.post("/billing/assinatura", status_code=201)
    def criar_assinatura(dados: NovaAssinatura, request: Request, u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        with uma_operacao_por_vez(banco, u["id"]):
            return _criar_assinatura(dados, request, u, banco, asaas)

    def _criar_assinatura(dados: NovaAssinatura, request: Request, u: dict, banco: Banco, asaas: AsaasClient):
        usuario_id, email = u["id"], u["email"]
        doc = normalizar_documento(dados.cpf_cnpj)  # ARES-QA-009: dígito verificador conferido na API
        if not doc or len(dados.nome.strip()) < 2:
            raise HTTPException(422, detail={"codigo": "dados_invalidos", "mensagem": "Informe o nome ou a razão social e um CPF ou CNPJ válido."})
        atual = banco.um("SELECT status_acesso FROM assinaturas WHERE usuario_id = ?", usuario_id)
        if atual and atual["status_acesso"] not in STATUS_FINAIS:
            raise HTTPException(409, detail={"codigo": "ja_assinante", "mensagem": "Esta conta já tem uma assinatura. Troque o plano ou a forma de pagamento no Portal."})
        if dados.forma == "cartao" and not dados.cartao:
            raise HTTPException(422, detail={"codigo": "cartao_obrigatorio", "mensagem": "Informe os dados do cartão."})

        plano = PLANOS[dados.plano]
        hoje = date.today()
        vencimento = hoje + timedelta(days=3) if dados.forma == "boleto" else hoje
        try:
            cliente = banco.um("SELECT customer_id FROM assinantes WHERE usuario_id = ?", usuario_id)
            if not cliente:
                novo = asaas.criar_cliente(name=dados.nome, email=email, cpfCnpj=doc, externalReference=usuario_id)
                banco.executar(
                    "INSERT INTO assinantes (usuario_id, email, nome, cpf_cnpj, customer_id) VALUES (?, ?, ?, ?, ?)",
                    usuario_id, email, dados.nome, novo["cpfCnpj"], novo["id"],
                )
                cliente = {"customer_id": novo["id"]}
            corpo = {
                "customer": cliente["customer_id"],
                "billingType": FORMAS[dados.forma],
                "value": plano["valor"],
                "nextDueDate": vencimento.isoformat(),
                "cycle": "MONTHLY",
                "description": f"Assinatura Órbita {plano['nome']}",
                "externalReference": usuario_id,
            }
            if dados.cartao:
                c = dados.cartao
                corpo["creditCard"] = {"holderName": c.titular, "number": c.numero, "expiryMonth": c.mes, "expiryYear": c.ano, "ccv": c.cvv}
                corpo["creditCardHolderInfo"] = {"name": dados.nome, "email": email, "cpfCnpj": doc, "postalCode": c.cep, "addressNumber": c.numero_endereco, "phone": c.telefone}
                corpo["remoteIp"] = request.client.host if request.client else "127.0.0.1"
            sub = asaas.criar_assinatura(**corpo)
        except AsaasError as e:
            raise _erro_asaas(e)

        banco.executar(
            "INSERT OR REPLACE INTO assinaturas (usuario_id, subscription_id, plano, forma, status_acesso, criada_em, final_cartao) VALUES (?, ?, ?, ?, 'pendente', ?, ?)",
            usuario_id, sub["id"], dados.plano, dados.forma, hoje.isoformat(), dados.cartao.numero[-4:] if dados.cartao else None,
        )
        # O webhook é quem libera. Se o pagamento já veio confirmado na resposta (cartão), aplica a mesma regra
        # na hora, de forma idempotente: o evento que chegar depois não muda nada.
        for cob in asaas.cobrancas_da_assinatura(sub["id"]):
            if cob["status"] in ("CONFIRMED", "RECEIVED"):
                _mudar_status(banco, sub["id"], "ativo", cob.get("paymentDate"))
        return _resumo(banco, asaas, usuario_id)

    @router.get("/billing/assinatura")
    def obter(u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        return _resumo(banco, asaas, u["id"])

    @router.get("/billing/nota")
    def nota(u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco)):
        """Item 9: dados da nota fiscal (vêm do checkout; null se ainda não houve compra)."""
        a = banco.um("SELECT nome, cpf_cnpj, endereco FROM assinantes WHERE usuario_id = ?", u["id"])
        return a

    @router.put("/billing/nota")
    def salvar_nota(dados: Nota, u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        a = banco.um("SELECT customer_id FROM assinantes WHERE usuario_id = ?", u["id"])
        if not a:
            raise HTTPException(409, detail={"codigo": "sem_cadastro", "mensagem": "Os dados da nota são informados na primeira compra."})
        nome = dados.nome.strip()
        doc = normalizar_documento(dados.cpf_cnpj)  # ARES-QA-009: antes só contava 11 ou 14 dígitos
        if len(nome) < 2 or not doc:
            raise HTTPException(422, detail={"codigo": "dados_invalidos", "mensagem": "Informe o nome ou a razão social e um CPF ou CNPJ válido."})
        endereco = (dados.endereco or "").strip() or None
        try:
            extra = {"address": endereco} if endereco else {}
            asaas.atualizar_cliente(a["customer_id"], name=nome, cpfCnpj=doc, **extra)
        except AsaasError as e:
            raise _erro_asaas(e)
        banco.executar("UPDATE assinantes SET nome = ?, cpf_cnpj = ?, endereco = ? WHERE usuario_id = ?", nome, doc, endereco, u["id"])
        return {"nome": nome, "cpf_cnpj": doc, "endereco": endereco}

    @router.put("/billing/assinatura/plano")
    def trocar_plano(dados: TrocaPlano, u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        """Item 33: upgrade para um plano maior, com a assinatura ativa. O novo valor vale nas próximas cobranças
        (como fica a cobrança proporcional no meio do mês: a definir). Plano igual ou menor: 409."""
        with uma_operacao_por_vez(banco, u["id"]):  # CAND-01 a 03: uma operação de cobrança por vez
            a = banco.um("SELECT * FROM assinaturas WHERE usuario_id = ?", u["id"])
            if not a or not tem_acesso(a) or a["cancelada_em"]:
                raise HTTPException(409, detail={"codigo": "sem_assinatura_ativa", "mensagem": "O upgrade precisa de uma assinatura ativa."})
            if ORDEM.index(dados.plano) <= ORDEM.index(a["plano"]):
                raise HTTPException(
                    409,
                    detail={"codigo": "nao_e_upgrade", "mensagem": "Por aqui só dá para subir de plano. Para um plano menor, fale com a equipe."},
                )
            novo = PLANOS[dados.plano]
            try:
                asaas.atualizar_assinatura(
                    a["subscription_id"], value=novo["valor"], description=f"Assinatura Órbita {novo['nome']}", updatePendingPayments=True
                )
            except AsaasError as e:
                raise _erro_asaas(e)
            banco.executar("UPDATE assinaturas SET plano = ?, atualizado_em = datetime('now') WHERE usuario_id = ?", dados.plano, u["id"])
            return _resumo(banco, asaas, u["id"])

    @router.put("/billing/assinatura/forma")
    def trocar_forma(dados: TrocaForma, u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        with uma_operacao_por_vez(banco, u["id"]):  # CAND-01 a 03: uma operação de cobrança por vez
            usuario_id = u["id"]
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

    @router.delete("/billing/assinatura")
    def cancelar(u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        with uma_operacao_por_vez(banco, u["id"]):  # CAND-01 a 03: uma operação de cobrança por vez
            usuario_id = u["id"]
            a = banco.um("SELECT * FROM assinaturas WHERE usuario_id = ?", usuario_id)
            if not a or a["status_acesso"] in STATUS_FINAIS:
                raise HTTPException(404, detail={"codigo": "sem_assinatura", "mensagem": "Não há assinatura para cancelar."})
            if a["cancelada_em"]:
                raise HTTPException(409, detail={"codigo": "ja_cancelada", "mensagem": "O cancelamento já foi pedido."})
            try:
                if a["status_acesso"] == "ativo" and a["primeira_paga_em"]:
                    # Termos de uso: o acesso segue até o fim do período pago. No Asaas, endDate encerra a
                    # assinatura nessa data, sem novas cobranças; reativar é só apagar o endDate.
                    fim = proxima_cobranca(a["primeira_paga_em"])
                    asaas.atualizar_assinatura(a["subscription_id"], endDate=(fim - timedelta(days=1)).isoformat())
                    banco.executar(
                        "UPDATE assinaturas SET cancelada_em = ?, acesso_ate = ?, atualizado_em = datetime('now') WHERE usuario_id = ?",
                        date.today().isoformat(), fim.isoformat(), usuario_id,
                    )
                else:
                    # Nunca pago (ou suspenso): não há período a respeitar; encerra na hora.
                    asaas.cancelar_assinatura(a["subscription_id"])
                    banco.executar(
                        "UPDATE assinaturas SET status_acesso = 'cancelado', cancelada_em = ?, atualizado_em = datetime('now') WHERE usuario_id = ?",
                        date.today().isoformat(), usuario_id,
                    )
            except AsaasError as e:
                raise _erro_asaas(e)
            return _resumo(banco, asaas, usuario_id)

    @router.post("/billing/assinatura/reativar")
    def reativar(u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        with uma_operacao_por_vez(banco, u["id"]):  # CAND-01 a 03: uma operação de cobrança por vez
            a = banco.um("SELECT * FROM assinaturas WHERE usuario_id = ?", u["id"])
            if not a or not a["cancelada_em"] or not tem_acesso(a):
                raise HTTPException(409, detail={"codigo": "nao_reativavel", "mensagem": "Não há cancelamento em andamento para desfazer. Assine de novo pelo site."})
            try:
                asaas.atualizar_assinatura(a["subscription_id"], endDate=None)
            except AsaasError as e:
                raise _erro_asaas(e)
            banco.executar("UPDATE assinaturas SET cancelada_em = NULL, acesso_ate = NULL, atualizado_em = datetime('now') WHERE usuario_id = ?", u["id"])
            return _resumo(banco, asaas, u["id"])

    @router.post("/billing/assinatura/reembolso")
    def reembolsar(pedido: PedidoReembolso | None = None, u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        with uma_operacao_por_vez(banco, u["id"]):  # CAND-01 a 03: uma operação de cobrança por vez
            usuario_id = u["id"]
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
            banco.executar(
                "UPDATE assinaturas SET status_acesso = 'reembolsado', reembolso_em = ?, acesso_ate = NULL, atualizado_em = datetime('now') WHERE usuario_id = ?",
                date.today().isoformat(), usuario_id,
            )
            melhorar = " ".join((pedido.melhorar or "").split()) if pedido else ""
            if pedido and (pedido.motivo or melhorar):
                banco.executar(
                    "INSERT INTO reembolso_feedback (usuario_id, motivo, melhorar) VALUES (?, ?, ?)",
                    usuario_id, pedido.motivo, melhorar or None,
                )
            return {"usuario_id": usuario_id, "status_acesso": "reembolsado", "cobrancas_estornadas": [c["id"] for c in pagas]}

    @router.post("/billing/assinatura/simular-pagamento")
    def simular_pagamento(u: dict = Depends(usuario_logado), banco: Banco = Depends(get_banco), asaas: AsaasClient = Depends(get_asaas)):
        """Só na simulação: confirma as cobranças pendentes, como o banco faria com o Pix ou o boleto.
        A liberação segue pelo caminho real: a simulação dispara o webhook e o webhook libera."""
        if not get_settings().asaas_sim_enabled:
            raise HTTPException(404, detail={"codigo": "indisponivel", "mensagem": "Disponível só na simulação."})
        a = banco.um("SELECT * FROM assinaturas WHERE usuario_id = ?", u["id"])
        if not a:
            raise HTTPException(404, detail={"codigo": "sem_assinatura", "mensagem": "Esta conta ainda não tem assinatura."})
        try:
            for cob in asaas.cobrancas_da_assinatura(a["subscription_id"]):
                if cob["status"] == "PENDING":
                    asaas.confirmar_no_sandbox(cob["id"])
        except AsaasError as e:
            raise _erro_asaas(e)
        return _resumo(banco, asaas, u["id"])

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
