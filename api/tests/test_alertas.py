"""Item 44: alertas por tema e resumo semanal guardados na conta, gravação só no plano Ouro."""
from __future__ import annotations

from tests.test_billing import entrar


def _ouro(http, banco):
    entrar(http, banco)
    r = http.post("/billing/assinatura", json={"nome": "Teste Silva", "cpf_cnpj": "52998224725", "plano": "ouro", "forma": "pix"})
    assert r.status_code == 201
    assert http.post("/billing/assinatura/simular-pagamento").status_code == 200


def test_ler_exige_sessao_e_gravar_exige_ouro(api):
    http, _, banco = api
    assert http.get("/alertas").status_code == 401
    entrar(http, banco)
    r = http.get("/alertas").json()
    assert r == {"ouro": False, "temas": [], "resumo": {"areas": [], "dia": "segunda"}, "enviados": []}
    assert http.put("/alertas/temas", json=[{"tema": "ICMS-ST"}]).status_code == 403
    assert http.put("/alertas/resumo", json={"areas": ["Previdenciário"]}).status_code == 403


def test_ouro_salva_temas_e_resumo(api):
    http, _, banco = api
    _ouro(http, banco)
    temas = [
        {"tema": "  Crédito de   PIS/Cofins ", "fontes": ["normas", "administrativo"], "frequencia": "diario"},
        {"tema": "crédito de pis/cofins"},  # repetido: sai
        {"tema": "ICMS-ST"},
    ]
    r = http.put("/alertas/temas", json=temas)
    assert r.status_code == 200
    salvo = http.get("/alertas").json()
    assert salvo["ouro"] is True
    assert [t["tema"] for t in salvo["temas"]] == ["Crédito de PIS/Cofins", "ICMS-ST"]
    assert salvo["temas"][0]["fontes"] == ["administrativo", "normas"] and salvo["temas"][0]["frequencia"] == "diario"
    assert salvo["temas"][1]["fontes"] == ["superiores", "administrativo", "normas", "regionais"]
    r = http.put("/alertas/resumo", json={"areas": ["Previdenciário", "Tributário federal"], "dia": "sexta"})
    assert r.status_code == 200
    assert http.get("/alertas").json()["resumo"] == {"areas": ["Tributário federal", "Previdenciário"], "dia": "sexta"}


def test_validacao_dos_dados(api):
    http, _, banco = api
    _ouro(http, banco)
    assert http.put("/alertas/temas", json=[{"tema": "ab"}]).status_code == 422
    assert http.put("/alertas/temas", json=[{"tema": "x" * 61}]).status_code == 422
    assert http.put("/alertas/temas", json=[{"tema": "ICMS", "fontes": []}]).status_code == 422
    assert http.put("/alertas/temas", json=[{"tema": "ICMS", "fontes": ["inventada"]}]).status_code == 422
    assert http.put("/alertas/temas", json=[{"tema": "ICMS", "frequencia": "a cada minuto"}]).status_code == 422
    assert http.put("/alertas/temas", json=[{"tema": f"tema {i}"} for i in range(21)]).status_code == 422
    assert http.put("/alertas/resumo", json={"areas": ["Inventada"]}).status_code == 422
    assert http.put("/alertas/resumo", json={"areas": [], "dia": "domingo"}).status_code == 422
