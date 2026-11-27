"""Serviços de conta e plugin (preparação para suporte e admin, passo 3): situação da conta e última atividade."""
from __future__ import annotations

import pytest

from app.config import get_settings
from app.servicos import contas, plugin
from app.servicos.base import Ator, ErroDeNegocio
from tests.conftest import entrar

EQUIPE = Ator("equipe", "e1", papel="admin", motivo="teste")


def test_conta_nova_esta_ativa_e_marca_atividade(api):
    http, _, banco = api
    entrar(http, banco)
    assert contas.situacao(banco, "u1") == "ativa"
    assert http.get("/auth/sessao").status_code == 200
    assert banco.um("SELECT ultima_atividade FROM usuarios WHERE id = 'u1'")["ultima_atividade"]


def test_suspensao_derruba_a_sessao_e_bloqueia_o_login(api):
    http, _, banco = api
    entrar(http, banco)
    contas.suspender(banco, EQUIPE, "u1", "Uso indevido relatado no chamado 7")
    assert http.get("/auth/sessao").status_code == 401  # a sessão caiu
    assert http.get("/billing/plano").status_code == 401
    r = http.post("/auth/login", json={"email": "teste@exemplo.com", "senha": "qualquer-coisa"})
    assert r.status_code in (401, 403)  # senha errada responde 401 antes; com a certa, 403 conta_suspensa (abaixo)


def test_login_de_conta_suspensa_recebe_403(api):
    http, _, banco = api
    from app.auth import hash_senha

    banco.executar("INSERT INTO usuarios (id, email, nome, senha_hash) VALUES ('u9', 'bia@exemplo.test', 'Bia', ?)", hash_senha("Senha-forte-123!"))
    contas.suspender(banco, EQUIPE, "u9", "Teste de suspensão")
    r = http.post("/auth/login", json={"email": "bia@exemplo.test", "senha": "Senha-forte-123!"})
    assert r.status_code == 403 and r.json()["codigo"] == "conta_suspensa"
    contas.reativar(banco, EQUIPE, "u9", "Resolvido no chamado")
    assert http.post("/auth/login", json={"email": "bia@exemplo.test", "senha": "Senha-forte-123!"}).status_code == 202


def test_so_equipe_ou_sistema_suspendem_e_sempre_com_motivo(api):
    http, _, banco = api
    entrar(http, banco)
    with pytest.raises(ErroDeNegocio) as e:
        contas.suspender(banco, Ator.cliente("u1"), "u1", "quero")
    assert e.value.status == 403
    with pytest.raises(ErroDeNegocio) as e:
        contas.suspender(banco, EQUIPE, "u1", "  ")
    assert e.value.codigo == "motivo_obrigatorio"
    with pytest.raises(ErroDeNegocio) as e:
        contas.suspender(banco, EQUIPE, "nao-existe", "motivo qualquer")
    assert e.value.status == 404
    contas.suspender(banco, EQUIPE, "u1", "motivo qualquer")
    with pytest.raises(ErroDeNegocio) as e:
        contas.suspender(banco, EQUIPE, "u1", "de novo")
    assert e.value.codigo == "ja_suspensa"


def test_cliente_nao_encerra_sessoes_de_outra_conta(api):
    http, _, banco = api
    entrar(http, banco)
    with pytest.raises(ErroDeNegocio) as e:
        contas.encerrar_sessoes(banco, Ator.cliente("outra"), "u1")
    assert e.value.status == 403
    assert http.get("/auth/sessao").status_code == 200
    assert contas.encerrar_sessoes(banco, EQUIPE, "u1") == 1  # a pedido do cliente, pela equipe
    assert http.get("/auth/sessao").status_code == 401


def test_plugin_de_conta_suspensa_e_recusado_e_uso_marca_atividade(api, monkeypatch):
    http, _, banco = api
    segredo = "segredo-do-servidor-mcp-com-mais-de-32-caracteres"
    monkeypatch.setattr(get_settings(), "plugin_servidor_token", segredo)
    entrar(http, banco)
    banco.executar("UPDATE usuarios SET ultima_atividade = NULL WHERE id = 'u1'")
    cab = {"X-Orbita-Servidor": segredo}
    assert http.post("/plugin/uso", json={"email": "teste@exemplo.com", "ia": "claude"}, headers=cab).status_code == 204
    assert banco.um("SELECT ultima_atividade FROM usuarios WHERE id = 'u1'")["ultima_atividade"]
    contas.suspender(banco, EQUIPE, "u1", "teste do plugin")
    r = http.post("/plugin/uso", json={"email": "teste@exemplo.com", "ia": "claude"}, headers=cab)
    assert r.status_code == 403 and r.json()["codigo"] == "conta_suspensa"


def test_suporte_ve_so_o_resumo_do_plugin(api, monkeypatch):
    http, _, banco = api
    entrar(http, banco)
    plugin.registrar_conexao(banco, "u1", "claude")
    plugin.registrar_conexao(banco, "u1", "chatgpt")
    r = plugin.resumo_para_suporte(banco, "u1")
    assert set(r) == {"baixou", "conectou", "ultima_conexao", "ias"}
    assert sorted(r["ias"]) == ["chatgpt", "claude"] and "perguntas" not in r
