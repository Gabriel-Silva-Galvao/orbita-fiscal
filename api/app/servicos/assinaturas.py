"""Regras da cobrança: assinar, trocar plano e forma, cancelar, reativar, reembolsar e o efeito do webhook.

Movido de app/billing.py no passo 2 da preparação (27/11/2026), sem mudar o comportamento: as rotas do cliente
continuam com o mesmo caminho e a mesma resposta. Cada função que muda algo recebe o `Ator`; o cliente só age sobre a
própria conta. O histórico e a auditoria entram no passo 4.
"""
from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from datetime import date, timedelta
from typing import Iterator

from app.asaas.client import AsaasClient, AsaasError
from app.db import Banco
from app.documentos import normalizar_documento
from app.servicos.base import Ator, ErroDeNegocio

# Item 25 da rodada de testes (25/11/2026): três planos. As especificações de cada um serão definidas depois.
PLANOS = {
    "bronze": {"nome": "Bronze", "valor": 19.90},
    "prata": {"nome": "Prata", "valor": 59.90},
    "ouro": {"nome": "Ouro", "valor": 119.90},
}
# Ordem dos planos, do menor ao maior (item 33): o cliente só troca para cima.
ORDEM = ["bronze", "prata", "ouro"]
FORMAS = {"cartao": "CREDIT_CARD", "pix": "PIX", "boleto": "BOLETO"}
FORMA_DE = {v: k for k, v in FORMAS.items()}
PRAZO_REEMBOLSO_DIAS = 7  # CDC, art. 49
STATUS_FINAIS = {"cancelado", "reembolsado"}
LIBERA = {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"}
SUSPENDE = {"PAYMENT_OVERDUE", "PAYMENT_CHARGEBACK_REQUESTED", "PAYMENT_REPROVED_BY_RISK_ANALYSIS"}
OPERACAO_MAX_SEGUNDOS = 120  # reserva esquecida (processo caiu no meio) deixa de valer depois disso


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


def erro_asaas(e: AsaasError) -> ErroDeNegocio:
    return ErroDeNegocio(400 if e.status < 500 else 502, e.codigo, e.descricao)


@contextmanager
def uma_operacao_por_vez(banco: Banco, usuario_id: str) -> Iterator[None]:
    """ARES-QA-003: conferir e depois agir deixava dois pedidos ao mesmo tempo (clique duplo, duas abas) passarem os
    dois pela conferência e criarem duas assinaturas cobradas no Asaas. A reserva é um INSERT na chave do usuário,
    atômico no SQLite: o segundo pedido falha na hora com 409, antes de qualquer chamada ao Asaas. Vale para qualquer
    ator: cliente e equipe mexendo na mesma conta ao mesmo tempo também recebem 409."""
    agora = time.time()
    banco.executar("DELETE FROM operacoes_cobranca WHERE usuario_id = ? AND iniciada < ?", usuario_id, agora - OPERACAO_MAX_SEGUNDOS)
    try:
        banco.executar("INSERT INTO operacoes_cobranca (usuario_id, iniciada) VALUES (?, ?)", usuario_id, agora)
    except sqlite3.IntegrityError:
        raise ErroDeNegocio(
            409, "em_andamento", "Já estamos processando um pedido desta conta. Aguarde alguns segundos e confira em Plano e pagamento."
        ) from None
    try:
        yield
    finally:
        banco.executar("DELETE FROM operacoes_cobranca WHERE usuario_id = ?", usuario_id)


def _assinatura(banco: Banco, usuario_id: str) -> dict | None:
    return banco.um("SELECT * FROM assinaturas WHERE usuario_id = ?", usuario_id)


# ---------- Leitura ----------
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


def resumo(banco: Banco, asaas: AsaasClient, usuario_id: str) -> dict:
    a = _assinatura(banco, usuario_id)
    if not a:
        raise ErroDeNegocio(404, "sem_assinatura", "Esta conta ainda não tem assinatura.")
    try:
        cobrancas = asaas.cobrancas_da_assinatura(a["subscription_id"]) if a["status_acesso"] != "cancelado" else []
        cobrancas_out = [_resumo_cobranca(asaas, c) for c in cobrancas]
    except AsaasError as e:
        if e.status != 404:
            raise erro_asaas(e)
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


def plano_atual(banco: Banco, usuario_id: str) -> dict:
    """Leve, para o header (item 24): só o plano e se dá acesso, sem consultar o Asaas."""
    a = _assinatura(banco, usuario_id)
    if not a:
        return {"plano": None, "status_acesso": None, "tem_acesso": False}
    return {"plano": a["plano"], "status_acesso": a["status_acesso"], "tem_acesso": tem_acesso(a)}


def nota(banco: Banco, usuario_id: str) -> dict | None:
    return banco.um("SELECT nome, cpf_cnpj, endereco FROM assinantes WHERE usuario_id = ?", usuario_id)


# ---------- Mudanças ----------
def mudar_status(banco: Banco, subscription_id: str, novo: str, pago_em: str | None = None, ator: Ator | None = None) -> None:
    """Efeito de um evento do Asaas (ator = sistema). Cancelado e reembolsado não voltam por evento atrasado."""
    a = banco.um("SELECT status_acesso FROM assinaturas WHERE subscription_id = ?", subscription_id)
    if not a or a["status_acesso"] in STATUS_FINAIS:
        return
    banco.executar(
        "UPDATE assinaturas SET status_acesso = ?, primeira_paga_em = COALESCE(primeira_paga_em, ?), atualizado_em = datetime('now') WHERE subscription_id = ?",
        novo, pago_em, subscription_id,
    )


def assinar(
    banco: Banco, asaas: AsaasClient, ator: Ator, usuario_id: str, email: str, *,
    nome: str, cpf_cnpj: str, plano: str, forma: str, cartao: dict | None = None, ip: str = "127.0.0.1",
) -> dict:
    ator.pode_agir_sobre(usuario_id)
    with uma_operacao_por_vez(banco, usuario_id):
        doc = normalizar_documento(cpf_cnpj)  # ARES-QA-009: dígito verificador conferido na API
        if not doc or len(nome.strip()) < 2:
            raise ErroDeNegocio(422, "dados_invalidos", "Informe o nome ou a razão social e um CPF ou CNPJ válido.")
        atual = banco.um("SELECT status_acesso FROM assinaturas WHERE usuario_id = ?", usuario_id)
        if atual and atual["status_acesso"] not in STATUS_FINAIS:
            raise ErroDeNegocio(409, "ja_assinante", "Esta conta já tem uma assinatura. Troque o plano ou a forma de pagamento no Portal.")
        if forma == "cartao" and not cartao:
            raise ErroDeNegocio(422, "cartao_obrigatorio", "Informe os dados do cartão.")

        p = PLANOS[plano]
        hoje = date.today()
        vencimento = hoje + timedelta(days=3) if forma == "boleto" else hoje
        try:
            cliente = banco.um("SELECT customer_id FROM assinantes WHERE usuario_id = ?", usuario_id)
            if not cliente:
                novo = asaas.criar_cliente(name=nome, email=email, cpfCnpj=doc, externalReference=usuario_id)
                banco.executar(
                    "INSERT INTO assinantes (usuario_id, email, nome, cpf_cnpj, customer_id) VALUES (?, ?, ?, ?, ?)",
                    usuario_id, email, nome, novo["cpfCnpj"], novo["id"],
                )
                cliente = {"customer_id": novo["id"]}
            corpo = {
                "customer": cliente["customer_id"],
                "billingType": FORMAS[forma],
                "value": p["valor"],
                "nextDueDate": vencimento.isoformat(),
                "cycle": "MONTHLY",
                "description": f"Assinatura Órbita {p['nome']}",
                "externalReference": usuario_id,
            }
            if cartao:
                c = cartao
                corpo["creditCard"] = {"holderName": c["titular"], "number": c["numero"], "expiryMonth": c["mes"], "expiryYear": c["ano"], "ccv": c["cvv"]}
                corpo["creditCardHolderInfo"] = {
                    "name": nome, "email": email, "cpfCnpj": doc, "postalCode": c["cep"], "addressNumber": c["numero_endereco"], "phone": c["telefone"],
                }
                corpo["remoteIp"] = ip
            sub = asaas.criar_assinatura(**corpo)
        except AsaasError as e:
            raise erro_asaas(e)

        banco.executar(
            "INSERT OR REPLACE INTO assinaturas (usuario_id, subscription_id, plano, forma, status_acesso, criada_em, final_cartao) VALUES (?, ?, ?, ?, 'pendente', ?, ?)",
            usuario_id, sub["id"], plano, forma, hoje.isoformat(), cartao["numero"][-4:] if cartao else None,
        )
        # O webhook é quem libera. Se o pagamento já veio confirmado na resposta (cartão), aplica a mesma regra
        # na hora, de forma idempotente: o evento que chegar depois não muda nada.
        for cob in asaas.cobrancas_da_assinatura(sub["id"]):
            if cob["status"] in ("CONFIRMED", "RECEIVED"):
                mudar_status(banco, sub["id"], "ativo", cob.get("paymentDate"))
        return resumo(banco, asaas, usuario_id)


def salvar_nota(banco: Banco, asaas: AsaasClient, ator: Ator, usuario_id: str, *, nome: str, cpf_cnpj: str, endereco: str | None) -> dict:
    ator.pode_agir_sobre(usuario_id)
    a = banco.um("SELECT customer_id FROM assinantes WHERE usuario_id = ?", usuario_id)
    if not a:
        raise ErroDeNegocio(409, "sem_cadastro", "Os dados da nota são informados na primeira compra.")
    nome = nome.strip()
    doc = normalizar_documento(cpf_cnpj)  # ARES-QA-009: antes só contava 11 ou 14 dígitos
    if len(nome) < 2 or not doc:
        raise ErroDeNegocio(422, "dados_invalidos", "Informe o nome ou a razão social e um CPF ou CNPJ válido.")
    endereco = (endereco or "").strip() or None
    try:
        extra = {"address": endereco} if endereco else {}
        asaas.atualizar_cliente(a["customer_id"], name=nome, cpfCnpj=doc, **extra)
    except AsaasError as e:
        raise erro_asaas(e)
    banco.executar("UPDATE assinantes SET nome = ?, cpf_cnpj = ?, endereco = ? WHERE usuario_id = ?", nome, doc, endereco, usuario_id)
    return {"nome": nome, "cpf_cnpj": doc, "endereco": endereco}


def trocar_plano(banco: Banco, asaas: AsaasClient, ator: Ator, usuario_id: str, plano: str) -> dict:
    """Item 33: o cliente só sobe de plano, com a assinatura ativa. O novo valor vale nas próximas cobranças (como fica
    a cobrança proporcional no meio do mês: a definir, ARES-QA-008). Plano igual ou menor: 409."""
    ator.pode_agir_sobre(usuario_id)
    with uma_operacao_por_vez(banco, usuario_id):
        a = _assinatura(banco, usuario_id)
        if not a or not tem_acesso(a) or a["cancelada_em"]:
            raise ErroDeNegocio(409, "sem_assinatura_ativa", "O upgrade precisa de uma assinatura ativa.")
        if ORDEM.index(plano) <= ORDEM.index(a["plano"]):
            raise ErroDeNegocio(409, "nao_e_upgrade", "Por aqui só dá para subir de plano. Para um plano menor, fale com a equipe.")
        novo = PLANOS[plano]
        try:
            asaas.atualizar_assinatura(a["subscription_id"], value=novo["valor"], description=f"Assinatura Órbita {novo['nome']}", updatePendingPayments=True)
        except AsaasError as e:
            raise erro_asaas(e)
        banco.executar("UPDATE assinaturas SET plano = ?, atualizado_em = datetime('now') WHERE usuario_id = ?", plano, usuario_id)
        return resumo(banco, asaas, usuario_id)


def trocar_forma(banco: Banco, asaas: AsaasClient, ator: Ator, usuario_id: str, forma: str) -> dict:
    ator.pode_agir_sobre(usuario_id)
    with uma_operacao_por_vez(banco, usuario_id):
        # Para o cartão, a decisão entre a página segura do Asaas e o formulário próprio ainda está em aberto (S3).
        a = _assinatura(banco, usuario_id)
        if not a or a["status_acesso"] in STATUS_FINAIS:
            raise ErroDeNegocio(404, "sem_assinatura", "Não há assinatura ativa para trocar a forma de pagamento.")
        try:
            asaas.atualizar_assinatura(a["subscription_id"], billingType=FORMAS[forma], updatePendingPayments=True)
        except AsaasError as e:
            raise erro_asaas(e)
        banco.executar("UPDATE assinaturas SET forma = ?, atualizado_em = datetime('now') WHERE usuario_id = ?", forma, usuario_id)
        return resumo(banco, asaas, usuario_id)


def cancelar(banco: Banco, asaas: AsaasClient, ator: Ator, usuario_id: str) -> dict:
    ator.pode_agir_sobre(usuario_id)
    with uma_operacao_por_vez(banco, usuario_id):
        a = _assinatura(banco, usuario_id)
        if not a or a["status_acesso"] in STATUS_FINAIS:
            raise ErroDeNegocio(404, "sem_assinatura", "Não há assinatura para cancelar.")
        if a["cancelada_em"]:
            raise ErroDeNegocio(409, "ja_cancelada", "O cancelamento já foi pedido.")
        try:
            if a["status_acesso"] == "ativo" and a["primeira_paga_em"]:
                # Termos de uso: o acesso segue até o fim do período pago. No Asaas, endDate encerra a assinatura
                # nessa data, sem novas cobranças; reativar é só apagar o endDate.
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
            raise erro_asaas(e)
        return resumo(banco, asaas, usuario_id)


def reativar(banco: Banco, asaas: AsaasClient, ator: Ator, usuario_id: str) -> dict:
    ator.pode_agir_sobre(usuario_id)
    with uma_operacao_por_vez(banco, usuario_id):
        a = _assinatura(banco, usuario_id)
        if not a or not a["cancelada_em"] or not tem_acesso(a):
            raise ErroDeNegocio(409, "nao_reativavel", "Não há cancelamento em andamento para desfazer. Assine de novo pelo site.")
        try:
            asaas.atualizar_assinatura(a["subscription_id"], endDate=None)
        except AsaasError as e:
            raise erro_asaas(e)
        banco.executar("UPDATE assinaturas SET cancelada_em = NULL, acesso_ate = NULL, atualizado_em = datetime('now') WHERE usuario_id = ?", usuario_id)
        return resumo(banco, asaas, usuario_id)


def reembolsar(banco: Banco, asaas: AsaasClient, ator: Ator, usuario_id: str, *, motivo: str | None = None, melhorar: str | None = None) -> dict:
    """Hoje estorna na hora (até o passo 6, quando o reembolso vira pedido aprovado pela equipe)."""
    ator.pode_agir_sobre(usuario_id)
    with uma_operacao_por_vez(banco, usuario_id):
        a = _assinatura(banco, usuario_id)
        if not a or not a["primeira_paga_em"]:
            raise ErroDeNegocio(400, "nada_pago", "Ainda não há pagamento confirmado para reembolsar.")
        if a["status_acesso"] == "reembolsado":
            raise ErroDeNegocio(409, "ja_reembolsado", "O reembolso desta assinatura já foi pedido.")
        pago_em = date.fromisoformat(a["primeira_paga_em"])
        if (date.today() - pago_em).days > PRAZO_REEMBOLSO_DIAS:
            fim = (pago_em + timedelta(days=PRAZO_REEMBOLSO_DIAS)).strftime("%d/%m/%Y")
            raise ErroDeNegocio(400, "fora_do_prazo", f"O prazo de 7 dias para reembolso terminou em {fim}. Você ainda pode cancelar, sem multa.")
        try:
            pagas = [c for c in asaas.cobrancas_da_assinatura(a["subscription_id"]) if c["status"] in ("CONFIRMED", "RECEIVED")]
            for cob in pagas:
                asaas.estornar(cob["id"], descricao="Reembolso em até 7 dias (CDC, art. 49)")
            asaas.cancelar_assinatura(a["subscription_id"])
        except AsaasError as e:
            raise erro_asaas(e)
        banco.executar(
            "UPDATE assinaturas SET status_acesso = 'reembolsado', reembolso_em = ?, acesso_ate = NULL, atualizado_em = datetime('now') WHERE usuario_id = ?",
            date.today().isoformat(), usuario_id,
        )
        from app.plugin import resumo_de_uso  # import local: plugin.py importa deste módulo

        melhorar = " ".join((melhorar or "").split())
        uso = json.dumps(resumo_de_uso(banco, usuario_id), ensure_ascii=False)
        banco.executar(
            "INSERT INTO reembolso_feedback (usuario_id, motivo, melhorar, uso_plugin) VALUES (?, ?, ?, ?)",
            usuario_id, motivo, melhorar or None, uso,
        )
        return {"usuario_id": usuario_id, "status_acesso": "reembolsado", "cobrancas_estornadas": [c["id"] for c in pagas]}


def simular_pagamento(banco: Banco, asaas: AsaasClient, ator: Ator, usuario_id: str) -> dict:
    """Só na simulação: confirma as cobranças pendentes, como o banco faria com o Pix ou o boleto."""
    ator.pode_agir_sobre(usuario_id)
    a = _assinatura(banco, usuario_id)
    if not a:
        raise ErroDeNegocio(404, "sem_assinatura", "Esta conta ainda não tem assinatura.")
    try:
        for cob in asaas.cobrancas_da_assinatura(a["subscription_id"]):
            if cob["status"] == "PENDING":
                asaas.confirmar_no_sandbox(cob["id"])
    except AsaasError as e:
        raise erro_asaas(e)
    return resumo(banco, asaas, usuario_id)


def aplicar_evento(banco: Banco, nome: str, pagamento: dict, assinatura: dict) -> None:
    """Efeito de um evento do webhook do Asaas (ator = sistema)."""
    sid = pagamento.get("subscription") or assinatura.get("id")
    if not sid:
        return
    sistema = Ator.sistema("webhook_asaas")
    if nome in LIBERA:
        mudar_status(banco, sid, "ativo", pagamento.get("paymentDate") or date.today().isoformat(), ator=sistema)
    elif nome in SUSPENDE:
        mudar_status(banco, sid, "suspenso", ator=sistema)
    elif nome == "PAYMENT_REFUNDED":
        mudar_status(banco, sid, "reembolsado", ator=sistema)
    elif nome == "SUBSCRIPTION_DELETED":
        mudar_status(banco, sid, "cancelado", ator=sistema)
