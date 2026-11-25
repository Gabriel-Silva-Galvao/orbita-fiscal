"""Contato para planos empresariais (item 26)."""
from __future__ import annotations

from app import correio

OK = {
    "nome": "Ana Souza",
    "empresa": "Souza Contabilidade",
    "email": "ana@exemplo.test",
    "usuarios": "6 a 20",
    "mensagem": "Queremos o plano para a equipe toda.",
}


def test_registra_e_envia(api, monkeypatch):
    http, _, banco = api
    enviados = []
    monkeypatch.setattr(correio, "enviar", lambda m: enviados.append(m) or True)
    r = http.post("/contato/empresarial", json=OK)
    assert r.status_code == 202 and r.json()["enviado"] is True
    assert enviados[0]["To"] == "contato@orbitafiscal.com.br" and enviados[0]["Reply-To"] == "ana@exemplo.test"
    assert "Souza Contabilidade" in enviados[0]["Subject"] and enviados[1]["To"] == "ana@exemplo.test"
    assert banco.um("SELECT empresa, enviado FROM contatos") == {"empresa": "Souza Contabilidade", "enviado": 1}


def test_sem_smtp_so_registra(api):
    http, _, banco = api
    r = http.post("/contato/empresarial", json=OK)
    assert r.status_code == 202 and r.json()["enviado"] is False
    assert banco.um("SELECT enviado FROM contatos")["enviado"] == 0


def test_dados_invalidos_e_isca(api):
    http, _, banco = api
    assert http.post("/contato/empresarial", json={**OK, "email": "sem-arroba"}).status_code == 422
    assert http.post("/contato/empresarial", json={**OK, "mensagem": "oi"}).status_code == 422
    r = http.post("/contato/empresarial", json={**OK, "site": "http://spam.test"})
    assert r.status_code == 202 and banco.um("SELECT count(*) AS n FROM contatos")["n"] == 0


def test_limite_por_ip(api):
    http, *_ = api
    codigos = [http.post("/contato/empresarial", json=OK).status_code for _ in range(6)]
    assert codigos[:5] == [202] * 5 and codigos[5] == 429
