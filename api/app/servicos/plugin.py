"""Regras do plugin: conexão registrada pelo servidor MCP e a foto de uso que o suporte e o reembolso mostram.

Movido de app/plugin.py no passo 3 da preparação (27/11/2026), sem mudar o comportamento. Novo: cada pergunta marca
a última atividade da conta (usuários online no plugin).
"""
from __future__ import annotations

import time

from app.db import Banco
from app.servicos import contas

IAS = {"claude", "chatgpt", "copilot", "gemini"}


def registrar_conexao(banco: Banco, usuario_id: str, ia: str | None) -> None:
    """Marca a primeira e a última vez que o plugin deste assinante falou com a Órbita e soma a pergunta na IA usada
    (IA desconhecida ou não informada conta como "outra")."""
    agora = time.time()
    ia = ia if ia in IAS else None
    banco.executar(
        "INSERT INTO plugin_conexoes (usuario_id, primeira, ultima, ia) VALUES (?,?,?,?) "
        "ON CONFLICT(usuario_id) DO UPDATE SET ultima=excluded.ultima, ia=COALESCE(excluded.ia, plugin_conexoes.ia)",
        usuario_id, agora, agora, ia,
    )
    banco.executar(
        "INSERT INTO plugin_uso_ia (usuario_id, ia, perguntas, primeira, ultima) VALUES (?,?,1,?,?) "
        "ON CONFLICT(usuario_id, ia) DO UPDATE SET perguntas = perguntas + 1, ultima = excluded.ultima",
        usuario_id, ia or "outra", agora, agora,
    )
    u = banco.um("SELECT ultima_atividade FROM usuarios WHERE id = ?", usuario_id)
    contas.registrar_atividade(banco, usuario_id, u["ultima_atividade"] if u else None, agora)


def resumo_de_uso(banco: Banco, usuario_id: str) -> dict:
    """Foto do uso do plugin de uma conta: o que o pedido de reembolso e o suporte vão mostrar."""
    c = banco.um("SELECT primeira, ultima FROM plugin_conexoes WHERE usuario_id = ?", usuario_id)
    ias = banco.todos(
        "SELECT ia, perguntas, primeira, ultima FROM plugin_uso_ia WHERE usuario_id = ? ORDER BY perguntas DESC", usuario_id
    )
    d = banco.um("SELECT COUNT(*) AS n, MIN(quando) AS primeiro FROM plugin_downloads_feitos WHERE usuario_id = ?", usuario_id)
    return {
        "baixou": bool(d and d["n"]),
        "downloads": d["n"] if d else 0,
        "primeiro_download": d["primeiro"] if d else None,
        "conectou": bool(c),
        "primeira_conexao": c["primeira"] if c else None,
        "ultima_conexao": c["ultima"] if c else None,
        "dias_de_uso": round((c["ultima"] - c["primeira"]) / 86400, 1) if c else 0,
        "perguntas": sum(i["perguntas"] for i in ias),
        "ias": ias,
    }


def resumo_para_suporte(banco: Banco, usuario_id: str) -> dict:
    """O que o Suporte vê (decisão de 27/11/2026, suporte.md): ativo ou não, se baixou, última conexão e as IAs, sem
    o número de perguntas nem os dias de uso (esses ficam para o Financeiro, no pedido de reembolso)."""
    r = resumo_de_uso(banco, usuario_id)
    return {"baixou": r["baixou"], "conectou": r["conectou"], "ultima_conexao": r["ultima_conexao"], "ias": [i["ia"] for i in r["ias"]]}
