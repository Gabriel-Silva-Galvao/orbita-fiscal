"""Conta e segurança (item 9): troca de senha e de e-mail com código, preferências e dados da nota fiscal."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import auth
from tests.test_billing import assinar


@pytest.fixture
def caixa(monkeypatch):
    recebidos: dict[str, str] = {}
    monkeypatch.setattr(auth, "enviar_codigo", lambda email, codigo: recebidos.__setitem__(email, codigo))
    return recebidos


def cadastrar(http, caixa, email="ana@exemplo.test", senha="senha-forte-1"):
    assert http.post("/auth/cadastro", json={"nome": "Ana", "email": email, "senha": senha}).status_code == 202
    assert http.post("/auth/codigo", json={"codigo": caixa[email]}).status_code == 200


def test_troca_de_senha_com_codigo_derruba_as_outras_sessoes(api, caixa):
    http, *_ = api
    cadastrar(http, caixa)
    outro = TestClient(http.app)
    assert outro.post("/auth/login", json={"email": "ana@exemplo.test", "senha": "senha-forte-1"}).status_code == 202
    assert outro.post("/auth/codigo", json={"codigo": caixa["ana@exemplo.test"]}).status_code == 200

    assert http.post("/auth/senha/trocar", json={"atual": "errada", "nova": "outra-senha-2"}).status_code == 401
    assert http.post("/auth/senha/trocar", json={"atual": "senha-forte-1", "nova": "curta"}).status_code == 422
    assert http.post("/auth/senha/trocar", json={"atual": "senha-forte-1", "nova": "outra-senha-2"}).status_code == 202
    assert http.post("/auth/confirmar", json={"codigo": "000000"}).status_code == 400
    r = http.post("/auth/confirmar", json={"codigo": caixa["ana@exemplo.test"]})
    assert r.status_code == 200 and r.json()["trocou"] == "senha"

    assert http.get("/auth/sessao").status_code == 200  # esta continua
    assert outro.get("/auth/sessao").status_code == 401  # a outra caiu
    http.post("/auth/sair")
    assert http.post("/auth/login", json={"email": "ana@exemplo.test", "senha": "senha-forte-1"}).status_code == 401
    assert http.post("/auth/login", json={"email": "ana@exemplo.test", "senha": "outra-senha-2"}).status_code == 202


def test_troca_de_email_confirma_no_endereco_novo(api, caixa):
    http, *_ = api
    cadastrar(http, caixa)
    cadastrar(TestClient(http.app), caixa, email="bia@exemplo.test")
    assert http.post("/auth/email/trocar", json={"email": "bia@exemplo.test"}).status_code == 409
    assert http.post("/auth/email/trocar", json={"email": "ana@exemplo.test"}).status_code == 422
    assert http.post("/auth/email/trocar", json={"email": "Ana.Nova@Exemplo.test"}).status_code == 202
    assert "ana.nova@exemplo.test" in caixa  # o código foi para o endereço novo
    r = http.post("/auth/confirmar", json={"codigo": caixa["ana.nova@exemplo.test"]})
    assert r.status_code == 200 and r.json()["email"] == "ana.nova@exemplo.test"
    assert http.get("/auth/sessao").json()["email"] == "ana.nova@exemplo.test"


def test_codigo_de_troca_nao_serve_para_entrar(api, caixa):
    http, *_ = api
    cadastrar(http, caixa)
    http.post("/auth/senha/trocar", json={"atual": "senha-forte-1", "nova": "outra-senha-2"})
    assert http.post("/auth/codigo", json={"codigo": caixa["ana@exemplo.test"]}).status_code == 410


def test_preferencias(api, caixa):
    http, *_ = api
    assert http.get("/auth/preferencias").status_code == 401
    cadastrar(http, caixa)
    assert http.get("/auth/preferencias").json() == {"novidades": True, "resumo_semanal": True, "avisos_de_cobranca": True}
    assert http.put("/auth/preferencias", json={"novidades": False, "resumo_semanal": True}).status_code == 200
    assert http.get("/auth/preferencias").json()["novidades"] is False


def test_dados_da_nota(api, caixa):
    http, store, _ = api
    cadastrar(http, caixa)
    assert http.get("/billing/nota").json() is None
    assert http.put("/billing/nota", json={"nome": "Ana", "cpf_cnpj": "52998224725"}).status_code == 409  # sem compra ainda
    assert assinar(http, "pix").status_code == 201
    assert http.put("/billing/nota", json={"nome": "Ana", "cpf_cnpj": "123"}).status_code == 422
    r = http.put("/billing/nota", json={"nome": "Ana Souza Advocacia", "cpf_cnpj": "11.222.333/0001-81", "endereco": "Rua A, 10"})
    assert r.status_code == 200 and r.json()["cpf_cnpj"] == "11222333000181"
    nota = http.get("/billing/nota").json()
    assert nota["nome"] == "Ana Souza Advocacia" and nota["endereco"] == "Rua A, 10"
    cliente = next(iter(store.clientes.values()))
    assert cliente["name"] == "Ana Souza Advocacia" and cliente["personType"] == "JURIDICA"
