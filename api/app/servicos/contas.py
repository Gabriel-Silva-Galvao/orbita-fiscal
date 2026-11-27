"""Regras da conta: situação (ativa ou suspensa), sessões, nome, exclusão e última atividade.

Passo 3 da preparação (27/11/2026). As rotas de /auth continuam com o mesmo caminho e a mesma resposta; o que é novo
é a situação da conta (a equipe poderá suspender, passo 7) e a `ultima_atividade` (usuários online, admin.md).
"""
from __future__ import annotations

import time

from app.db import Banco
from app.servicos.base import Ator, ErroDeNegocio

ATIVIDADE_PASSO = 60  # grava a última atividade no máximo uma vez por minuto por conta (não pesa no banco)
MOTIVO_MIN, MOTIVO_MAX = 3, 300


def situacao(banco: Banco, usuario_id: str) -> str | None:
    u = banco.um("SELECT situacao FROM usuarios WHERE id = ?", usuario_id)
    return u["situacao"] if u else None


def registrar_atividade(banco: Banco, usuario_id: str, ultima: float | None, agora: float | None = None) -> None:
    """Marca que a conta está em uso (site, Portal ou plugin). `ultima` é o valor já lido, para evitar outra consulta."""
    agora = agora or time.time()
    if not ultima or agora - ultima > ATIVIDADE_PASSO:
        banco.executar("UPDATE usuarios SET ultima_atividade = ? WHERE id = ?", agora, usuario_id)


def _motivo(motivo: str | None) -> str:
    m = " ".join((motivo or "").split())
    if not MOTIVO_MIN <= len(m) <= MOTIVO_MAX:
        raise ErroDeNegocio(422, "motivo_obrigatorio", f"Escreva o motivo, entre {MOTIVO_MIN} e {MOTIVO_MAX} caracteres.")
    return m


def suspender(banco: Banco, ator: Ator, usuario_id: str, motivo: str | None) -> dict:
    """Bloqueia a conta e derruba todas as sessões. Só a equipe ou o sistema suspendem, sempre com motivo.
    (Se a suspensão também cancela a cobrança no Asaas está em aberto: preparacao-suporte-admin.md, seção 12.)"""
    if ator.tipo == "cliente":
        raise ErroDeNegocio(403, "sem_permissao", "Só a equipe da Órbita suspende contas.")
    m = _motivo(motivo)
    if not banco.executar(
        "UPDATE usuarios SET situacao = 'suspensa', suspensa_em = datetime('now'), suspensa_motivo = ? WHERE id = ? AND situacao = 'ativa'",
        m, usuario_id,
    ):
        if not situacao(banco, usuario_id):
            raise ErroDeNegocio(404, "conta_inexistente", "Conta não encontrada.")
        raise ErroDeNegocio(409, "ja_suspensa", "Esta conta já está suspensa.")
    encerrar_sessoes(banco, ator, usuario_id)
    return {"usuario_id": usuario_id, "situacao": "suspensa", "motivo": m}


def reativar(banco: Banco, ator: Ator, usuario_id: str, motivo: str | None) -> dict:
    if ator.tipo == "cliente":
        raise ErroDeNegocio(403, "sem_permissao", "Só a equipe da Órbita reativa contas.")
    _motivo(motivo)
    if not banco.executar(
        "UPDATE usuarios SET situacao = 'ativa', suspensa_em = NULL, suspensa_motivo = NULL WHERE id = ? AND situacao = 'suspensa'", usuario_id
    ):
        raise ErroDeNegocio(409, "nao_suspensa", "Esta conta não está suspensa.")
    return {"usuario_id": usuario_id, "situacao": "ativa"}


def encerrar_sessoes(banco: Banco, ator: Ator, usuario_id: str, manter_sessao_id: str | None = None) -> int:
    """Encerra todas as sessões da conta (ou todas menos a atual). Devolve quantas saíram."""
    ator.pode_agir_sobre(usuario_id)
    if manter_sessao_id:
        return banco.executar("DELETE FROM sessoes WHERE usuario_id = ? AND id <> ?", usuario_id, manter_sessao_id)
    return banco.executar("DELETE FROM sessoes WHERE usuario_id = ?", usuario_id)


def encerrar_sessao(banco: Banco, ator: Ator, usuario_id: str, sessao_id: str) -> None:
    """Encerra uma sessão da conta. O id de uma sessão de outra pessoa não é achado (404)."""
    ator.pode_agir_sobre(usuario_id)
    if not banco.executar("DELETE FROM sessoes WHERE id = ? AND usuario_id = ?", sessao_id, usuario_id):
        raise ErroDeNegocio(404, "nao_achada", "Essa sessão já foi encerrada.")


def trocar_nome(banco: Banco, ator: Ator, usuario_id: str, nome: str) -> str:
    ator.pode_agir_sobre(usuario_id)
    nome = nome.strip()
    if not 2 <= len(nome) <= 120:
        raise ErroDeNegocio(422, "nome_invalido", "Escreva um nome entre 2 e 120 caracteres.")
    banco.executar("UPDATE usuarios SET nome = ? WHERE id = ?", nome, usuario_id)
    return nome


def excluir(banco: Banco, ator: Ator, usuario_id: str, email: str) -> None:
    """Apaga a conta e o login. Dados de cobrança (assinantes, assinaturas) ficam pelo prazo legal de guarda fiscal."""
    ator.pode_agir_sobre(usuario_id)
    a = banco.um("SELECT status_acesso, cancelada_em FROM assinaturas WHERE usuario_id = ?", usuario_id)
    if a and a["status_acesso"] not in ("cancelado", "reembolsado") and not a["cancelada_em"]:
        raise ErroDeNegocio(409, "assinatura_ativa", "Cancele a assinatura antes de excluir a conta, para não haver nova cobrança.")
    banco.executar("DELETE FROM sessoes WHERE usuario_id = ?", usuario_id)
    banco.executar("DELETE FROM desafios WHERE email = ?", email)
    banco.executar("DELETE FROM preferencias WHERE usuario_id = ?", usuario_id)
    banco.executar("DELETE FROM usuarios WHERE id = ?", usuario_id)
