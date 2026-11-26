"""Regressão ARES-QA-009: CPF e CNPJ com dígito verificador errado eram aceitos (só contava 11 ou 14 dígitos)."""
from __future__ import annotations

import pytest

from app.documentos import normalizar_documento
from tests.conftest import entrar
from tests.test_billing import assinar


@pytest.mark.parametrize("texto,esperado", [
    ("529.982.247-25", "52998224725"),
    ("11.222.333/0001-81", "11222333000181"),
    ("12.ABC.345/01DE-35", "12ABC34501DE35"),  # CNPJ alfanumérico, exemplo oficial da Receita (2026)
    ("12.abc.345/01de-35", "12ABC34501DE35"),
])
def test_documentos_validos(texto, esperado):
    assert normalizar_documento(texto) == esperado


@pytest.mark.parametrize("texto", [
    "529.982.247-24", "00000000000", "11111111111", "11.222.333/0001-80", "12.ABC.345/01DE-36", "00000000000000",
    "123", "52998224725X", "AB.CDE.FGH/IJKL-MN", "",
])
def test_documentos_invalidos(texto):
    assert normalizar_documento(texto) is None


def test_api_recusa_documento_com_digito_errado(api):
    http, store, banco = api
    entrar(http, banco)
    r = assinar(http, "pix", cpf_cnpj="529.982.247-24")
    assert r.status_code == 422 and r.json()["detail"]["codigo"] == "dados_invalidos"
    assert not store.clientes and not store.assinaturas  # nada chegou ao Asaas
    assert assinar(http, "pix").status_code == 201
    assert http.put("/billing/nota", json={"nome": "Ana", "cpf_cnpj": "000.000.000-00"}).status_code == 422
    r = http.put("/billing/nota", json={"nome": "Souza Ltda", "cpf_cnpj": "11.222.333/0001-81"})
    assert r.status_code == 200 and r.json()["cpf_cnpj"] == "11222333000181"
    # CNPJ alfanumérico passa na validação da API (test_documentos_validos); o envio ao Asaas ainda não foi
    # conferido com o Asaas real, e a simulação só aceita dígitos.
