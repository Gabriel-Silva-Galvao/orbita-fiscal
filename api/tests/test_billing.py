"""Testes da cobrança da Órbita (etapa 4), de ponta a ponta com a simulação do Asaas.

Os webhooks da simulação chegam de verdade em /webhooks/asaas (ver conftest.py), então a
liberação do acesso é testada pelo mesmo caminho que valerá com o Asaas real.
"""
from __future__ import annotations

from datetime import date, timedelta

from app.config import get_settings
from tests.conftest import entrar

CHAVE = get_settings().asaas_api_key
TOKEN = get_settings().asaas_webhook_token
CARTAO = {"titular": "TESTE SILVA", "numero": "4444444444444444", "mes": "12", "ano": "2030", "cvv": "123"}


def assinar(http, forma: str, plano: str = "prata", **extra):
    corpo = {"nome": "Teste Silva", "cpf_cnpj": "529.982.247-25", "plano": plano, "forma": forma, **extra}
    return http.post("/billing/assinatura", json=corpo)


def confirmar(http, cobranca_id: str):
    r = http.post(f"/asaas-sim/v3/sandbox/payment/{cobranca_id}/confirm", headers={"access_token": CHAVE})
    assert r.status_code == 200, r.text


def status(http) -> str:
    return http.get("/billing/assinatura").json()["status_acesso"]


def test_pix_fica_pendente_e_libera_com_o_webhook(api):
    http, *_ = api
    entrar(http, api[2])
    r = assinar(http, "pix")
    assert r.status_code == 201, r.text
    dados = r.json()
    assert dados["status_acesso"] == "pendente" and dados["valor"] == 59.9
    [cob] = dados["cobrancas"]
    assert cob["status"] == "PENDING" and cob["pix"]["copia_e_cola"].startswith("000201")
    confirmar(http, cob["id"])
    assert status(http) == "ativo"


def test_boleto_vence_em_3_dias_e_libera_na_compensacao(api):
    http, *_ = api
    entrar(http, api[2])
    dados = assinar(http, "boleto", plano="ouro").json()
    [cob] = dados["cobrancas"]
    assert dados["valor"] == 119.9 and cob["vencimento"] == (date.today() + timedelta(days=3)).isoformat()
    assert len(cob["boleto"]["linha_digitavel"]) == 47
    assert dados["status_acesso"] == "pendente"
    confirmar(http, cob["id"])
    assert status(http) == "ativo"


def test_cartao_aprovado_libera_na_hora(api):
    http, *_ = api
    entrar(http, api[2])
    dados = assinar(http, "cartao", cartao=CARTAO).json()
    assert dados["status_acesso"] == "ativo" and dados["cobrancas"][0]["status"] == "CONFIRMED"


def test_cartao_recusado_devolve_mensagem_e_nao_cria_assinatura(api):
    http, *_ = api
    entrar(http, api[2])
    r = assinar(http, "cartao", cartao={**CARTAO, "numero": "5184019740373151"})
    assert r.status_code == 400
    assert r.json()["detail"]["codigo"] == "invalid_creditCard"
    assert http.get("/billing/assinatura").status_code == 404


def test_nao_deixa_assinar_duas_vezes(api):
    http, *_ = api
    entrar(http, api[2])
    assert assinar(http, "pix").status_code == 201
    r = assinar(http, "boleto")
    assert r.status_code == 409 and r.json()["detail"]["codigo"] == "ja_assinante"


def test_webhook_exige_token(api):
    http, *_ = api
    entrar(http, api[2])
    r = http.post("/webhooks/asaas", json={"id": "evt_x", "event": "PAYMENT_RECEIVED"}, headers={"asaas-access-token": "errado"})
    assert r.status_code == 401


def test_webhook_repetido_nao_reprocessa(api):
    http, store, banco = api
    entrar(http, api[2])
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
    entrar(http, api[2])
    [cob] = assinar(http, "boleto").json()["cobrancas"]
    http.post(f"/asaas-sim/v3/sandbox/payment/{cob['id']}/overdue", headers={"access_token": CHAVE})
    assert status(http) == "suspenso"


def test_trocar_forma_de_pagamento(api):
    http, *_ = api
    entrar(http, api[2])
    assinar(http, "pix")
    r = http.put("/billing/assinatura/forma", json={"forma": "boleto"})
    assert r.status_code == 200 and r.json()["forma"] == "boleto"
    assert r.json()["cobrancas"][0]["forma"] == "boleto" and "boleto" in r.json()["cobrancas"][0]


def test_cancelar_sem_pagar_encerra_na_hora(api):
    http, *_ = api
    entrar(http, api[2])
    assinar(http, "pix")
    assert http.delete("/billing/assinatura").json()["status_acesso"] == "cancelado"
    assert status(http) == "cancelado"
    assert assinar(http, "boleto").status_code == 201  # depois de cancelar, pode assinar de novo


def test_reembolso_dentro_de_7_dias(api):
    http, *_ = api
    entrar(http, api[2])
    dados = assinar(http, "cartao", cartao=CARTAO).json()
    r = http.post("/billing/assinatura/reembolso")
    assert r.status_code == 200 and r.json()["status_acesso"] == "reembolsado"
    assert r.json()["cobrancas_estornadas"] == [dados["cobrancas"][0]["id"]]
    assert status(http) == "reembolsado"


def test_reembolso_guarda_o_questionario_opcional(api):
    http, _, banco = api
    entrar(http, api[2])
    assinar(http, "cartao", cartao=CARTAO)
    r = http.post("/billing/assinatura/reembolso", json={"motivo": "dificil", "melhorar": "  Não achei   o plugin "})
    assert r.status_code == 200
    f = banco.um("SELECT motivo, melhorar FROM reembolso_feedback WHERE usuario_id = 'u1'")
    assert f == {"motivo": "dificil", "melhorar": "Não achei o plugin"}


def test_reembolso_recusa_motivo_desconhecido(api):
    http, *_ = api
    entrar(http, api[2])
    assinar(http, "cartao", cartao=CARTAO)
    assert http.post("/billing/assinatura/reembolso", json={"motivo": "qualquer"}).status_code == 422
    assert status(http) != "reembolsado"


def test_reembolso_fora_do_prazo(api):
    http, _, banco = api
    entrar(http, api[2])
    assinar(http, "cartao", cartao=CARTAO)
    antiga = (date.today() - timedelta(days=8)).isoformat()
    banco.executar("UPDATE assinaturas SET primeira_paga_em = ? WHERE usuario_id = 'u1'", antiga)
    r = http.post("/billing/assinatura/reembolso")
    assert r.status_code == 400 and r.json()["detail"]["codigo"] == "fora_do_prazo"


def test_asaas_fora_do_ar_vira_502_com_mensagem(api, tmp_path):
    http, *_ = api
    entrar(http, api[2])
    from app.asaas.client import AsaasClient

    http.app.state.asaas = AsaasClient("http://127.0.0.1:1/v3", CHAVE)  # porta sem ninguém ouvindo
    r = assinar(http, "pix")
    assert r.status_code == 502 and r.json()["detail"]["codigo"] == "asaas_indisponivel"


def test_reembolso_sem_pagamento(api):
    http, *_ = api
    entrar(http, api[2])
    assinar(http, "pix")
    r = http.post("/billing/assinatura/reembolso")
    assert r.status_code == 400 and r.json()["detail"]["codigo"] == "nada_pago"


def test_rotas_do_assinante_exigem_sessao(api):
    http, *_ = api
    assert http.get("/billing/assinatura").status_code == 401
    assert assinar(http, "pix").status_code == 401
    assert http.delete("/billing/assinatura").status_code == 401
    assert http.post("/billing/assinatura/reembolso").status_code == 401


def test_cada_um_ve_so_a_propria_assinatura(api):
    http, _, banco = api
    entrar(http, banco, "u1", "um@exemplo.com")
    assert assinar(http, "pix").status_code == 201
    entrar(http, banco, "u2", "dois@exemplo.com")  # outra pessoa no mesmo navegador
    assert http.get("/billing/assinatura").status_code == 404
    assert http.delete("/billing/assinatura").status_code == 404
    assert banco.um("SELECT status_acesso FROM assinaturas WHERE usuario_id = 'u1'")["status_acesso"] == "pendente"


def test_assinatura_usa_o_email_da_conta(api):
    http, _, banco = api
    entrar(http, banco, "u1", "conta@exemplo.com")
    assinar(http, "pix", email="outro@exemplo.com")  # campo extra é ignorado
    assert banco.um("SELECT email FROM assinantes WHERE usuario_id = 'u1'")["email"] == "conta@exemplo.com"


def test_simular_pagamento_libera_pelo_webhook(api):
    http, store, banco = api
    entrar(http, banco)
    assinar(http, "boleto")
    r = http.post("/billing/assinatura/simular-pagamento")
    assert r.status_code == 200 and r.json()["status_acesso"] == "ativo"
    assert any(e["event"] == "PAYMENT_RECEIVED" for e in store.eventos)


def test_cancelar_depois_de_pagar_mantem_acesso_ate_o_fim_do_periodo(api):
    http, store, banco = api
    entrar(http, banco)
    dados = assinar(http, "cartao", cartao=CARTAO).json()
    r = http.delete("/billing/assinatura")
    assert r.status_code == 200
    a = r.json()
    assert a["status_acesso"] == "ativo" and a["tem_acesso"] is True
    assert a["cancelada_em"] == date.today().isoformat() and a["acesso_ate"] > date.today().isoformat()
    assert a["proxima_cobranca"] is None
    # No Asaas, a assinatura ganha data de fim e não é apagada.
    sub = store.assinaturas[dados["assinatura_id"]]
    assert sub["endDate"] and not sub["deleted"]
    assert http.delete("/billing/assinatura").status_code == 409  # não cancela duas vezes
    assert assinar(http, "pix").status_code == 409  # ainda é assinante; o caminho é reativar


def test_reativar_desfaz_o_cancelamento(api):
    http, store, banco = api
    entrar(http, banco)
    dados = assinar(http, "cartao", cartao=CARTAO).json()
    http.delete("/billing/assinatura")
    r = http.post("/billing/assinatura/reativar")
    assert r.status_code == 200 and r.json()["cancelada_em"] is None and r.json()["proxima_cobranca"]
    assert store.assinaturas[dados["assinatura_id"]]["endDate"] is None
    assert http.post("/billing/assinatura/reativar").status_code == 409


def test_acesso_acaba_no_fim_do_periodo_cancelado(api):
    from app.billing import tem_acesso

    a = {"status_acesso": "ativo", "acesso_ate": "2026-12-24"}
    assert tem_acesso(a, date(2026, 12, 24)) and not tem_acesso(a, date(2026, 12, 25))


def test_proxima_cobranca_no_mesmo_dia_do_mes():
    from app.billing import proxima_cobranca

    assert proxima_cobranca("2026-11-24", date(2026, 11, 24)) == date(2026, 12, 24)
    assert proxima_cobranca("2026-01-31", date(2026, 2, 1)) == date(2026, 2, 28)
    assert proxima_cobranca("2026-11-24", date(2027, 3, 1)) == date(2027, 3, 24)


def test_resumo_traz_final_do_cartao_e_reembolso(api):
    http, _, banco = api
    entrar(http, banco)
    assert assinar(http, "cartao", cartao=CARTAO).json()["final_cartao"] == "4444"
    r = http.post("/billing/assinatura/reembolso")
    a = http.get("/billing/assinatura").json()
    assert a["reembolso_em"] == date.today().isoformat() and a["tem_acesso"] is False


def test_pix_tem_codigo_oficial_e_qr_de_verdade(api):
    """Item 4: o copia e cola segue o BR Code (CRC16 confere) e a imagem é um QR em PNG, não um pixel."""
    import base64

    from app.asaas_sim.store import _crc16

    http, *_ = api
    entrar(http, api[2])
    r = assinar(http, "pix")
    assert r.status_code == 201, r.text
    [cob] = r.json()["cobrancas"]
    codigo = cob["pix"]["copia_e_cola"]
    assert codigo.startswith("000201") and "br.gov.bcb.pix" in codigo
    assert codigo[-4:] == _crc16(codigo[:-4])
    png = base64.b64decode(cob["pix"]["imagem_base64"])
    assert png[:8] == b"\x89PNG\r\n\x1a\n" and len(png) > 300


def test_plano_leve_para_o_header(api):
    """Item 24: o header pergunta só o plano, sem consultar o Asaas."""
    http, *_ = api
    assert http.get("/billing/plano").status_code == 401
    entrar(http, api[2])
    assert http.get("/billing/plano").json() == {"plano": None, "status_acesso": None, "tem_acesso": False}
    r = assinar(http, "pix")
    assert r.status_code == 201
    p = http.get("/billing/plano").json()
    assert p["plano"] == "prata" and p["status_acesso"] == "pendente" and p["tem_acesso"] is False
    confirmar(http, r.json()["cobrancas"][0]["id"])
    p = http.get("/billing/plano").json()
    assert p["status_acesso"] == "ativo" and p["tem_acesso"] is True


def test_upgrade_so_para_cima(api):
    """Item 33: Prata -> Ouro muda o plano e o valor; igual ou menor, e sem pagamento, recusa."""
    http, *_ = api
    entrar(http, api[2])
    r = assinar(http, "pix", plano="prata")
    assert http.put("/billing/assinatura/plano", json={"plano": "ouro"}).status_code == 409  # ainda pendente
    confirmar(http, r.json()["cobrancas"][0]["id"])
    assert http.put("/billing/assinatura/plano", json={"plano": "prata"}).status_code == 409
    assert http.put("/billing/assinatura/plano", json={"plano": "bronze"}).status_code == 409
    up = http.put("/billing/assinatura/plano", json={"plano": "ouro"})
    assert up.status_code == 200, up.text
    assert up.json()["plano"] == "ouro" and up.json()["valor"] == 119.9
    assert http.get("/billing/plano").json()["plano"] == "ouro"


def test_pedidos_simultaneos_criam_uma_assinatura_so(api, monkeypatch):
    """Regressão ARES-QA-003: quatro POST /billing/assinatura ao mesmo tempo (clique duplo, duas abas) criavam quatro
    assinaturas cobradas no Asaas. Agora um passa (201) e os outros recebem 409 em_andamento, sem tocar no Asaas."""
    import threading
    import time as _time

    from fastapi.testclient import TestClient

    from app import auth

    http, store, banco = api
    entrar(http, banco)
    # Cenário da revisão: a 1ª tentativa teve o cartão recusado (o cliente do Asaas já existe) e a pessoa clica de novo.
    assert assinar(http, "cartao", cartao={**CARTAO, "numero": "5184019740373151"}).status_code == 400
    # A reserva foi liberada mesmo com o erro do Asaas: nada fica preso.
    assert banco.um("SELECT 1 FROM operacoes_cobranca") is None

    asaas = http.app.state.asaas
    original = asaas.criar_assinatura

    def lento(**corpo):  # o Asaas real leva centenas de ms; aqui garante que os pedidos se sobreponham
        _time.sleep(0.3)
        return original(**corpo)

    monkeypatch.setattr(asaas, "criar_assinatura", lento)
    barreira, resultados = threading.Barrier(4), []

    def pedir():
        c = TestClient(http.app)
        c.cookies.set(auth.COOKIE_SESSAO, http.cookies.get(auth.COOKIE_SESSAO))
        barreira.wait()
        r = assinar(c, "cartao", cartao=CARTAO)
        resultados.append((r.status_code, r.json().get("detail", {}).get("codigo") if r.status_code != 201 else None))

    ts = [threading.Thread(target=pedir) for _ in range(4)]
    [t.start() for t in ts]
    [t.join() for t in ts]

    assert sorted(resultados, key=str) == [(201, None)] + [(409, "em_andamento")] * 3, resultados
    assert len(store.assinaturas) == 1  # uma cobrança só no Asaas
    assert len(banco.todos("SELECT * FROM assinaturas")) == 1
    assert banco.um("SELECT 1 FROM operacoes_cobranca") is None
    # Depois que o primeiro termina, um novo pedido recebe a resposta de sempre: já é assinante.
    r = assinar(http, "pix")
    assert r.status_code == 409 and r.json()["detail"]["codigo"] == "ja_assinante"


def test_reserva_esquecida_expira(api):
    """Se o processo cair no meio de uma compra, a reserva não trava a conta para sempre."""
    import time as _time

    http, _, banco = api
    entrar(http, banco)
    banco.executar("INSERT INTO operacoes_cobranca (usuario_id, iniciada) VALUES ('u1', ?)", _time.time())
    r = assinar(http, "pix")
    assert r.status_code == 409 and r.json()["detail"]["codigo"] == "em_andamento"
    banco.executar("UPDATE operacoes_cobranca SET iniciada = ?", _time.time() - 600)
    assert assinar(http, "pix").status_code == 201


def test_reembolsos_simultaneos_estornam_uma_vez_so(api, monkeypatch):
    """Regressão CAND-01 (achado ao conferir o código do pull): dois pedidos de reembolso ao mesmo tempo passavam os
    dois pela conferência e pediam o estorno duas vezes no Asaas. Agora um passa e o outro recebe 409 em_andamento."""
    import threading
    import time as _time

    from fastapi.testclient import TestClient

    from app import auth

    http, store, banco = api
    entrar(http, banco)
    assert assinar(http, "cartao", cartao=CARTAO).json()["status_acesso"] == "ativo"
    asaas = http.app.state.asaas
    estornos, original = [], asaas.estornar

    def lento(cobranca_id, **kw):
        estornos.append(cobranca_id)
        _time.sleep(0.3)
        return original(cobranca_id, **kw)

    monkeypatch.setattr(asaas, "estornar", lento)
    barreira, resultados = threading.Barrier(3), []

    def pedir():
        c = TestClient(http.app)
        c.cookies.set(auth.COOKIE_SESSAO, http.cookies.get(auth.COOKIE_SESSAO))
        barreira.wait()
        r = c.post("/billing/assinatura/reembolso")
        resultados.append(r.status_code if r.status_code == 200 else (r.status_code, r.json()["detail"]["codigo"]))

    ts = [threading.Thread(target=pedir) for _ in range(3)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert sorted(resultados, key=str) == sorted([200, (409, "em_andamento"), (409, "em_andamento")], key=str), resultados
    assert len(estornos) == 1
    r = http.post("/billing/assinatura/reembolso")  # depois, a resposta de sempre
    assert r.status_code == 409 and r.json()["detail"]["codigo"] == "ja_reembolsado"
