"""Banco da API (SQLite, sem dependências extras). As tabelas são criadas na inicialização."""
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
            self.con.executescript(ESQUEMA)
            # Bancos criados antes da etapa 7d: acrescenta as colunas que faltam.
            existentes = {r[1] for r in self.con.execute("PRAGMA table_info(assinaturas)")}
            for col in ("criada_em", "final_cartao", "cancelada_em", "acesso_ate", "reembolso_em"):
                if col not in existentes:
                    self.con.execute(f"ALTER TABLE assinaturas ADD COLUMN {col} TEXT")
            self.con.commit()

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
