"""Banco da API (SQLite, sem dependências extras). As tabelas vêm das migrações numeradas (app/migracoes.py)."""
from __future__ import annotations

import sqlite3
import threading

ESQUEMA = """
CREATE TABLE IF NOT EXISTS assinantes (
    usuario_id   TEXT PRIMARY KEY,
    email        TEXT NOT NULL,
    nome         TEXT NOT NULL,
    cpf_cnpj     TEXT NOT NULL,
    customer_id  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS assinaturas (
    usuario_id        TEXT PRIMARY KEY REFERENCES assinantes(usuario_id),
    subscription_id   TEXT NOT NULL UNIQUE,
    plano             TEXT NOT NULL,
    forma             TEXT NOT NULL,
    status_acesso     TEXT NOT NULL,
    primeira_paga_em  TEXT,
    criada_em         TEXT,
    final_cartao      TEXT,
    cancelada_em      TEXT,   -- cancelamento pedido: não renova, acesso segue até acesso_ate
    acesso_ate        TEXT,
    reembolso_em      TEXT,
    atualizado_em     TEXT NOT NULL DEFAULT (datetime('now'))
);
-- ARES-QA-003: uma operação de cobrança por conta de cada vez (reserva gravada antes de chamar o Asaas).
CREATE TABLE IF NOT EXISTS operacoes_cobranca (
    usuario_id  TEXT PRIMARY KEY,
    iniciada    REAL NOT NULL
);
-- Uma linha por reembolso: o questionário opcional (por que saiu, o que melhorar) e a foto do uso do plugin
-- naquele momento (JSON de plugin.resumo_de_uso), para a equipe analisar.
CREATE TABLE IF NOT EXISTS reembolso_feedback (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  TEXT NOT NULL,
    motivo      TEXT,
    melhorar    TEXT,
    uso_plugin  TEXT,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now'))
);
-- Idempotência: cada evento do Asaas é processado uma vez só (entrega "pelo menos uma vez").
CREATE TABLE IF NOT EXISTS eventos_webhook (
    id           TEXT PRIMARY KEY,
    evento       TEXT NOT NULL,
    recebido_em  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class Banco:
    def __init__(self, caminho: str):
        self.con = sqlite3.connect(caminho, check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        self.trava = threading.RLock()
        with self.trava:
            # Passo 1 da preparação (27/11/2026): as tabelas agora vêm das migrações numeradas (app/migracoes.py),
            # aplicadas pelo create_app. Aqui só o modo do SQLite: WAL deixa as leituras longas da área da equipe
            # correrem ao lado das escritas do cliente, e busy_timeout espera um pouco em vez de falhar na hora.
            if caminho != ":memory:":
                self.con.execute("PRAGMA journal_mode=WAL")
            self.con.execute("PRAGMA busy_timeout=5000")

    def um(self, sql: str, *args) -> dict | None:
        with self.trava:
            linha = self.con.execute(sql, args).fetchone()
        return dict(linha) if linha else None

    def todos(self, sql: str, *args) -> list[dict]:
        with self.trava:
            return [dict(r) for r in self.con.execute(sql, args).fetchall()]

    def executar(self, sql: str, *args) -> int:
        with self.trava, self.con:
            return self.con.execute(sql, args).rowcount
