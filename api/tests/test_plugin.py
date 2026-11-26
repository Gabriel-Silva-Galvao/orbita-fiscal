"""Download do plugin de demonstração (item 6 da rodada de testes)."""
from __future__ import annotations

import io
import json
import time
import zipfile

from tests.test_billing import assinar, confirmar, entrar


def caminho(url: str) -> str:
    return url[url.index("/plugin/") :]


def test_link_exige_sessao_e_assinatura(api):
    http, *_ = api
    assert http.post("/plugin/link").status_code == 401
    entrar(http, api[2])
    r = http.post("/plugin/link")
    assert r.status_code == 403 and r.json()["codigo"] == "sem_acesso"
    r = assinar(http, "pix")
    assert http.post("/plugin/link").status_code == 403  # Pix ainda pendente: sem acesso
    confirmar(http, r.json()["cobrancas"][0]["id"])
    assert http.post("/plugin/link").status_code == 201


def test_baixa_o_zip_de_demonstracao(api):
    http, *_ = api
    entrar(http, api[2])
    r = assinar(http, "pix")
    confirmar(http, r.json()["cobrancas"][0]["id"])
    link = http.post("/plugin/link").json()
    assert link["demonstracao"] is True and link["arquivo"].endswith(".zip")
    z = http.get(caminho(link["url"]))
    assert z.status_code == 200 and z.headers["content-type"] == "application/zip"
    assert 'attachment; filename="orbita-plugin-' in z.headers["content-disposition"]
    with zipfile.ZipFile(io.BytesIO(z.content)) as arq:
        nomes = set(arq.namelist())
        assert {"orbita/README.md", "orbita/.claude-plugin/plugin.json", "orbita/skills/orbita-pesquisa/SKILL.md"} <= nomes
        assert "DEMONSTRAÇÃO" in arq.read("orbita/README.md").decode()
        assert json.loads(arq.read("orbita/.claude-plugin/plugin.json"))["name"] == "orbita"


def test_link_expira_e_link_desconhecido(api):
    http, _, banco = api
    entrar(http, banco)
    r = assinar(http, "pix")
    confirmar(http, r.json()["cobrancas"][0]["id"])
    url = caminho(http.post("/plugin/link").json()["url"])
    assert http.get(url).status_code == 200
    banco.executar("UPDATE downloads SET expira = ?", time.time() - 1)
    assert http.get(url).status_code == 410
    assert http.get("/plugin/baixar/nao-existe").status_code == 404
    assert banco.um("SELECT token_hash FROM downloads")["token_hash"] not in url  # só o hash fica guardado


# ---------- Item 40: status do plugin ----------
SEGREDO = "segredo-do-servidor-mcp-com-mais-de-32-caracteres"


def test_status_do_plugin_so_fica_ativo_com_plano_e_conexao(api, monkeypatch):
    from app.config import get_settings
    from tests.conftest import entrar
    from tests.test_billing import assinar

    http, _, banco = api
    monkeypatch.setattr(get_settings(), "plugin_servidor_token", SEGREDO)
    assert http.get("/plugin/status").status_code == 401
    entrar(http, banco, email="ana@exemplo.test")
    st = http.get("/plugin/status").json()
    assert st == {"ativo": False, "plano_ativo": False, "conectado": False, "primeira": None, "ultima": None, "ia": None}

    # O servidor MCP avisa o uso: precisa do segredo certo.
    corpo = {"email": "Ana@Exemplo.test", "ia": "claude"}
    assert http.post("/plugin/uso", json=corpo).status_code == 401
    assert http.post("/plugin/uso", json=corpo, headers={"X-Orbita-Servidor": "errado"}).status_code == 401
    assert http.post("/plugin/uso", json={"email": "ninguem@exemplo.test"}, headers={"X-Orbita-Servidor": SEGREDO}).status_code == 404
    assert http.post("/plugin/uso", json=corpo, headers={"X-Orbita-Servidor": SEGREDO}).status_code == 204
    st = http.get("/plugin/status").json()
    assert st["conectado"] is True and st["ia"] == "claude" and st["ativo"] is False  # conectado, mas sem plano

    assinar(http, "pix")
    http.post("/billing/assinatura/simular-pagamento")
    assert http.get("/plugin/status").json()["ativo"] is True


def test_uso_desligado_sem_segredo_e_simulacao_so_no_dev(api, monkeypatch):
    from app.config import get_settings
    from tests.conftest import entrar

    http, _, banco = api
    monkeypatch.setattr(get_settings(), "plugin_servidor_token", "")
    assert http.post("/plugin/uso", json={"email": "a@b.c"}, headers={"X-Orbita-Servidor": ""}).status_code == 503
    entrar(http, banco)
    assert http.post("/plugin/simular-conexao").status_code == 204
    assert http.get("/plugin/status").json()["conectado"] is True
    monkeypatch.setattr(get_settings(), "asaas_sim_enabled", False)
    assert http.post("/plugin/simular-conexao").status_code == 404
