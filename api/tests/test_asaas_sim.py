"""Testes da simulação do Asaas, usando o próprio cliente da API (como será com o Asaas real)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.asaas.client import AsaasClient, AsaasError
from app.asaas_sim.store import Store
from app.config import get_settings
from app.db import Banco
from app.main import create_app

CHAVE = get_settings().asaas_api_key
CARTAO_OK = {"holderName": "TESTE SILVA", "number": "4444 4444 4444 4444", "expiryMonth": "12", "expiryYear": "2030", "ccv": "123"}
TITULAR = {"name": "Teste Silva", "email": "teste@exemplo.com", "cpfCnpj": "52998224725", "postalCode": "30140000", "addressNumber": "1", "phone": "31999999999"}


@pytest.fixture
def ctx(tmp_path):
    entregues: list[tuple[str, dict, dict]] = []

    def enviar(url: str, corpo: dict, headers: dict) -> int:
        entregues.append((url, corpo, headers))
        return 200

    store = Store(enviar=enviar)
    http = TestClient(create_app(store, banco=Banco(str(tmp_path / "t.db"))))
    store.webhooks.clear()  # aqui só a simulação: sem o webhook da Órbita cadastrado pela API
    asaas = AsaasClient("http://testserver/asaas-sim/v3", CHAVE, http=http)
    return asaas, store, http, entregues


def cliente(asaas: AsaasClient) -> dict:
    return asaas.criar_cliente(name="Teste Silva", cpfCnpj="529.982.247-25", email="teste@exemplo.com")


def assinatura(asaas: AsaasClient, cus: str, forma: str, **extra) -> dict:
    return asaas.criar_assinatura(customer=cus, billingType=forma, value=50.0, nextDueDate="2026-11-27", cycle="MONTHLY", description="Órbita Pro", **extra)


def test_autenticacao(ctx):
    _, _, http, _ = ctx
    sem = http.post("/asaas-sim/v3/customers", json={})
    assert sem.status_code == 401 and sem.json()["errors"][0]["code"] == "access_token_not_found"
    errada = http.post("/asaas-sim/v3/customers", json={}, headers={"access_token": "$aact_hmlg_outra"})
    assert errada.status_code == 401 and errada.json()["errors"][0]["code"] == "invalid_access_token"


def test_cliente_e_validacao(ctx):
    asaas, *_ = ctx
    c = cliente(asaas)
    assert c["id"].startswith("cus_") and c["cpfCnpj"] == "52998224725" and c["personType"] == "FISICA"
    with pytest.raises(AsaasError) as e:
        asaas.criar_cliente(name="Sem documento")
    assert e.value.status == 400 and e.value.codigo == "invalid_cpfCnpj"


def test_pix_pendente_ate_confirmar(ctx):
    asaas, store, _, _ = ctx
    sub = assinatura(asaas, cliente(asaas)["id"], "PIX")
    assert sub["id"].startswith("sub_") and sub["status"] == "ACTIVE"
    [cob] = asaas.cobrancas_da_assinatura(sub["id"])
    assert cob["status"] == "PENDING" and cob["billingType"] == "PIX" and cob["subscription"] == sub["id"]
    qr = asaas.pix_qrcode(cob["id"])
    assert qr["payload"].startswith("000201") and qr["encodedImage"]
    pago = asaas.confirmar_no_sandbox(cob["id"])
    assert pago["status"] == "RECEIVED" and pago["paymentDate"]
    nomes = [e["event"] for e in store.eventos]
    assert nomes == ["SUBSCRIPTION_CREATED", "PAYMENT_CREATED", "PAYMENT_RECEIVED"]


def test_boleto_linha_digitavel(ctx):
    asaas, *_ = ctx
    sub = assinatura(asaas, cliente(asaas)["id"], "BOLETO")
    [cob] = asaas.cobrancas_da_assinatura(sub["id"])
    assert cob["bankSlipUrl"] and cob["nossoNumero"]
    linha = asaas.linha_digitavel(cob["id"])
    assert len(linha["identificationField"]) == 47 and linha["identificationField"].isdigit()
    assert len(linha["barCode"]) == 44
    with pytest.raises(AsaasError):
        asaas.pix_qrcode(cob["id"])


def test_cartao_aprovado_confirma_na_hora(ctx):
    asaas, store, _, _ = ctx
    sub = assinatura(asaas, cliente(asaas)["id"], "CREDIT_CARD", creditCard=CARTAO_OK, creditCardHolderInfo=TITULAR, remoteIp="200.1.2.3")
    [cob] = asaas.cobrancas_da_assinatura(sub["id"])
    assert cob["status"] == "CONFIRMED" and cob["creditCard"]["creditCardNumber"] == "4444"
    assert [e["event"] for e in store.eventos][-1] == "PAYMENT_CONFIRMED"


def test_cartao_recusado_nao_grava_nada(ctx):
    asaas, store, _, _ = ctx
    cus = cliente(asaas)["id"]
    recusado = {**CARTAO_OK, "number": "5184019740373151"}
    with pytest.raises(AsaasError) as e:
        assinatura(asaas, cus, "CREDIT_CARD", creditCard=recusado, creditCardHolderInfo=TITULAR, remoteIp="200.1.2.3")
    assert e.value.status == 400 and e.value.codigo == "invalid_creditCard"
    assert "Transação não autorizada" in e.value.descricao
    assert not store.assinaturas and not store.cobrancas


def test_cartao_sem_ip_e_recusado_antes_de_gravar(ctx):
    asaas, store, _, _ = ctx
    with pytest.raises(AsaasError) as e:
        assinatura(asaas, cliente(asaas)["id"], "CREDIT_CARD", creditCard=CARTAO_OK, creditCardHolderInfo=TITULAR)
    assert e.value.codigo == "invalid_remoteIp" and not store.assinaturas


def test_estorno_total_e_parcial(ctx):
    asaas, store, _, _ = ctx
    sub = assinatura(asaas, cliente(asaas)["id"], "PIX")
    [cob] = asaas.cobrancas_da_assinatura(sub["id"])
    with pytest.raises(AsaasError):
        asaas.estornar(cob["id"])  # ainda não foi paga
    asaas.confirmar_no_sandbox(cob["id"])
    parcial = asaas.estornar(cob["id"], valor=20.0)
    assert parcial["status"] == "RECEIVED" and parcial["refunds"][0]["value"] == 20.0
    with pytest.raises(AsaasError) as e:
        asaas.estornar(cob["id"], valor=40.0)  # passa do que resta (30,00)
    assert e.value.codigo == "invalid_value"
    total = asaas.estornar(cob["id"])
    assert total["status"] == "REFUNDED"
    assert [e["event"] for e in store.eventos][-2:] == ["PAYMENT_PARTIALLY_REFUNDED", "PAYMENT_REFUNDED"]


def test_trocar_forma_e_cancelar(ctx):
    asaas, store, _, _ = ctx
    sub = assinatura(asaas, cliente(asaas)["id"], "PIX")
    novo = asaas.atualizar_assinatura(sub["id"], billingType="BOLETO", updatePendingPayments=True)
    assert novo["billingType"] == "BOLETO"
    [cob] = asaas.cobrancas_da_assinatura(sub["id"])
    assert cob["billingType"] == "BOLETO"
    assert asaas.cancelar_assinatura(sub["id"]) == {"deleted": True, "id": sub["id"]}
    with pytest.raises(AsaasError) as e:
        asaas.obter_assinatura(sub["id"])
    assert e.value.status == 404
    nomes = [e["event"] for e in store.eventos]
    assert "PAYMENT_DELETED" in nomes and nomes[-1] == "SUBSCRIPTION_DELETED"


def test_vencimento_forcado(ctx):
    _, store, http, _ = ctx
    asaas = AsaasClient("http://testserver/asaas-sim/v3", CHAVE, http=http)
    sub = assinatura(asaas, cliente(asaas)["id"], "BOLETO")
    [cob] = asaas.cobrancas_da_assinatura(sub["id"])
    r = http.post(f"/asaas-sim/v3/sandbox/payment/{cob['id']}/overdue", headers={"access_token": CHAVE})
    assert r.status_code == 200 and r.json()["status"] == "OVERDUE"
    assert store.eventos[-1]["event"] == "PAYMENT_OVERDUE"


def test_webhook_recebe_eventos_com_token(ctx):
    asaas, _, _, entregues = ctx
    wh = asaas.cadastrar_webhook(
        name="Órbita", url="http://localhost:8000/webhooks/asaas", email="dev@exemplo.com",
        enabled=True, interrupted=False, sendType="SEQUENTIALLY",
        events=["PAYMENT_RECEIVED", "PAYMENT_CONFIRMED"], authToken="t" * 32,
    )
    assert wh["id"].startswith("wh_")
    sub = assinatura(asaas, cliente(asaas)["id"], "PIX")
    [cob] = asaas.cobrancas_da_assinatura(sub["id"])
    assert entregues == []  # PAYMENT_CREATED não foi assinado
    asaas.confirmar_no_sandbox(cob["id"])
    [(url, corpo, headers)] = entregues
    assert url.endswith("/webhooks/asaas") and headers["asaas-access-token"] == "t" * 32
    assert corpo["event"] == "PAYMENT_RECEIVED" and corpo["payment"]["id"] == cob["id"] and corpo["id"].startswith("evt_")


def test_webhook_pausa_depois_de_15_falhas():
    store = Store(enviar=lambda *_: 500)
    store.cadastrar_webhook({"name": "x", "url": "http://x", "email": "a@b.c", "sendType": "SEQUENTIALLY", "events": ["PAYMENT_CREATED"], "authToken": "t" * 32})
    cus = store.criar_cliente({"name": "A", "cpfCnpj": "52998224725"})["id"]
    for _ in range(15):
        store.criar_assinatura({"customer": cus, "billingType": "PIX", "value": 50, "nextDueDate": "2026-11-27", "cycle": "MONTHLY"})
    [wh] = store.webhooks.values()
    assert wh["interrupted"] is True
    antes = len(store.entregas)
    store.criar_assinatura({"customer": cus, "billingType": "PIX", "value": 50, "nextDueDate": "2026-11-27", "cycle": "MONTHLY"})
    assert len(store.entregas) == antes  # fila pausada: não tenta mais


def test_saude(ctx):
    _, _, http, _ = ctx
    assert http.get("/saude").json() == {"ok": True, "asaas": "simulacao"}
