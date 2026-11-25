"""Item 17: a API não sobe com configuração perigosa (docs/backend-e-seguranca.md, S1, S2 e S4)."""
from __future__ import annotations

import pytest

from app.config import CHAVE_SIMULACAO, TOKEN_WEBHOOK_EXEMPLO, Settings, get_settings, problemas_de_producao


def conf(**k):
    base = dict(asaas_sim_enabled=False, cookie_secure=True, asaas_webhook_token="x" * 40,
                asaas_api_key="$aact_prod_chave_de_verdade", auth_codigo_na_resposta=False)
    base.update(k)
    return Settings(_env_file=None, **base)


def test_producao_bem_configurada_sobe():
    assert problemas_de_producao(conf()) == []


def test_simulacao_nao_roda_em_producao():
    assert problemas_de_producao(conf(asaas_sim_enabled=True))


def test_segredos_de_exemplo_e_codigo_na_resposta_sao_recusados():
    assert problemas_de_producao(conf(asaas_webhook_token=TOKEN_WEBHOOK_EXEMPLO))
    assert problemas_de_producao(conf(asaas_webhook_token="curto"))
    assert problemas_de_producao(conf(asaas_api_key=CHAVE_SIMULACAO))
    assert problemas_de_producao(conf(auth_codigo_na_resposta=True))


def test_desenvolvimento_com_simulacao_sobe():
    assert problemas_de_producao(conf(asaas_sim_enabled=True, cookie_secure=False, asaas_webhook_token=TOKEN_WEBHOOK_EXEMPLO,
                                      asaas_api_key=CHAVE_SIMULACAO, auth_codigo_na_resposta=True)) == []


def test_create_app_recusa_subir(monkeypatch):
    from app.main import create_app

    monkeypatch.setenv("ASAAS_SIM_ENABLED", "false")
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="ASAAS_WEBHOOK_TOKEN"):
            create_app()
    finally:
        get_settings.cache_clear()


def test_webhook_recusa_token_errado(api):
    http, *_ = api
    assert http.post("/webhooks/asaas", json={"id": "e1", "event": "PAYMENT_RECEIVED"}).status_code == 401
    r = http.post("/webhooks/asaas", json={"id": "e1", "event": "PAYMENT_RECEIVED"}, headers={"asaas-access-token": "errado"})
    assert r.status_code == 401
