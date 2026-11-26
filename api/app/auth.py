"""Conta e login da Órbita (etapa 7a): e-mail e senha, sempre com código de 6 dígitos por e-mail.

Contrato usado pelo site (src/pages/entrar.astro e src/middleware.ts), com base em /auth:
  POST /auth/cadastro         {nome, email, senha, plano?} -> 202 código enviado | 409 e-mail já tem conta
  POST /auth/login            {email, senha}               -> 202 código enviado | 401 não confere
  POST /auth/codigo           {codigo, manter?}            -> 200 sessão criada (cookie)
                                                              | 400 {tentativas_restantes} | 410 expirado | 429 sem tentativas
  POST /auth/codigo/reenviar  {}                           -> 202 | 429 espere 60 s | 410 sem desafio
  POST /auth/senha/esqueci    {email}                      -> 202 sempre (não revela se a conta existe)
  GET  /auth/sessao                                        -> 200 {id, email, nome} | 401
  PUT  /auth/conta            {nome}                       -> 200 | 422
  DELETE /auth/conta                                       -> 204 | 409 assinatura_ativa (cancele antes)
  POST /auth/sair                                          -> 204
  GET  /auth/sessoes                                       -> 200 [{id, aparelho, tipo, criada, ultimo_uso, atual, mesmo_aparelho}]
  POST /auth/sair-dos-outros                               -> 204 (encerra todas as sessões menos esta)
  DELETE /auth/sessoes/{id}                                -> 204 (sai daquele aparelho) | 404
  POST /auth/sair-de-todos                                 -> 204 (encerra todas, inclusive esta)
  POST /auth/senha/trocar     {atual, nova}                -> 202 código enviado ao e-mail | 401 senha atual errada
  POST /auth/email/trocar     {email, senha}               -> 202 código enviado ao e-mail NOVO | 401 senha atual errada | 409 em uso
  POST /auth/confirmar        {codigo}                     -> 200 troca feita (as outras sessões caem; troca de e-mail avisa o antigo)
  GET/PUT /auth/preferencias  {novidades, resumo_semanal}  -> preferências de e-mail (item 9)

Sessão (item 1 da rodada de testes, 25/11/2026): no máximo 30 dias a partir do login, sem renovar.
Com "manter conectado" (padrão), o cookie dura 30 dias; sem ele, o cookie some ao fechar o navegador e a
sessão no servidor vale 12 horas. Cada sessão guarda o aparelho (do User-Agent), quando foi criada e o último
uso; excluir a conta encerra todas.

Segurança: senha com scrypt (biblioteca padrão), código e tokens guardados só como SHA-256,
cookies HttpOnly. A conta só nasce depois do código confirmado. Só e-mail e senha: o login
pelo Google saiu em 25/11/2026. Envio do código: por SMTP (app/correio.py) quando SMTP_HOST está
definido; sem ele, vai para o log da API (e, em desenvolvimento, na resposta, se
AUTH_CODIGO_NA_RESPOSTA=true).
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import re
import secrets
import time
import uuid
from collections import deque
from typing import Callable

from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.correio import avisar_troca_de_email, enviar_codigo

log = logging.getLogger("orbita.auth")

COOKIE_SESSAO = "orbita_sessao"
COOKIE_DESAFIO = "orbita_desafio"
CODIGO_VALIDADE = 10 * 60
CODIGO_TENTATIVAS = 5
REENVIO_ESPERA = 60
SESSAO_VALIDADE = 30 * 24 * 3600
SESSAO_CURTA = 12 * 3600  # sem "manter conectado"
ULTIMO_USO_PASSO = 60  # grava o último uso no máximo uma vez por minuto
LOGIN_JANELA, LOGIN_MAX_FALHAS = 15 * 60, 10
SENHA_ATUAL_MAX_FALHAS = 5  # ARES-SEC-018: senha atual errada na troca de senha/e-mail, por conta, na mesma janela
CODIGO_MAX_FALHAS_CONTA = 10  # ARES-SEC-002: códigos errados por e-mail, somando todos os desafios, na mesma janela
# Segurança (26/11/2026): o regex antigo, r"^[^@\s]+@[^@\s]+\.[^@\s]+$", voltava atrás em tempo quadrático num domínio
# longo cheio de pontos (ReDoS) e, como o regex segura o GIL, travava a API inteira. Este não volta atrás: os pedaços do
# domínio não contêm ponto, e o ponto é literal entre eles. Além disso, o e-mail passa por limite de tamanho antes.
EMAIL_MAX = 254
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s.]{1,63}(?:\.[^@\s.]{1,63})+$")

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
    finalidade   TEXT NOT NULL,          -- cadastro | login | senha | email
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
CREATE TABLE IF NOT EXISTS preferencias (
    usuario_id      TEXT PRIMARY KEY,
    novidades       INTEGER NOT NULL DEFAULT 1,
    resumo_semanal  INTEGER NOT NULL DEFAULT 1
);
"""

# Colunas da sessão acrescentadas no item 1 (bancos antigos ganham as colunas sem perder as sessões).
COLUNAS_SESSAO = {"id": "TEXT", "criada": "REAL", "ultimo_uso": "REAL", "aparelho": "TEXT", "manter": "INTEGER"}


def migrar(con) -> None:
    existentes = {r[1] for r in con.execute("PRAGMA table_info(sessoes)")}
    for col, tipo in COLUNAS_SESSAO.items():
        if col not in existentes:
            con.execute(f"ALTER TABLE sessoes ADD COLUMN {col} {tipo}")
    con.execute("UPDATE sessoes SET id = lower(hex(randomblob(8))) WHERE id IS NULL")
    # Item 9: desafios de troca de senha e de e-mail são de um usuário já logado.
    if "usuario_id" not in {r[1] for r in con.execute("PRAGMA table_info(desafios)")}:
        con.execute("ALTER TABLE desafios ADD COLUMN usuario_id TEXT")
    con.commit()


def aparelho(user_agent: str) -> str:
    """Nome curto do aparelho, para a lista de sessões: navegador e sistema."""
    ua = user_agent or ""
    nav = next((n for k, n in (("Edg/", "Edge"), ("OPR/", "Opera"), ("Firefox/", "Firefox"), ("FxiOS/", "Firefox"), ("CriOS/", "Chrome"),
                               ("Chrome/", "Chrome"),
                               ("Safari/", "Safari")) if k in ua), "Navegador")
    so = next((n for k, n in (("Windows", "Windows"), ("Android", "Android"), ("iPhone", "iPhone"), ("iPad", "iPad"),
                              ("Mac OS", "macOS"), ("Linux", "Linux")) if k in ua), "")
    return f"{nav} no {so}" if so else nav


def tipo_aparelho(nome: str) -> str:
    """Item 47: computador, celular ou tablet, a partir do nome curto (para o ícone da lista)."""
    if "iPad" in nome:
        return "tablet"
    if "iPhone" in nome or "Android" in nome:
        return "celular"
    return "computador"


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


def sessao_valida(banco, token: str | None) -> dict | None:
    """Sessão do cookie, se existe e não expirou; marca o último uso (no máximo uma vez por minuto)."""
    if not token:
        return None
    s = banco.um(
        "SELECT u.id, u.email, u.nome, s.expira, s.ultimo_uso, s.id AS sessao_id FROM sessoes s "
        "JOIN usuarios u ON u.id=s.usuario_id WHERE s.token_hash=?",
        _sha(token),
    )
    agora = time.time()
    if not s or s["expira"] < agora:
        return None
    if not s["ultimo_uso"] or agora - s["ultimo_uso"] > ULTIMO_USO_PASSO:
        banco.executar("UPDATE sessoes SET ultimo_uso=? WHERE token_hash=?", agora, _sha(token))
    return {"id": s["id"], "email": s["email"], "nome": s["nome"], "sessao_id": s["sessao_id"]}


def usuario_logado(req: Request, orbita_sessao: str | None = Cookie(None)) -> dict:
    """Dependência das rotas do assinante: devolve {id, email, nome} da sessão ou responde 401."""
    s = sessao_valida(req.app.state.banco, orbita_sessao)
    if not s:
        raise HTTPException(401, detail={"codigo": "sem_sessao", "mensagem": "Entre na sua conta."})
    s.pop("sessao_id")
    return s


# Limites de tamanho em todo texto que entra (segurança, 26/11/2026): nada de string gigante chegando ao regex,
# ao scrypt ou ao banco. Acima do limite, a API responde 422 antes de qualquer processamento.
class Cadastro(BaseModel):
    nome: str = Field(max_length=120)
    email: str = Field(max_length=EMAIL_MAX)
    senha: str = Field(max_length=128)
    plano: str | None = Field(default=None, max_length=20)


class Login(BaseModel):
    email: str = Field(max_length=EMAIL_MAX)
    senha: str = Field(max_length=128)


class Codigo(BaseModel):
    codigo: str = Field(max_length=12)
    manter: bool = True


class Esqueci(BaseModel):
    email: str = Field(max_length=EMAIL_MAX)


class Nome(BaseModel):
    nome: str = Field(max_length=120)


class TrocaSenha(BaseModel):
    atual: str = Field(max_length=128)
    nova: str = Field(max_length=128)


class TrocaEmail(BaseModel):
    email: str = Field(max_length=EMAIL_MAX)
    senha: str = Field(max_length=128)  # ARES-SEC-017: só a sessão não basta para trocar o e-mail


class Confirmacao(BaseModel):
    codigo: str = Field(max_length=12)


class Preferencias(BaseModel):
    novidades: bool
    resumo_semanal: bool


class Limitador:
    """Contador de falhas por chave numa janela de tempo, na memória do processo.

    ARES-SEC-016: a versão anterior era um defaultdict que criava uma chave a cada e-mail digitado (até numa leitura)
    e só apagava no login certo; um anônimo fazia a memória crescer sem limite mandando logins com e-mails inventados.
    Agora: ler não cria chave; fila vazia é apagada; a chave é um hash curto (não o e-mail); cada fila guarda no máximo
    o teto daquele limite; e a cada 1.000 falhas (ou acima de TETO_CHAVES) as chaves vencidas são varridas. Assim a
    memória fica proporcional às falhas dos últimos 15 minutos, com no máximo ~10 registros por chave."""

    TETO_CHAVES = 50_000
    VARRER_A_CADA = 1_000

    def __init__(self, janela: float):
        self.janela = janela
        self.filas: dict[str, deque] = {}
        self._escritas = 0

    @staticmethod
    def _k(chave: str) -> str:
        return hashlib.sha256(chave.encode()).hexdigest()[:24]

    def _podar(self, k: str, agora: float) -> int:
        q = self.filas.get(k)
        if q is None:
            return 0
        while q and agora - q[0] > self.janela:
            q.popleft()
        if not q:
            del self.filas[k]
            return 0
        return len(q)

    def bloqueado(self, chave: str, maximo: int) -> bool:
        return self._podar(self._k(chave), time.time()) >= maximo

    def falhou(self, chave: str, maximo: int) -> None:
        k, agora = self._k(chave), time.time()
        self._podar(k, agora)
        self.filas.setdefault(k, deque(maxlen=maximo)).append(agora)
        self._escritas += 1
        if self._escritas % self.VARRER_A_CADA == 0 or len(self.filas) > self.TETO_CHAVES:
            self.varrer()

    def zerar(self, chave: str) -> None:
        self.filas.pop(self._k(chave), None)

    def varrer(self) -> None:
        agora = time.time()
        for k in list(self.filas):
            self._podar(k, agora)
        if len(self.filas) > self.TETO_CHAVES:
            log.warning("Limitador de login com %d chaves ativas (acima de %d): possível ataque de volume", len(self.filas), self.TETO_CHAVES)


def _erro(status: int, codigo: str, descricao: str, **extra) -> JSONResponse:
    return JSONResponse({"codigo": codigo, "descricao": descricao, **extra}, status_code=status)


def criar_router(enviar: Callable[[str, str], None] | None = None) -> APIRouter:
    r = APIRouter(prefix="/auth", tags=["Conta e login"])
    falhas = Limitador(LOGIN_JANELA)
    r.limitador = falhas  # main.py guarda em app.state.limitador_login (observação e testes)

    def banco(req: Request):
        return req.app.state.banco

    def cookie(resp: Response, nome: str, valor: str, max_age: int | None) -> None:
        # max_age None: cookie de sessão do navegador (some ao fechar).
        s = get_settings()
        resp.set_cookie(nome, valor, max_age=max_age, httponly=True, samesite="lax", secure=s.cookie_secure, path="/")

    def novo_desafio(req: Request, resp: Response, finalidade: str, email: str, nome=None, senha_hash=None, usuario_id=None) -> dict:
        token, codigo = secrets.token_urlsafe(32), f"{secrets.randbelow(10**6):06d}"
        agora = time.time()
        banco(req).executar(
            "INSERT INTO desafios (token_hash, finalidade, email, nome, senha_hash, codigo_hash, expira, tentativas, enviado_em, usuario_id)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            _sha(token), finalidade, email, nome, senha_hash, _sha(codigo), agora + CODIGO_VALIDADE, CODIGO_TENTATIVAS, agora, usuario_id,
        )
        cookie(resp, COOKIE_DESAFIO, token, CODIGO_VALIDADE)
        (enviar or enviar_codigo)(email, codigo)
        corpo = {"enviado_para": email, "validade_segundos": CODIGO_VALIDADE}
        if get_settings().auth_codigo_na_resposta:
            corpo["codigo_dev"] = codigo
        return corpo

    def desafio_atual(req: Request, token: str | None) -> dict | None:
        return banco(req).um("SELECT * FROM desafios WHERE token_hash=?", _sha(token)) if token else None

    def limite_login(chave: str, maximo: int = LOGIN_MAX_FALHAS) -> bool:
        return falhas.bloqueado(chave, maximo)

    def senha_atual_confere(req: Request, usuario_id: str, senha: str) -> JSONResponse | None:
        """ARES-SEC-018: a troca de senha (e a de e-mail) conferia a senha atual sem limite, o que permitia adivinhá-la
        por força bruta com uma sessão roubada, contornando o limite do login. Agora conta os erros por conta: no
        5º erro em 15 minutos, 429 até a janela passar (mesmo com a senha certa)."""
        chave = f"conta:{usuario_id}"
        if limite_login(chave, SENHA_ATUAL_MAX_FALHAS):
            return _erro(429, "muitas_tentativas", "Muitas tentativas com a senha atual. Espere alguns minutos.")
        u = banco(req).um("SELECT senha_hash FROM usuarios WHERE id=?", usuario_id)
        if not confere_senha(senha, u["senha_hash"]):
            falhas.falhou(chave, SENHA_ATUAL_MAX_FALHAS)
            return _erro(401, "senha_atual", "A senha atual não confere.")
        falhas.zerar(chave)
        return None

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
            falhas.falhou(email, LOGIN_MAX_FALHAS)
            return _erro(401, "credenciais", "E-mail ou senha não conferem.")
        falhas.zerar(email)
        if limite_login(f"codigo:{email}", CODIGO_MAX_FALHAS_CONTA):
            # ARES-SEC-002: conta com códigos errados demais na janela não ganha desafio novo (nem mais 5 chutes).
            return _erro(429, "muitas_tentativas", "Muitos códigos errados. Espere alguns minutos para pedir outro.")
        return novo_desafio(req, resp, "login", email)

    def conferir(req: Request, d: dict | None, codigo: str) -> JSONResponse | None:
        """Confere o código de um desafio: expirado, sem tentativas ou errado viram a resposta de erro."""
        if not d or d["expira"] < time.time():
            return _erro(410, "expirado", "O código expirou. Peça outro.")
        if d["tentativas"] <= 0:
            return _erro(429, "sem_tentativas", "Muitas tentativas. Peça um código novo.")
        # ARES-SEC-002: além das 5 tentativas de cada desafio, um teto por e-mail somando todos os desafios; sem ele,
        # cada login novo dava mais 5 chutes e o código de 6 dígitos caía por força bruta com a senha já descoberta.
        conta = f"codigo:{d['email']}"
        if limite_login(conta, CODIGO_MAX_FALHAS_CONTA):
            return _erro(429, "sem_tentativas", "Muitos códigos errados. Espere alguns minutos para pedir outro.")
        if not hmac.compare_digest(_sha(codigo.strip()), d["codigo_hash"]):
            falhas.falhou(conta, CODIGO_MAX_FALHAS_CONTA)
            restantes = d["tentativas"] - 1
            banco(req).executar("UPDATE desafios SET tentativas=? WHERE token_hash=?", restantes, d["token_hash"])
            if restantes <= 0:
                return _erro(429, "sem_tentativas", "Muitas tentativas. Peça um código novo.")
            return _erro(400, "codigo_errado", "Código incorreto.", tentativas_restantes=restantes)
        falhas.zerar(conta)
        return None

    @r.post("/codigo")
    def codigo(dados: Codigo, req: Request, resp: Response, orbita_desafio: str | None = Cookie(None)):
        d = desafio_atual(req, orbita_desafio)
        if d and d["finalidade"] not in ("cadastro", "login"):
            d = None  # código de troca de senha/e-mail não serve para entrar
        erro = conferir(req, d, dados.codigo)
        if erro:
            return erro

        b = banco(req)
        if d["finalidade"] == "cadastro":
            if b.um("SELECT 1 FROM usuarios WHERE email=?", d["email"]):
                return _erro(409, "email_em_uso", "Esse e-mail já tem conta.")
            uid = str(uuid.uuid4())
            b.executar("INSERT INTO usuarios (id, email, nome, senha_hash) VALUES (?,?,?,?)", uid, d["email"], d["nome"], d["senha_hash"])
        else:
            uid = b.um("SELECT id FROM usuarios WHERE email=?", d["email"])["id"]
        b.executar("DELETE FROM desafios WHERE token_hash=?", d["token_hash"])

        # Token novo a cada login; o token velho deste navegador, se houver, é encerrado.
        token, agora = secrets.token_urlsafe(32), time.time()
        velho = req.cookies.get(COOKIE_SESSAO)
        if velho:
            b.executar("DELETE FROM sessoes WHERE token_hash=?", _sha(velho))
        validade = SESSAO_VALIDADE if dados.manter else SESSAO_CURTA
        b.executar(
            "INSERT INTO sessoes (token_hash, usuario_id, expira, id, criada, ultimo_uso, aparelho, manter) VALUES (?,?,?,?,?,?,?,?)",
            _sha(token), uid, agora + validade, secrets.token_hex(8), agora, agora,
            aparelho(req.headers.get("user-agent", "")), int(dados.manter),
        )
        cookie(resp, COOKIE_SESSAO, token, SESSAO_VALIDADE if dados.manter else None)
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
        # ARES-QA-010: sem o usuario_id, o desafio reenviado da troca de senha/e-mail não era mais "daquela conta" e o
        # /auth/confirmar sempre respondia 410.
        return novo_desafio(req, resp, d["finalidade"], d["email"], d["nome"], d["senha_hash"], usuario_id=d["usuario_id"])

    @r.post("/senha/esqueci", status_code=202)
    def esqueci(dados: Esqueci, req: Request):
        email = dados.email.strip().lower()
        if banco(req).um("SELECT 1 FROM usuarios WHERE email=?", email):
            # Troca de senha por link: etapa futura. Por ora, só registra o pedido.
            log.warning("Pedido de troca de senha para %s (envio do link: a definir)", email)
        return {"ok": True}

    @r.get("/sessao")
    def sessao(req: Request, orbita_sessao: str | None = Cookie(None)):
        s = sessao_valida(banco(req), orbita_sessao)
        if not s:
            return _erro(401, "sem_sessao", "Entre na sua conta.")
        s.pop("sessao_id")
        return s

    # ---------- Item 9: troca de senha e de e-mail, sempre com código ----------
    @r.post("/senha/trocar", status_code=202)
    def trocar_senha(dados: TrocaSenha, req: Request, resp: Response, orbita_sessao: str | None = Cookie(None)):
        s = sessao_valida(banco(req), orbita_sessao)
        if not s:
            return _erro(401, "sem_sessao", "Entre na sua conta.")
        erro = senha_atual_confere(req, s["id"], dados.atual)
        if erro:
            return erro
        if len(dados.nova) < 8:
            return _erro(422, "senha_curta", "A senha nova precisa ter pelo menos 8 caracteres.")
        if dados.nova == dados.atual:
            return _erro(422, "senha_igual", "A senha nova precisa ser diferente da atual.")
        return novo_desafio(req, resp, "senha", s["email"], senha_hash=hash_senha(dados.nova), usuario_id=s["id"])

    @r.post("/email/trocar", status_code=202)
    def trocar_email(dados: TrocaEmail, req: Request, resp: Response, orbita_sessao: str | None = Cookie(None)):
        s = sessao_valida(banco(req), orbita_sessao)
        if not s:
            return _erro(401, "sem_sessao", "Entre na sua conta.")
        # ARES-SEC-017: com uma sessão roubada, trocar o e-mail sem a senha tomava a conta de vez (a recuperação
        # vai para o e-mail). Agora a senha atual é exigida, como na troca de senha.
        erro = senha_atual_confere(req, s["id"], dados.senha)
        if erro:
            return erro
        email = dados.email.strip().lower()
        if not EMAIL_RE.match(email):
            return _erro(422, "dados_invalidos", "Informe um e-mail válido.")
        if email == s["email"]:
            return _erro(422, "email_igual", "Esse já é o seu e-mail.")
        if banco(req).um("SELECT 1 FROM usuarios WHERE email=?", email):
            return _erro(409, "email_em_uso", "Esse e-mail já tem conta.")
        # O código vai para o e-mail NOVO: prova que a pessoa tem acesso a ele.
        return novo_desafio(req, resp, "email", email, usuario_id=s["id"])

    @r.post("/confirmar")
    def confirmar(dados: Confirmacao, req: Request, resp: Response, orbita_sessao: str | None = Cookie(None), orbita_desafio: str | None = Cookie(None)):
        s = sessao_valida(banco(req), orbita_sessao)
        if not s:
            return _erro(401, "sem_sessao", "Entre na sua conta.")
        d = desafio_atual(req, orbita_desafio)
        if d and (d["finalidade"] not in ("senha", "email") or d["usuario_id"] != s["id"]):
            d = None
        erro = conferir(req, d, dados.codigo)
        if erro:
            return erro
        b = banco(req)
        b.executar("DELETE FROM desafios WHERE token_hash=?", d["token_hash"])
        resp.delete_cookie(COOKIE_DESAFIO, path="/")
        if d["finalidade"] == "senha":
            b.executar("UPDATE usuarios SET senha_hash=? WHERE id=?", d["senha_hash"], s["id"])
            # Senha nova: todas as outras sessões caem; esta continua (S13 do documento de segurança).
            b.executar("DELETE FROM sessoes WHERE usuario_id=? AND id<>?", s["id"], s["sessao_id"])
            return {"ok": True, "trocou": "senha"}
        if b.um("SELECT 1 FROM usuarios WHERE email=?", d["email"]):
            return _erro(409, "email_em_uso", "Esse e-mail já tem conta.")
        b.executar("UPDATE usuarios SET email=? WHERE id=?", d["email"], s["id"])
        # ARES-SEC-017 / ARES-QA-012: como na troca de senha, as outras sessões caem; e o endereço antigo é avisado,
        # para o dono perceber se não foi ele.
        b.executar("DELETE FROM sessoes WHERE usuario_id=? AND id<>?", s["id"], s["sessao_id"])
        avisar_troca_de_email(s["email"], d["email"])
        return {"ok": True, "trocou": "email", "email": d["email"]}

    @r.get("/preferencias")
    def preferencias(req: Request, orbita_sessao: str | None = Cookie(None)):
        s = sessao_valida(banco(req), orbita_sessao)
        if not s:
            return _erro(401, "sem_sessao", "Entre na sua conta.")
        p = banco(req).um("SELECT novidades, resumo_semanal FROM preferencias WHERE usuario_id=?", s["id"])
        p = p or {"novidades": 1, "resumo_semanal": 1}
        return {"novidades": bool(p["novidades"]), "resumo_semanal": bool(p["resumo_semanal"]), "avisos_de_cobranca": True}

    @r.put("/preferencias")
    def salvar_preferencias(dados: Preferencias, req: Request, orbita_sessao: str | None = Cookie(None)):
        s = sessao_valida(banco(req), orbita_sessao)
        if not s:
            return _erro(401, "sem_sessao", "Entre na sua conta.")
        banco(req).executar(
            "INSERT INTO preferencias (usuario_id, novidades, resumo_semanal) VALUES (?,?,?) "
            "ON CONFLICT(usuario_id) DO UPDATE SET novidades=excluded.novidades, resumo_semanal=excluded.resumo_semanal",
            s["id"], int(dados.novidades), int(dados.resumo_semanal),
        )
        return {"novidades": dados.novidades, "resumo_semanal": dados.resumo_semanal, "avisos_de_cobranca": True}

    @r.get("/sessoes")
    def sessoes(req: Request, orbita_sessao: str | None = Cookie(None)):
        s = sessao_valida(banco(req), orbita_sessao)
        if not s:
            return _erro(401, "sem_sessao", "Entre na sua conta.")
        linhas = banco(req).todos(
            "SELECT id, aparelho, criada, ultimo_uso, manter FROM sessoes WHERE usuario_id=? AND expira>? ORDER BY ultimo_uso DESC",
            s["id"], time.time(),
        )
        # Item 47: "mesmo_aparelho" marca outra sessão aberta no mesmo navegador e sistema desta (um login antigo aqui).
        este = aparelho(req.headers.get("user-agent", ""))
        return [
            {
                **l,
                "manter": bool(l["manter"]),
                "tipo": tipo_aparelho(l["aparelho"] or ""),
                "atual": l["id"] == s["sessao_id"],
                "mesmo_aparelho": l["id"] != s["sessao_id"] and (l["aparelho"] or "") == este,
            }
            for l in linhas
        ]

    @r.post("/sair-dos-outros", status_code=204)
    def sair_dos_outros(req: Request, orbita_sessao: str | None = Cookie(None)):
        s = sessao_valida(banco(req), orbita_sessao)
        if not s:
            return _erro(401, "sem_sessao", "Entre na sua conta.")
        banco(req).executar("DELETE FROM sessoes WHERE usuario_id=? AND id<>?", s["id"], s["sessao_id"])
        return Response(status_code=204)

    @r.delete("/sessoes/{sid}", status_code=204)
    def encerrar(sid: str, req: Request, resp: Response, orbita_sessao: str | None = Cookie(None)):
        s = sessao_valida(banco(req), orbita_sessao)
        if not s:
            return _erro(401, "sem_sessao", "Entre na sua conta.")
        # Só encerra sessão da própria conta: o id de outra pessoa não é achado.
        if not banco(req).executar("DELETE FROM sessoes WHERE id=? AND usuario_id=?", sid, s["id"]):
            return _erro(404, "nao_achada", "Essa sessão já foi encerrada.")
        if sid == s["sessao_id"]:
            resp.delete_cookie(COOKIE_SESSAO, path="/")
        resp.status_code = 204
        return resp

    @r.post("/sair-de-todos", status_code=204)
    def sair_de_todos(req: Request, resp: Response, orbita_sessao: str | None = Cookie(None)):
        s = sessao_valida(banco(req), orbita_sessao)
        if not s:
            return _erro(401, "sem_sessao", "Entre na sua conta.")
        banco(req).executar("DELETE FROM sessoes WHERE usuario_id=?", s["id"])
        resp.delete_cookie(COOKIE_SESSAO, path="/")
        resp.status_code = 204
        return resp

    @r.put("/conta")
    def trocar_nome(dados: Nome, req: Request, orbita_sessao: str | None = Cookie(None)):
        u = usuario_logado(req, orbita_sessao)
        nome = dados.nome.strip()
        if not 2 <= len(nome) <= 120:
            return _erro(422, "nome_invalido", "Escreva um nome entre 2 e 120 caracteres.")
        banco(req).executar("UPDATE usuarios SET nome = ? WHERE id = ?", nome, u["id"])
        return {**u, "nome": nome}

    @r.delete("/conta", status_code=204)
    def excluir(req: Request, resp: Response, orbita_sessao: str | None = Cookie(None)):
        u = usuario_logado(req, orbita_sessao)
        b = banco(req)
        a = b.um("SELECT status_acesso, cancelada_em FROM assinaturas WHERE usuario_id = ?", u["id"])
        if a and a["status_acesso"] not in ("cancelado", "reembolsado") and not a["cancelada_em"]:
            return _erro(409, "assinatura_ativa", "Cancele a assinatura antes de excluir a conta, para não haver nova cobrança.")
        # Dados de cobrança (assinantes, assinaturas) ficam pelo prazo legal de guarda fiscal; a conta e o login saem.
        b.executar("DELETE FROM sessoes WHERE usuario_id = ?", u["id"])
        b.executar("DELETE FROM desafios WHERE email = ?", u["email"])
        b.executar("DELETE FROM preferencias WHERE usuario_id = ?", u["id"])
        b.executar("DELETE FROM usuarios WHERE id = ?", u["id"])
        resp.delete_cookie(COOKIE_SESSAO, path="/")
        resp.status_code = 204
        return resp

    @r.post("/sair", status_code=204)
    def sair(req: Request, resp: Response, orbita_sessao: str | None = Cookie(None)):
        if orbita_sessao:
            banco(req).executar("DELETE FROM sessoes WHERE token_hash=?", _sha(orbita_sessao))
        resp.delete_cookie(COOKIE_SESSAO, path="/")
        resp.status_code = 204
        return resp

    return r
