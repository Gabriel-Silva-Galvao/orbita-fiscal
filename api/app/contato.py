"""Contato para planos empresariais (item 26 da rodada de testes, 25/11/2026).

POST /contato/empresarial {nome, empresa, email, usuarios?, mensagem, site?}
  -> 202 {ok, enviado}            mensagem recebida (enviado=false: sem SMTP, só registrada)
  -> 422 dados_invalidos | 429 muitas_mensagens

Proteções: campo isca `site` (robôs preenchem; pessoas não veem), que faz a mensagem ser descartada em silêncio;
limite de 5 mensagens por IP por hora; tamanhos máximos. A mensagem fica registrada na tabela `contatos` e vai
por SMTP para CONTATO_EMAIL, com Reply-To de quem escreveu, e uma confirmação vai para quem escreveu.
"""
from __future__ import annotations

import re

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app import correio
from app.config import get_settings

ESQUEMA = """
CREATE TABLE IF NOT EXISTS contatos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT NOT NULL,
    empresa     TEXT NOT NULL,
    email       TEXT NOT NULL,
    usuarios    TEXT,
    mensagem    TEXT NOT NULL,
    ip          TEXT,
    enviado     INTEGER NOT NULL,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Mesmo regex seguro de app/auth.py (sem ReDoS) e o mesmo contador com memória limitada (ARES-SEC-016).
from app.auth import EMAIL_RE, Limitador  # noqa: E402
JANELA, MAXIMO = 3600, 5
# ARES-QA-002: nome e empresa vão para o assunto e o texto do e-mail; quebra de linha ali fazia o EmailMessage
# recusar o cabeçalho (ValueError), a rota responder 500 e a mensagem se perder. Caractere de controle é recusado.
CONTROLE = re.compile(r"[\x00-\x1f\x7f]")


class Mensagem(BaseModel):
    nome: str = Field(max_length=120)
    empresa: str = Field(max_length=160)
    email: str = Field(max_length=254)
    usuarios: str | None = Field(default=None, max_length=40)
    mensagem: str = Field(max_length=4000)
    site: str | None = Field(default=None, max_length=200)  # isca para robôs


def criar_router() -> APIRouter:
    r = APIRouter(prefix="/contato", tags=["Contato"])
    # ARES-SEC-009: além do limite por IP, um limite por endereço de destino, para a confirmação não virar
    # disparo de e-mails para uma mesma vítima (o IP muda fácil; o destino não).
    por_ip, por_destino = Limitador(JANELA), Limitador(JANELA)

    @r.post("/empresarial", status_code=202)
    def empresarial(dados: Mensagem, req: Request):
        if dados.site:  # robô: finge que deu certo e não faz nada
            return {"ok": True, "enviado": True}
        nome, empresa = dados.nome.strip(), dados.empresa.strip()
        email, msg = dados.email.strip().lower(), dados.mensagem.strip()
        if (len(nome) < 2 or len(empresa) < 2 or CONTROLE.search(nome) or CONTROLE.search(empresa)
                or not EMAIL_RE.match(email) or len(msg) < 10):
            return JSONResponse(
                {"codigo": "dados_invalidos", "descricao": "Preencha nome, empresa, um e-mail válido e a mensagem."},
                status_code=422,
            )
        ip = req.client.host if req.client else "?"
        if por_ip.bloqueado(ip, MAXIMO) or por_destino.bloqueado(email, MAXIMO):
            return JSONResponse(
                {"codigo": "muitas_mensagens", "descricao": "Muitas mensagens em pouco tempo. Tente de novo mais tarde."},
                status_code=429,
            )
        por_ip.falhou(ip, MAXIMO)
        por_destino.falhou(email, MAXIMO)

        # Grava antes de enviar: se o envio falhar, a mensagem continua registrada (ARES-QA-002).
        banco = req.app.state.banco
        banco.executar(
            "INSERT INTO contatos (nome, empresa, email, usuarios, mensagem, ip, enviado) VALUES (?,?,?,?,?,?,0)",
            nome, empresa, email, dados.usuarios, msg, ip,
        )
        contato_id = banco.um("SELECT last_insert_rowid() AS id")["id"]
        s = get_settings()
        corpo = f"Nome: {nome}\nEmpresa: {empresa}\nE-mail: {email}\nUsuários: {dados.usuarios or 'não informado'}\n\n{msg}\n"
        enviado = correio.enviar(
            correio.texto_simples(s.contato_email, f"Plano empresarial: {empresa}", corpo, responder_para=email)
        )
        if enviado:
            correio.enviar(
                correio.texto_simples(
                    email,
                    "Recebemos sua mensagem · Órbita",
                    # ARES-SEC-009: sem nome nem empresa (texto de quem escreveu): o formulário aceita qualquer
                    # endereço, e a confirmação não pode levar a outra pessoa um texto escolhido por um estranho.
                    "Olá,\n\nRecebemos sua mensagem sobre os planos empresariais da Órbita. "
                    "Uma pessoa da equipe responde por este e-mail.\n\n"
                    "Se você não escreveu para a Órbita, pode ignorar esta mensagem.\n\nEquipe Órbita\n",
                )
            )
        if enviado:
            banco.executar("UPDATE contatos SET enviado = 1 WHERE id = ?", contato_id)
        return {"ok": True, "enviado": enviado}

    return r
