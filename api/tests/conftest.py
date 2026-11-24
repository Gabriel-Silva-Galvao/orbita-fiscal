"""Monta a API inteira para os testes: banco temporário, simulação do Asaas e entrega real
dos webhooks da simulação para a rota /webhooks/asaas da própria API."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.asaas.client import AsaasClient
from app.asaas_sim.store import Store
from app.config import get_settings
from app.db import Banco
from app.main import create_app


@pytest.fixture
def api(tmp_path):
    settings = get_settings()
    store = Store()
    holder: dict = {}

    def enviar(url: str, corpo: dict, headers: dict) -> int:
        # A simulação "chama" o webhook: entrega direto na API sob teste.
        caminho = url.split(settings.api_public_url, 1)[-1]
        return holder["http"].post(caminho, json=corpo, headers=headers).status_code

    store.enviar = enviar
    banco = Banco(str(tmp_path / "teste.db"))
    app = create_app(store=store, banco=banco, asaas=None)
    http = TestClient(app)
    holder["http"] = http
    app.state.asaas = AsaasClient("http://testserver/asaas-sim/v3", settings.asaas_api_key, http=http)
    return http, store, banco
