"""Conta e login da Órbita (etapa 7a): e-mail e senha, sempre com código de 6 dígitos por e-mail.

Contrato usado pelo site (src/pages/entrar.astro e src/middleware.ts), com base em /auth:
  POST /auth/cadastro         {nome, email, senha, plano?} -> 202 código enviado | 409 e-mail já tem conta
  POST /auth/login            {email, senha}               -> 202 código enviado | 401 não confere
  POST /auth/codigo           {codigo}                     -> 200 sessão criada (cookie)
                                                              | 400 {tentativas_restantes} | 410 expirado | 429 sem tentativas
  POST /auth/codigo/reenviar  {}                           -> 202 | 429 espere 60 s | 410 sem desafio
  POST /auth/senha/esqueci    {email}                      -> 202 sempre (não revela se a conta existe)
  GET  /auth/google                                         -> 303 de volta ao site (?erro=google-indisponivel), por ora
  GET  /auth/sessao                                        -> 200 {id, email, nome} | 401
  POST /auth/sair                                          -> 204

Segurança: senha com scrypt (biblioteca padrão), código e tokens guardados só como SHA-256,
cookies HttpOnly. A conta só nasce depois do código confirmado. Login pelo Google: etapa futura.
Envio de e-mail: ainda não há provedor; o código vai para o log da API (e, em desenvolvimento,
na resposta, se AUTH_CODIGO_NA_RESPOSTA=true).
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import re
import secrets
import time
import uuid
from collections import defaultdict, deque
from typing import Callable

from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from app.config import get_settings

log = logging.getLogger("orbita.auth")

COOKIE_SESSAO = "orbita_sessao"
COOKIE_DESAFIO = "orbita_desafio"
CODIGO_VALIDADE = 10 * 60
CODIGO_TENTATIVAS = 5
REENVIO_ESPERA = 60
SESSAO_VALIDADE = 30 * 24 * 3600
LOGIN_JANELA, LOGIN_MAX_FALHAS = 15 * 60, 10
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id          TEXT PRIMARY KEY,
    email       TEXT NOT NULL UNIQUE,
    nome        TEXT NOT NULL,
    senha_hash  TEXT NOT NULL,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS desafios (
    token_hash   TEXT PRIMARY KEY,
    finalidade   TEXT NOT NULL,          -- cadastro | login
    email        TEXT NOT NULL,
    nome         TEXT,
    senha_hash   TEXT,
    codigo_hash  TEXT NOT NULL,
    expira       REAL NOT NULL,
    tentativas   INTEGER NOT NULL,
    enviado_em   REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sessoes (
    token_hash  TEXT PRIMARY KEY,
    usuario_id  TEXT NOT NULL REFERENCES usuarios(id),
    expira      REAL NOT NULL
);
"""


def _sha(v: str) -> str:
    return hashlib.sha256(v.encode()).hexdigest()


def hash_senha(senha: str) -> str:
    sal = secrets.token_bytes(16)
    dk = hashlib.scrypt(senha.encode(), salt=sal, n=2**14, r=8, p=1)
    return f"scrypt${sal.hex()}${dk.hex()}"


def confere_senha(senha: str, guardado: str) -> bool:
    try:
        _, sal, dk = guardado.split("$")
    except ValueError:
        return False
    novo = hashlib.scrypt(senha.encode(), salt=bytes.fromhex(sal), n=2**14, r=8, p=1)
    return hmac.compare_digest(novo.hex(), dk)


def enviar_codigo_log(email: str, codigo: str) -> None:
    log.warning("Código de verificação para %s: %s (sem provedor de e-mail ainda)", email, codigo)


def usuario_logado(req: Request, orbita_sessao: str | None = Cookie(None)) -> dict:
    """Dependência das rotas do assinante: devolve {id, email, nome} da sessão ou responde 401."""
    s = req.app.state.banco.um(
        "SELECT u.id, u.email, u.nome, s.expira FROM sessoes s JOIN usuarios u ON u.id=s.usuario_id WHERE s.token_hash=?",
        _sha(orbita_sessao) if orbita_sessao else "",
    )
    if not s or s["expira"] < time.time():
        raise HTTPException(401, detail={"codigo": "sem_sessao", "mensagem": "Entre na sua conta."})
    s.pop("expira")
    return s


class Cadastro(BaseModel):
    nome: str
    email: str
    senha: str
    plano: str | None = None


class Login(BaseModel):
    email: str
    senha: str


class Codigo(BaseModel):
    codigo: str


class Esqueci(BaseModel):
    email: str


def _erro(status: int, codigo: str, descricao: str, **extra) -> JSONResponse:
    return JSONResponse({"codigo": codigo, "descricao": descricao, **extra}, status_code=status)


def criar_router(enviar: Callable[[str, str], None] | None = None) -> APIRouter:
    r = APIRouter(prefix="/auth", tags=["Conta e login"])
    falhas: dict[str, deque] = defaultdict(deque)

    def banco(req: Request):
        return req.app.state.banco

    def cookie(resp: Response, nome: str, valor: str, max_age: int) -> None:
        s = get_settings()
        resp.set_cookie(nome, valor, max_age=max_age, httponly=True, samesite="lax", secure=s.cookie_secure, path="/")

    def novo_desafio(req: Request, resp: Response, finalidade: str, email: str, nome=None, senha_hash=None) -> dict:
        token, codigo = secrets.token_urlsafe(32), f"{secrets.randbelow(10**6):06d}"
        agora = time.time()
        banco(req).executar(
            "INSERT INTO desafios VALUES (?,?,?,?,?,?,?,?,?)",
            _sha(token), finalidade, email, nome, senha_hash, _sha(codigo), agora + CODIGO_VALIDADE, CODIGO_TENTATIVAS, agora,
        )
        cookie(resp, COOKIE_DESAFIO, token, CODIGO_VALIDADE)
        (enviar or enviar_codigo_log)(email, codigo)
        corpo = {"enviado_para": email, "validade_segundos": CODIGO_VALIDADE}
        if get_settings().auth_codigo_na_resposta:
            corpo["codigo_dev"] = codigo
        return corpo

    def desafio_atual(req: Request, token: str | None) -> dict | None:
        return banco(req).um("SELECT * FROM desafios WHERE token_hash=?", _sha(token)) if token else None

    def limite_login(email: str) -> bool:
        q, agora = falhas[email], time.time()
        while q and agora - q[0] > LOGIN_JANELA:
            q.popleft()
        return len(q) >= LOGIN_MAX_FALHAS

    @r.post("/cadastro", status_code=202)
    def cadastro(dados: Cadastro, req: Request, resp: Response):
        email, nome = dados.email.strip().lower(), dados.nome.strip()
        if not nome or not EMAIL_RE.match(email):
            return _erro(422, "dados_invalidos", "Informe nome e um e-mail válido.")
        if len(dados.senha) < 8:
            return _erro(422, "senha_curta", "A senha precisa ter pelo menos 8 caracteres.")
        if banco(req).um("SELECT 1 FROM usuarios WHERE email=?", email):
            return _erro(409, "email_em_uso", "Esse e-mail já tem conta.")
        return novo_desafio(req, resp, "cadastro", email, nome, hash_senha(dados.senha))

    @r.post("/login", status_code=202)
    def login(dados: Login, req: Request, resp: Response):
        email = dados.email.strip().lower()
        if limite_login(email):
            return _erro(429, "muitas_tentativas", "Muitas tentativas. Espere alguns minutos.")
        u = banco(req).um("SELECT * FROM usuarios WHERE email=?", email)
        if not u or not confere_senha(dados.senha, u["senha_hash"]):
            falhas[email].append(time.time())
            return _erro(401, "credenciais", "E-mail ou senha não conferem.")
        falhas.pop(email, None)
        return novo_desafio(req, resp, "login", email)

    @r.post("/codigo")
    def codigo(dados: Codigo, req: Request, resp: Response, orbita_desafio: str | None = Cookie(None)):
        d = desafio_atual(req, orbita_desafio)
        if not d or d["expira"] < time.time():
            return _erro(410, "expirado", "O código expirou. Peça outro.")
        if d["tentativas"] <= 0:
            return _erro(429, "sem_tentativas", "Muitas tentativas. Peça um código novo.")
        if not hmac.compare_digest(_sha(dados.codigo.strip()), d["codigo_hash"]):
            restantes = d["tentativas"] - 1
            banco(req).executar("UPDATE desafios SET tentativas=? WHERE token_hash=?", restantes, d["token_hash"])
            if restantes <= 0:
                return _erro(429, "sem_tentativas", "Muitas tentativas. Peça um código novo.")
            return _erro(400, "codigo_errado", "Código incorreto.", tentativas_restantes=restantes)

        b = banco(req)
        if d["finalidade"] == "cadastro":
            if b.um("SELECT 1 FROM usuarios WHERE email=?", d["email"]):
                return _erro(409, "email_em_uso", "Esse e-mail já tem conta.")
            uid = str(uuid.uuid4())
            b.executar("INSERT INTO usuarios (id, email, nome, senha_hash) VALUES (?,?,?,?)", uid, d["email"], d["nome"], d["senha_hash"])
        else:
            uid = b.um("SELECT id FROM usuarios WHERE email=?", d["email"])["id"]
        b.executar("DELETE FROM desafios WHERE token_hash=?", d["token_hash"])

        token = secrets.token_urlsafe(32)
        b.executar("INSERT INTO sessoes VALUES (?,?,?)", _sha(token), uid, time.time() + SESSAO_VALIDADE)
        cookie(resp, COOKIE_SESSAO, token, SESSAO_VALIDADE)
        resp.delete_cookie(COOKIE_DESAFIO, path="/")
        u = b.um("SELECT id, email, nome FROM usuarios WHERE id=?", uid)
        return {"usuario": u}

    @r.post("/codigo/reenviar", status_code=202)
    def reenviar(req: Request, resp: Response, orbita_desafio: str | None = Cookie(None)):
        d = desafio_atual(req, orbita_desafio)
        if not d:
            return _erro(410, "expirado", "Entre de novo para receber outro código.")
        espera = REENVIO_ESPERA - (time.time() - d["enviado_em"])
        if espera > 0:
            return _erro(429, "espere", "Espere para pedir outro código.", espere_segundos=int(espera) + 1)
        banco(req).executar("DELETE FROM desafios WHERE token_hash=?", d["token_hash"])
        return novo_desafio(req, resp, d["finalidade"], d["email"], d["nome"], d["senha_hash"])

    @r.post("/senha/esqueci", status_code=202)
    def esqueci(dados: Esqueci, req: Request):
        email = dados.email.strip().lower()
        if banco(req).um("SELECT 1 FROM usuarios WHERE email=?", email):
            # Troca de senha por link: etapa futura. Por ora, só registra o pedido.
            log.warning("Pedido de troca de senha para %s (envio do link: a definir)", email)
        return {"ok": True}

    @r.get("/google")
    def google():
        # Login pelo Google ainda não existe: volta ao site com um aviso, em vez de uma página de erro.
        return RedirectResponse(f"{get_settings().site_url}/entrar?erro=google-indisponivel", status_code=303)

    @r.get("/sessao")
    def sessao(req: Request, orbita_sessao: str | None = Cookie(None)):
        s = banco(req).um(
            "SELECT u.id, u.email, u.nome, s.expira FROM sessoes s JOIN usuarios u ON u.id=s.usuario_id WHERE s.token_hash=?",
            _sha(orbita_sessao) if orbita_sessao else "",
        )
        if not s or s["expira"] < time.time():
            return _erro(401, "sem_sessao", "Entre na sua conta.")
        s.pop("expira")
        return s

    @r.post("/sair", status_code=204)
    def sair(req: Request, resp: Response, orbita_sessao: str | None = Cookie(None)):
        if orbita_sessao:
            banco(req).executar("DELETE FROM sessoes WHERE token_hash=?", _sha(orbita_sessao))
        resp.delete_cookie(COOKIE_SESSAO, path="/")
        resp.status_code = 204
        return resp

    return r
