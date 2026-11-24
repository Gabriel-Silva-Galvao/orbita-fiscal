"""Testes da cobrança da Órbita (etapa 4), de ponta a ponta com a simulação do Asaas.

Os webhooks da simulação chegam de verdade em /webhooks/asaas (ver conftest.py), então a
liberação do acesso é testada pelo mesmo caminho que valerá com o Asaas real.
"""
from __future__ import annotations

from datetime import date, timedelta

from app.config import get_settings

CHAVE = get_settings().asaas_api_key
TOKEN = get_settings().asaas_webhook_token
CARTAO = {"titular": "TESTE SILVA", "numero": "4444444444444444", "mes": "12", "ano": "2030", "cvv": "123"}


def assinar(http, forma: str, usuario: str = "u1", plano: str = "pro", **extra):
    corpo = {"usuario_id": usuario, "nome": "Teste Silva", "email": "teste@exemplo.com", "cpf_cnpj": "529.982.247-25", "plano": plano, "forma": forma, **extra}
    return http.post("/billing/assinaturas", json=corpo)


def confirmar(http, cobranca_id: str):
    r = http.post(f"/asaas-sim/v3/sandbox/payment/{cobranca_id}/confirm", headers={"access_token": CHAVE})
    assert r.status_code == 200, r.text


def status(http, usuario: str = "u1") -> str:
    return http.get(f"/billing/assinaturas/{usuario}").json()["status_acesso"]


def test_pix_fica_pendente_e_libera_com_o_webhook(api):
    http, *_ = api
    r = assinar(http, "pix")
    assert r.status_code == 201, r.text
    dados = r.json()
    assert dados["status_acesso"] == "pendente" and dados["valor"] == 50.0
    [cob] = dados["cobrancas"]
    assert cob["status"] == "PENDING" and cob["pix"]["copia_e_cola"].startswith("000201")
    confirmar(http, cob["id"])
    assert status(http) == "ativo"


def test_boleto_vence_em_3_dias_e_libera_na_compensacao(api):
    http, *_ = api
    dados = assinar(http, "boleto", plano="max").json()
    [cob] = dados["cobrancas"]
    assert dados["valor"] == 75.9 and cob["vencimento"] == (date.today() + timedelta(days=3)).isoformat()
    assert len(cob["boleto"]["linha_digitavel"]) == 47
    assert dados["status_acesso"] == "pendente"
    confirmar(http, cob["id"])
    assert status(http) == "ativo"


def test_cartao_aprovado_libera_na_hora(api):
    http, *_ = api
    dados = assinar(http, "cartao", cartao=CARTAO, ip="200.1.2.3").json()
    assert dados["status_acesso"] == "ativo" and dados["cobrancas"][0]["status"] == "CONFIRMED"


def test_cartao_recusado_devolve_mensagem_e_nao_cria_assinatura(api):
    http, *_ = api
    r = assinar(http, "cartao", cartao={**CARTAO, "numero": "5184019740373151"})
    assert r.status_code == 400
    assert r.json()["detail"]["codigo"] == "invalid_creditCard"
    assert http.get("/billing/assinaturas/u1").status_code == 404


def test_nao_deixa_assinar_duas_vezes(api):
    http, *_ = api
    assert assinar(http, "pix").status_code == 201
    r = assinar(http, "boleto")
    assert r.status_code == 409 and r.json()["detail"]["codigo"] == "ja_assinante"


def test_webhook_exige_token(api):
    http, *_ = api
    r = http.post("/webhooks/asaas", json={"id": "evt_x", "event": "PAYMENT_RECEIVED"}, headers={"asaas-access-token": "errado"})
    assert r.status_code == 401


def test_webhook_repetido_nao_reprocessa(api):
    http, store, banco = api
    [cob] = assinar(http, "pix").json()["cobrancas"]
    confirmar(http, cob["id"])
    evento = next(e for e in store.eventos if e["event"] == "PAYMENT_RECEIVED")
    # Alguém muda o status por fora; o mesmo evento chegando de novo não pode reativar.
    banco.executar("UPDATE assinaturas SET status_acesso = 'suspenso' WHERE usuario_id = 'u1'")
    r = http.post("/webhooks/asaas", json=evento, headers={"asaas-access-token": TOKEN})
    assert r.json() == {"ok": True, "duplicado": True}
    assert status(http) == "suspenso"


def test_vencimento_suspende(api):
    http, *_ = api
    [cob] = assinar(http, "boleto").json()["cobrancas"]
    http.post(f"/asaas-sim/v3/sandbox/payment/{cob['id']}/overdue", headers={"access_token": CHAVE})
    assert status(http) == "suspenso"


def test_trocar_forma_de_pagamento(api):
    http, *_ = api
    assinar(http, "pix")
    r = http.put("/billing/assinaturas/u1/forma", json={"forma": "boleto"})
    assert r.status_code == 200 and r.json()["forma"] == "boleto"
    assert r.json()["cobrancas"][0]["forma"] == "boleto" and "boleto" in r.json()["cobrancas"][0]


def test_cancelar(api):
    http, *_ = api
    assinar(http, "pix")
    assert http.delete("/billing/assinaturas/u1").json()["status_acesso"] == "cancelado"
    assert status(http) == "cancelado"
    assert assinar(http, "boleto").status_code == 201  # depois de cancelar, pode assinar de novo


def test_reembolso_dentro_de_7_dias(api):
    http, *_ = api
    dados = assinar(http, "cartao", cartao=CARTAO, ip="200.1.2.3").json()
    r = http.post("/billing/assinaturas/u1/reembolso")
    assert r.status_code == 200 and r.json()["status_acesso"] == "reembolsado"
    assert r.json()["cobrancas_estornadas"] == [dados["cobrancas"][0]["id"]]
    assert status(http) == "reembolsado"


def test_reembolso_fora_do_prazo(api):
    http, _, banco = api
    assinar(http, "cartao", cartao=CARTAO, ip="200.1.2.3")
    antiga = (date.today() - timedelta(days=8)).isoformat()
    banco.executar("UPDATE assinaturas SET primeira_paga_em = ? WHERE usuario_id = 'u1'", antiga)
    r = http.post("/billing/assinaturas/u1/reembolso")
    assert r.status_code == 400 and r.json()["detail"]["codigo"] == "fora_do_prazo"


def test_asaas_fora_do_ar_vira_502_com_mensagem(api, tmp_path):
    http, *_ = api
    from app.asaas.client import AsaasClient

    http.app.state.asaas = AsaasClient("http://127.0.0.1:1/v3", CHAVE)  # porta sem ninguém ouvindo
    r = assinar(http, "pix")
    assert r.status_code == 502 and r.json()["detail"]["codigo"] == "asaas_indisponivel"


def test_reembolso_sem_pagamento(api):
    http, *_ = api
    assinar(http, "pix")
    r = http.post("/billing/assinaturas/u1/reembolso")
    assert r.status_code == 400 and r.json()["detail"]["codigo"] == "nada_pago"
