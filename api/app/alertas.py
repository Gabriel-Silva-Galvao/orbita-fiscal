"""Alertas por tema e resumo semanal (item 44 da rodada de testes, 26/11/2026). Recurso do plano Ouro.

Antes, os temas e as áreas ficavam só no navegador. Agora ficam na conta:

  GET /alertas                 (sessão) -> 200 {ouro, temas: [...], resumo: {areas, dia}, enviados: []}
  PUT /alertas/temas           (sessão + Ouro) [{tema, fontes, frequencia}] -> 200 (lista salva) | 403 sem_ouro | 422
  PUT /alertas/resumo          (sessão + Ouro) {areas, dia} -> 200 | 403 sem_ouro | 422

A leitura funciona em qualquer plano (para mostrar o que estava salvo, se a pessoa saiu do Ouro); gravar só no Ouro,
conferido aqui no servidor. Os valores de fontes, frequência, áreas e dia vêm de listas fechadas; o texto do tema tem
de 3 a 60 caracteres e cada conta guarda até 20 temas. O envio dos alertas depende do servidor MCP e da base: até lá,
"enviados" volta vazio.
"""
from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.auth import usuario_logado
from app.billing import tem_acesso

ESQUEMA = """
CREATE TABLE IF NOT EXISTS alertas (
    usuario_id  TEXT PRIMARY KEY,
    temas       TEXT NOT NULL DEFAULT '[]',
    areas       TEXT NOT NULL DEFAULT '[]',
    dia         TEXT NOT NULL DEFAULT 'segunda',
    atualizado  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

FONTES = ("superiores", "administrativo", "normas", "regionais")
AREAS = (
    "Tributário federal",
    "ICMS e estaduais",
    "ISS e municipais",
    "Previdenciário",
    "Processo tributário",
    "Reforma tributária (IBS e CBS)",
)
DIAS = ("segunda", "terca", "quarta", "quinta", "sexta")
MAX_TEMAS = 20


class Tema(BaseModel):
    tema: str = Field(min_length=3, max_length=60)
    fontes: list[Literal["superiores", "administrativo", "normas", "regionais"]] = Field(default_factory=lambda: list(FONTES), max_length=4)
    frequencia: Literal["na_hora", "diario", "semanal"] = "na_hora"

    @field_validator("tema")
    @classmethod
    def _limpa(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 3:
            raise ValueError("Escreva o tema com pelo menos 3 letras.")
        return v

    @field_validator("fontes")
    @classmethod
    def _sem_repetir(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Escolha pelo menos uma fonte.")
        return [f for f in FONTES if f in v]


class Resumo(BaseModel):
    areas: list[str] = Field(default_factory=list, max_length=len(AREAS))
    dia: Literal["segunda", "terca", "quarta", "quinta", "sexta"] = "segunda"

    @field_validator("areas")
    @classmethod
    def _areas_validas(cls, v: list[str]) -> list[str]:
        if any(a not in AREAS for a in v):
            raise ValueError("Área desconhecida.")
        return [a for a in AREAS if a in v]


def _e_ouro(banco, usuario_id: str) -> bool:
    a = banco.um("SELECT * FROM assinaturas WHERE usuario_id = ?", usuario_id)
    return bool(a and a["plano"] == "ouro" and tem_acesso(a))


def _ler(banco, usuario_id: str) -> dict:
    l = banco.um("SELECT temas, areas, dia FROM alertas WHERE usuario_id = ?", usuario_id)
    if not l:
        return {"temas": [], "resumo": {"areas": [], "dia": "segunda"}}
    return {"temas": json.loads(l["temas"]), "resumo": {"areas": json.loads(l["areas"]), "dia": l["dia"]}}


def _exigir_ouro(banco, usuario_id: str) -> None:
    if not _e_ouro(banco, usuario_id):
        raise HTTPException(403, detail={"codigo": "sem_ouro", "mensagem": "Alertas e resumo são do plano Ouro."})


def criar_router() -> APIRouter:
    r = APIRouter(prefix="/alertas", tags=["Alertas"])

    @r.get("")
    def ler(req: Request, u: dict = Depends(usuario_logado)):
        banco = req.app.state.banco
        return {"ouro": _e_ouro(banco, u["id"]), **_ler(banco, u["id"]), "enviados": []}

    @r.put("/temas")
    def salvar_temas(temas: list[Tema], req: Request, u: dict = Depends(usuario_logado)):
        banco = req.app.state.banco
        _exigir_ouro(banco, u["id"])
        if len(temas) > MAX_TEMAS:
            raise HTTPException(422, detail={"codigo": "temas_demais", "mensagem": f"No máximo {MAX_TEMAS} temas."})
        vistos, limpos = set(), []
        for t in temas:
            chave = t.tema.lower()
            if chave not in vistos:
                vistos.add(chave)
                limpos.append(t.model_dump())
        banco.executar(
            "INSERT INTO alertas (usuario_id, temas) VALUES (?, ?) "
            "ON CONFLICT(usuario_id) DO UPDATE SET temas = excluded.temas, atualizado = datetime('now')",
            u["id"], json.dumps(limpos, ensure_ascii=False),
        )
        return limpos

    @r.put("/resumo")
    def salvar_resumo(dados: Resumo, req: Request, u: dict = Depends(usuario_logado)):
        banco = req.app.state.banco
        _exigir_ouro(banco, u["id"])
        banco.executar(
            "INSERT INTO alertas (usuario_id, areas, dia) VALUES (?, ?, ?) "
            "ON CONFLICT(usuario_id) DO UPDATE SET areas = excluded.areas, dia = excluded.dia, atualizado = datetime('now')",
            u["id"], json.dumps(dados.areas, ensure_ascii=False), dados.dia,
        )
        return dados.model_dump()

    return r
