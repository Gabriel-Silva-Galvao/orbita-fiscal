"""Migrações numeradas e modo WAL (preparação para suporte e admin, passo 1)."""
from __future__ import annotations

import sqlite3

import pytest

from app import migracoes
from app.db import Banco

TABELAS = {
    "usuarios", "desafios", "sessoes", "preferencias", "assinantes", "assinaturas", "operacoes_cobranca",
    "eventos_webhook", "reembolso_feedback", "plugin_conexoes", "plugin_uso_ia", "plugin_downloads_feitos",
    "downloads", "alertas", "migracoes",
}


def tabelas(con) -> set[str]:
    return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def test_banco_novo_recebe_o_esquema_inteiro(tmp_path):
    con = Banco(str(tmp_path / "novo.db")).con
    assert migracoes.aplicar(con) == [1, 2]
    assert TABELAS <= tabelas(con)
    assert migracoes.versao_atual(con) == migracoes.MIGRACOES[-1][0]
    assert migracoes.aplicar(con) == []  # rodar de novo não faz nada


def test_banco_antigo_ganha_as_colunas_sem_perder_dados(tmp_path):
    caminho = str(tmp_path / "antigo.db")
    velho = sqlite3.connect(caminho)
    # Como as tabelas eram antes dos itens 1, 7d e 9: sem as colunas novas.
    velho.executescript(
        """
        CREATE TABLE usuarios (id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, nome TEXT NOT NULL, senha_hash TEXT NOT NULL,
                               criado_em TEXT NOT NULL DEFAULT (datetime('now')));
        CREATE TABLE sessoes (token_hash TEXT PRIMARY KEY, usuario_id TEXT NOT NULL, expira REAL NOT NULL);
        CREATE TABLE assinantes (usuario_id TEXT PRIMARY KEY, email TEXT NOT NULL, nome TEXT NOT NULL, cpf_cnpj TEXT NOT NULL,
                                 customer_id TEXT NOT NULL);
        CREATE TABLE assinaturas (usuario_id TEXT PRIMARY KEY, subscription_id TEXT NOT NULL UNIQUE, plano TEXT NOT NULL,
                                  forma TEXT NOT NULL, status_acesso TEXT NOT NULL, primeira_paga_em TEXT,
                                  atualizado_em TEXT NOT NULL DEFAULT (datetime('now')));
        INSERT INTO usuarios (id, email, nome, senha_hash) VALUES ('u1', 'ana@exemplo.test', 'Ana', 'h');
        INSERT INTO sessoes VALUES ('t1', 'u1', 9999999999);
        INSERT INTO assinantes VALUES ('u1', 'ana@exemplo.test', 'Ana', '52998224725', 'cus_1');
        INSERT INTO assinaturas (usuario_id, subscription_id, plano, forma, status_acesso) VALUES ('u1', 'sub_1', 'prata', 'pix', 'ativo');
        """
    )
    velho.close()
    con = Banco(caminho).con
    assert migracoes.aplicar(con) == [1, 2]
    assert {"criada_em", "cancelada_em", "reembolso_em"} <= migracoes._colunas(con, "assinaturas")
    assert {"id", "ultimo_uso", "aparelho"} <= migracoes._colunas(con, "sessoes")
    assert "endereco" in migracoes._colunas(con, "assinantes")
    assert con.execute("SELECT plano FROM assinaturas WHERE usuario_id = 'u1'").fetchone()[0] == "prata"
    assert con.execute("SELECT id FROM sessoes WHERE token_hash = 't1'").fetchone()[0]  # sessão antiga ganhou id


def test_migracao_que_falha_nao_deixa_nada_pela_metade(tmp_path, monkeypatch):
    con = Banco(str(tmp_path / "falha.db")).con
    migracoes.aplicar(con)
    antes = migracoes.versao_atual(con)
    ruim = "CREATE TABLE parcial (x INTEGER); INSERT INTO tabela_que_nao_existe VALUES (1)"
    monkeypatch.setattr(migracoes, "MIGRACOES", [*migracoes.MIGRACOES, (antes + 1, "Quebrada de propósito", ruim)])
    with pytest.raises(sqlite3.OperationalError):
        migracoes.aplicar(con)
    assert "parcial" not in tabelas(con)
    assert migracoes.versao_atual(con) == antes


def test_numeros_repetidos_sao_recusados(tmp_path, monkeypatch):
    con = Banco(str(tmp_path / "rep.db")).con
    monkeypatch.setattr(migracoes, "MIGRACOES", [*migracoes.MIGRACOES, (1, "Repetida", "SELECT 1")])
    with pytest.raises(AssertionError):
        migracoes.aplicar(con)


def test_banco_em_wal_e_com_espera(tmp_path):
    con = Banco(str(tmp_path / "wal.db")).con
    assert con.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    assert con.execute("PRAGMA busy_timeout").fetchone()[0] == 5000


def test_a_api_sobe_com_o_banco_migrado(api):
    _, _, banco = api
    assert migracoes.versao_atual(banco.con) == migracoes.MIGRACOES[-1][0]
