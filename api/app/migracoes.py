"""Migrações numeradas do banco (preparação para suporte e admin, passo 1, 27/11/2026).

Antes, cada módulo criava as suas tabelas na subida e acrescentava colunas com `ALTER` soltos. Agora o banco guarda
em `migracoes` quais versões já foram aplicadas, e a API aplica as que faltam, em ordem, na subida.

Como acrescentar uma mudança no banco:
1. Acrescente uma entrada no fim de MIGRACOES com o próximo número, uma descrição curta e o SQL (ou uma função que
   recebe a conexão, quando precisar conferir algo antes).
2. Nunca edite uma migração já publicada: crie outra.
3. Teste em `tests/test_migracoes.py` que o banco antigo chega ao esquema novo sem perder dados.

A versão 1 é o esquema de 27/11/2026, igual ao que existia: em banco novo cria tudo; em banco antigo só completa o que
faltar (as colunas acrescentadas pelos itens 1, 7d e 9 e pelo questionário do reembolso).
"""
from __future__ import annotations

import sqlite3
from typing import Callable, Union

Passo = Union[str, Callable[[sqlite3.Connection], None]]


def _colunas(con: sqlite3.Connection, tabela: str) -> set[str]:
    return {r[1] for r in con.execute(f"PRAGMA table_info({tabela})")}


def _acrescentar(con: sqlite3.Connection, tabela: str, colunas: dict[str, str]) -> None:
    existentes = _colunas(con, tabela)
    for nome, tipo in colunas.items():
        if nome not in existentes:
            con.execute(f"ALTER TABLE {tabela} ADD COLUMN {nome} {tipo}")


def _v1_esquema_inicial(con: sqlite3.Connection) -> None:
    # Importa aqui para não criar dependência circular (os módulos importam o banco).
    from app import alertas, auth, contato, db, plugin

    for esquema in (db.ESQUEMA, auth.ESQUEMA, plugin.ESQUEMA, contato.ESQUEMA, alertas.ESQUEMA):
        for comando in [c for c in esquema.split(";") if c.strip()]:
            con.execute(comando)
    # Bancos criados antes destas colunas existirem (o que os antigos ALTER soltos faziam).
    _acrescentar(con, "assinaturas", {c: "TEXT" for c in ("criada_em", "final_cartao", "cancelada_em", "acesso_ate", "reembolso_em")})
    _acrescentar(con, "assinantes", {"endereco": "TEXT"})
    _acrescentar(con, "reembolso_feedback", {"uso_plugin": "TEXT"})
    _acrescentar(con, "sessoes", auth.COLUNAS_SESSAO)
    con.execute("UPDATE sessoes SET id = lower(hex(randomblob(8))) WHERE id IS NULL")
    _acrescentar(con, "desafios", {"usuario_id": "TEXT"})


MIGRACOES: list[tuple[int, str, Passo]] = [
    (1, "Esquema inicial de 27/11/2026", _v1_esquema_inicial),
    (
        2,
        "Situação da conta e última atividade (passo 3 da preparação)",
        "ALTER TABLE usuarios ADD COLUMN situacao TEXT NOT NULL DEFAULT 'ativa';"
        "ALTER TABLE usuarios ADD COLUMN suspensa_em TEXT;"
        "ALTER TABLE usuarios ADD COLUMN suspensa_motivo TEXT;"
        "ALTER TABLE usuarios ADD COLUMN ultima_atividade REAL",
    ),
]


def aplicar(con: sqlite3.Connection) -> list[int]:
    """Aplica, em ordem, as migrações que faltam. Cada uma roda numa transação: se falhar, nada dela fica gravado e a
    API não sobe. Devolve os números aplicados agora."""
    con.execute(
        "CREATE TABLE IF NOT EXISTS migracoes ("
        " versao INTEGER PRIMARY KEY, descricao TEXT NOT NULL, aplicada_em TEXT NOT NULL DEFAULT (datetime('now')))"
    )
    con.commit()
    feitas = {r[0] for r in con.execute("SELECT versao FROM migracoes")}
    numeros = [n for n, _, _ in MIGRACOES]
    assert numeros == sorted(set(numeros)), "Migrações fora de ordem ou com número repetido."
    aplicadas = []
    for numero, descricao, passo in MIGRACOES:
        if numero in feitas:
            continue
        try:
            con.execute("BEGIN")
            if callable(passo):
                passo(con)
            else:
                for comando in [c for c in passo.split(";") if c.strip()]:
                    con.execute(comando)
            con.execute("INSERT INTO migracoes (versao, descricao) VALUES (?, ?)", (numero, descricao))
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
        aplicadas.append(numero)
    return aplicadas


def versao_atual(con: sqlite3.Connection) -> int:
    linha = con.execute("SELECT MAX(versao) FROM migracoes").fetchone()
    return linha[0] or 0
