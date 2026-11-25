"""Conta e login com código por e-mail (etapa 7a)."""
from __future__ import annotations

import time

import pytest

from app import auth


@pytest.fixture
def caixa(monkeypatch):
    """Caixa de entrada falsa: guarda o último código enviado para cada e-mail."""
    recebidos: dict[str, str] = {}
    monkeypatch.setattr(auth, "enviar_codigo", lambda email, codigo: recebidos.__setitem__(email, codigo))
    return recebidos


def cadastrar(http, caixa, email="ana@exemplo.test", senha="senha-forte-1"):
    r = http.post("/auth/cadastro", json={"nome": "Ana", "email": email, "senha": senha, "plano": "prata"})
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


def test_login_pelo_google_nao_existe_mais(api):
    http, _, _ = api
    assert http.get("/auth/google", follow_redirects=False).status_code == 404


def test_email_do_codigo_por_smtp(monkeypatch):
    from app import correio as em
    from app.config import get_settings
    enviados = []

    class SMTPFalso:
        def __init__(self, host, port, timeout):
            enviados.append(("conexao", host, port))
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self, context): enviados.append("starttls")
        def login(self, u, p): enviados.append(("login", u))
        def send_message(self, m): enviados.append(m)

    monkeypatch.setenv("SMTP_HOST", "smtp.teste.local")
    monkeypatch.setenv("SMTP_USER", "usuario")
    monkeypatch.setenv("SMTP_PASSWORD", "x")
    get_settings.cache_clear()
    monkeypatch.setattr(em.smtplib, "SMTP", SMTPFalso)
    try:
        em.enviar_codigo("ana@exemplo.com", "123456")
    finally:
        get_settings.cache_clear()
    msg = enviados[-1]
    assert ("conexao", "smtp.teste.local", 587) in enviados and "starttls" in enviados
    assert msg["To"] == "ana@exemplo.com" and "123456" in msg["Subject"]
    assert "123456" in msg.get_body(("plain",)).get_content()


def test_trocar_nome(api, caixa):
    http, _, _ = api
    cadastrar(http, caixa)
    assert http.put("/auth/conta", json={"nome": "Ana Souza"}).json()["nome"] == "Ana Souza"
    assert http.get("/auth/sessao").json()["nome"] == "Ana Souza"
    assert http.put("/auth/conta", json={"nome": " "}).status_code == 422


def test_excluir_conta_exige_cancelar_antes(api, caixa):
    http, _, banco = api
    cadastrar(http, caixa)
    http.post("/billing/assinatura", json={"nome": "Ana", "cpf_cnpj": "52998224725", "plano": "prata", "forma": "pix"})
    r = http.delete("/auth/conta")
    assert r.status_code == 409 and r.json()["codigo"] == "assinatura_ativa"
    http.delete("/billing/assinatura")  # nunca pago: encerra na hora
    assert http.delete("/auth/conta").status_code == 204
    assert http.get("/auth/sessao").status_code == 401
    assert banco.um("SELECT 1 FROM usuarios WHERE email = 'ana@exemplo.test'") is None


def test_rotas_da_conta_exigem_sessao(api):
    http, _, _ = api
    assert http.put("/auth/conta", json={"nome": "X Y"}).status_code == 401
    assert http.delete("/auth/conta").status_code == 401


# ---------- Item 1 da rodada de testes: sessão de 30 dias, "manter conectado" e aparelhos ----------

def entrar_em(http, caixa, email="ana@exemplo.test", manter=True, ua="Mozilla/5.0 (Windows NT 10.0) Chrome/130"):
    r = http.post("/auth/login", json={"email": email, "senha": "senha-forte-1"}, headers={"user-agent": ua})
    assert r.status_code == 202
    r = http.post("/auth/codigo", json={"codigo": caixa[email], "manter": manter}, headers={"user-agent": ua})
    assert r.status_code == 200
    return r


def test_manter_conectado_define_o_cookie_e_a_validade(api, caixa):
    http, _, banco = api
    cadastrar(http, caixa)
    http.post("/auth/sair")
    r = entrar_em(http, caixa, manter=True)
    assert "Max-Age=2592000" in r.headers["set-cookie"]  # 30 dias
    s = banco.um("SELECT expira, criada, manter FROM sessoes ORDER BY criada DESC")
    assert s["manter"] == 1 and 29.9 * 86400 < s["expira"] - s["criada"] <= 30 * 86400
    http.post("/auth/sair")
    r = entrar_em(http, caixa, manter=False)
    cab = next(c for c in r.headers.get_list("set-cookie") if c.startswith("orbita_sessao="))
    assert "Max-Age" not in cab and "expires" not in cab.lower()  # cookie some ao fechar o navegador
    s = banco.um("SELECT expira, criada, manter FROM sessoes ORDER BY criada DESC")
    assert s["manter"] == 0 and s["expira"] - s["criada"] <= 12 * 3600


def test_sessao_expirada_pede_login(api, caixa):
    http, _, banco = api
    cadastrar(http, caixa)
    banco.executar("UPDATE sessoes SET expira = ?", time.time() - 1)
    assert http.get("/auth/sessao").status_code == 401


def test_novo_login_troca_o_token_deste_navegador(api, caixa):
    http, _, banco = api
    cadastrar(http, caixa)
    entrar_em(http, caixa)
    assert banco.um("SELECT count(*) AS n FROM sessoes")["n"] == 1


def test_aparelhos_conectados_e_sair_de_um(api, caixa):
    from fastapi.testclient import TestClient

    http, _, _ = api
    cadastrar(http, caixa)
    celular = TestClient(http.app)
    entrar_em(celular, caixa, ua="Mozilla/5.0 (Linux; Android 14) Chrome/130 Mobile")
    lista = http.get("/auth/sessoes").json()
    assert len(lista) == 2 and sum(s["atual"] for s in lista) == 1
    outro = next(s for s in lista if not s["atual"])
    assert outro["aparelho"] == "Chrome no Android"
    assert http.delete(f"/auth/sessoes/{outro['id']}").status_code == 204
    assert celular.get("/auth/sessao").status_code == 401
    assert http.get("/auth/sessao").status_code == 200
    assert http.delete(f"/auth/sessoes/{outro['id']}").status_code == 404


def test_nao_encerra_sessao_de_outra_conta(api, caixa):
    from fastapi.testclient import TestClient

    http, _, _ = api
    cadastrar(http, caixa)
    bia = TestClient(http.app)
    cadastrar(bia, caixa, email="bia@exemplo.test")
    id_bia = bia.get("/auth/sessoes").json()[0]["id"]
    assert http.delete(f"/auth/sessoes/{id_bia}").status_code == 404
    assert bia.get("/auth/sessao").status_code == 200


def test_sair_de_todos(api, caixa):
    from fastapi.testclient import TestClient

    http, _, _ = api
    cadastrar(http, caixa)
    outro = TestClient(http.app)
    entrar_em(outro, caixa)
    assert http.post("/auth/sair-de-todos").status_code == 204
    assert http.get("/auth/sessao").status_code == 401
    assert outro.get("/auth/sessao").status_code == 401


def test_aparelho_pelo_user_agent():
    assert auth.aparelho("Mozilla/5.0 (Windows NT 10.0; Win64) AppleWebKit Chrome/130 Safari/537 Edg/130") == "Edge no Windows"
    assert auth.aparelho("Mozilla/5.0 (iPhone; CPU iPhone OS 18) AppleWebKit Version/18 Safari/604") == "Safari no iPhone"
    assert auth.aparelho("") == "Navegador"
