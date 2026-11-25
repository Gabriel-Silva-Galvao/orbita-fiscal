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


def entrar(http, banco, uid: str = "u1", email: str = "teste@exemplo.com") -> None:
    """Cria a conta e a sessão direto no banco e põe o cookie no cliente (o login em si é testado em test_auth)."""
    import secrets
    import time

    from app import auth

    if not banco.um("SELECT 1 FROM usuarios WHERE id = ?", uid):
        banco.executar("INSERT INTO usuarios (id, email, nome, senha_hash) VALUES (?, ?, 'Teste Silva', 'x')", uid, email)
    token = secrets.token_urlsafe(16)
    banco.executar("INSERT INTO sessoes (token_hash, usuario_id, expira, id) VALUES (?, ?, ?, ?)", auth._sha(token), uid, time.time() + 3600, uid[:16])
    http.cookies.set(auth.COOKIE_SESSAO, token)
