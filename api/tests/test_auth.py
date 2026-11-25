"""Conta e login com código por e-mail (etapa 7a)."""
from __future__ import annotations

import time

import pytest

from app import auth


@pytest.fixture
def caixa(monkeypatch):
    """Caixa de entrada falsa: guarda o último código enviado para cada e-mail."""
    recebidos: dict[str, str] = {}
    monkeypatch.setattr(auth, "enviar_codigo_log", lambda email, codigo: recebidos.__setitem__(email, codigo))
    return recebidos


def cadastrar(http, caixa, email="ana@exemplo.test", senha="senha-forte-1"):
    r = http.post("/auth/cadastro", json={"nome": "Ana", "email": email, "senha": senha, "plano": "pro"})
    assert r.status_code == 202
    r = http.post("/auth/codigo", json={"codigo": caixa[email]})
    assert r.status_code == 200
    return r.json()["usuario"]


def test_cadastro_so_cria_conta_depois_do_codigo(api, caixa):
    http, _, banco = api
    r = http.post("/auth/cadastro", json={"nome": "Ana", "email": "Ana@Exemplo.test", "senha": "senha-forte-1"})
    assert r.status_code == 202 and "codigo_dev" not in r.json()
    assert banco.um("SELECT 1 FROM usuarios") is None
    assert http.get("/auth/sessao").status_code == 401
    r = http.post("/auth/codigo", json={"codigo": caixa["ana@exemplo.test"]})
    assert r.status_code == 200
    s = http.get("/auth/sessao").json()
    assert s["email"] == "ana@exemplo.test" and s["nome"] == "Ana"


def test_senha_guardada_com_hash(api, caixa):
    http, _, banco = api
    cadastrar(http, caixa)
    h = banco.um("SELECT senha_hash FROM usuarios")["senha_hash"]
    assert h.startswith("scrypt$") and "senha-forte-1" not in h


def test_cadastro_recusa_email_repetido_e_dados_ruins(api, caixa):
    http, _, _ = api
    cadastrar(http, caixa)
    assert http.post("/auth/cadastro", json={"nome": "Ana", "email": "ana@exemplo.test", "senha": "outra-senha-1"}).status_code == 409
    assert http.post("/auth/cadastro", json={"nome": "B", "email": "nao-e-email", "senha": "senha-forte-1"}).status_code == 422
    assert http.post("/auth/cadastro", json={"nome": "B", "email": "b@exemplo.test", "senha": "curta"}).status_code == 422


def test_login_pede_codigo_e_confere_senha(api, caixa):
    http, _, _ = api
    cadastrar(http, caixa)
    http.post("/auth/sair")
    assert http.get("/auth/sessao").status_code == 401
    assert http.post("/auth/login", json={"email": "ana@exemplo.test", "senha": "errada"}).status_code == 401
    assert http.post("/auth/login", json={"email": "ninguem@exemplo.test", "senha": "x"}).status_code == 401
    assert http.post("/auth/login", json={"email": "ANA@exemplo.test", "senha": "senha-forte-1"}).status_code == 202
    assert http.get("/auth/sessao").status_code == 401  # ainda falta o código
    assert http.post("/auth/codigo", json={"codigo": caixa["ana@exemplo.test"]}).status_code == 200
    assert http.get("/auth/sessao").status_code == 200


def test_codigo_errado_conta_tentativas_e_bloqueia(api, caixa):
    http, _, _ = api
    http.post("/auth/cadastro", json={"nome": "Ana", "email": "ana@exemplo.test", "senha": "senha-forte-1"})
    certo = caixa["ana@exemplo.test"]
    errado = "000000" if certo != "000000" else "111111"
    for restantes in (4, 3, 2, 1):
        r = http.post("/auth/codigo", json={"codigo": errado})
        assert r.status_code == 400 and r.json()["tentativas_restantes"] == restantes
    assert http.post("/auth/codigo", json={"codigo": errado}).status_code == 429
    assert http.post("/auth/codigo", json={"codigo": certo}).status_code == 429  # nem o certo vale mais


def test_codigo_expirado(api, caixa, monkeypatch):
    http, _, _ = api
    http.post("/auth/cadastro", json={"nome": "Ana", "email": "ana@exemplo.test", "senha": "senha-forte-1"})
    agora = time.time()
    monkeypatch.setattr(auth.time, "time", lambda: agora + auth.CODIGO_VALIDADE + 1)
    assert http.post("/auth/codigo", json={"codigo": caixa["ana@exemplo.test"]}).status_code == 410


def test_codigo_sem_desafio(api):
    http, _, _ = api
    assert http.post("/auth/codigo", json={"codigo": "123456"}).status_code == 410


def test_reenviar_espera_60s_e_troca_o_codigo(api, caixa, monkeypatch):
    http, _, _ = api
    http.post("/auth/cadastro", json={"nome": "Ana", "email": "ana@exemplo.test", "senha": "senha-forte-1"})
    primeiro = caixa["ana@exemplo.test"]
    r = http.post("/auth/codigo/reenviar")
    assert r.status_code == 429 and r.json()["espere_segundos"] > 0
    agora = time.time()
    monkeypatch.setattr(auth.time, "time", lambda: agora + 61)
    assert http.post("/auth/codigo/reenviar").status_code == 202
    segundo = caixa["ana@exemplo.test"]
    if segundo != primeiro:
        assert http.post("/auth/codigo", json={"codigo": primeiro}).status_code == 400  # o código antigo não vale mais
    assert http.post("/auth/codigo", json={"codigo": segundo}).status_code == 200


def test_muitas_senhas_erradas_bloqueiam(api, caixa):
    http, _, _ = api
    cadastrar(http, caixa)
    for _ in range(auth.LOGIN_MAX_FALHAS):
        http.post("/auth/login", json={"email": "ana@exemplo.test", "senha": "errada"})
    assert http.post("/auth/login", json={"email": "ana@exemplo.test", "senha": "senha-forte-1"}).status_code == 429


def test_esqueci_nao_revela_conta(api, caixa):
    http, _, _ = api
    cadastrar(http, caixa)
    a = http.post("/auth/senha/esqueci", json={"email": "ana@exemplo.test"})
    b = http.post("/auth/senha/esqueci", json={"email": "ninguem@exemplo.test"})
    assert a.status_code == b.status_code == 202 and a.json() == b.json()


def test_sair_invalida_a_sessao_no_servidor(api, caixa):
    http, _, _ = api
    cadastrar(http, caixa)
    token = http.cookies.get(auth.COOKIE_SESSAO)
    assert http.post("/auth/sair").status_code == 204
    http.cookies.set(auth.COOKIE_SESSAO, token)  # mesmo reapresentando o cookie antigo
    assert http.get("/auth/sessao").status_code == 401


def test_cookies_httponly(api, caixa):
    http, _, _ = api
    r = http.post("/auth/cadastro", json={"nome": "Ana", "email": "ana@exemplo.test", "senha": "senha-forte-1"})
    assert "httponly" in r.headers["set-cookie"].lower()


def test_cors_libera_o_site_com_cookies(api):
    http, _, _ = api
    r = http.options("/auth/login", headers={"Origin": "http://localhost:4321", "Access-Control-Request-Method": "POST"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:4321"
    assert r.headers["access-control-allow-credentials"] == "true"
    r = http.options("/auth/login", headers={"Origin": "https://site-estranho.test", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in r.headers
