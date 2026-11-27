"""Camada de serviços da cobrança (preparação para suporte e admin, passo 2): as funções chamadas direto, com ator."""
from __future__ import annotations

import pytest

from app.servicos import assinaturas as servico
from app.servicos.base import Ator, ErroDeNegocio
from tests.test_billing import assinar, confirmar, entrar


def preparar(api):
    http, _, banco = api
    entrar(http, banco)
    r = assinar(http, "pix")
    confirmar(http, r.json()["cobrancas"][0]["id"])
    return http, banco, http.app.state.asaas


def test_cliente_so_age_sobre_a_propria_conta(api):
    _, banco, asaas = preparar(api)
    intruso = Ator.cliente("outra-conta")
    for acao in (servico.cancelar, servico.reativar):
        with pytest.raises(ErroDeNegocio) as e:
            acao(banco, asaas, intruso, "u1")
        assert e.value.status == 403 and e.value.codigo == "outra_conta"
    with pytest.raises(ErroDeNegocio):
        servico.trocar_plano(banco, asaas, intruso, "u1", "ouro")
    assert servico.plano_atual(banco, "u1")["plano"] == "prata"  # nada mudou


def test_equipe_usa_a_mesma_regra_sobre_a_conta_do_cliente(api):
    """A equipe passa pela mesma função (a checagem de papel fica na rota da equipe, passo 7)."""
    _, banco, asaas = preparar(api)
    equipe = Ator("equipe", "e1", papel="financeiro", motivo="pedido no chamado 1042")
    r = servico.cancelar(banco, asaas, equipe, "u1")
    assert r["cancelada_em"] and r["tem_acesso"] is True  # acesso até o fim do período pago, como pelo Portal
    with pytest.raises(ErroDeNegocio) as e:
        servico.cancelar(banco, asaas, equipe, "u1")
    assert e.value.codigo == "ja_cancelada"


def test_reserva_por_conta_vale_entre_cliente_e_equipe(api):
    _, banco, asaas = preparar(api)
    with servico.uma_operacao_por_vez(banco, "u1"):  # o cliente está no meio de uma operação
        with pytest.raises(ErroDeNegocio) as e:
            servico.trocar_forma(banco, asaas, Ator("equipe", "e1", papel="financeiro"), "u1", "boleto")
    assert e.value.status == 409 and e.value.codigo == "em_andamento"


def test_evento_do_sistema_suspende_e_nao_ressuscita_cancelado(api):
    _, banco, _ = preparar(api)
    sid = banco.um("SELECT subscription_id FROM assinaturas WHERE usuario_id = 'u1'")["subscription_id"]
    servico.aplicar_evento(banco, "PAYMENT_OVERDUE", {"subscription": sid}, {})
    assert servico.plano_atual(banco, "u1")["status_acesso"] == "suspenso"
    servico.aplicar_evento(banco, "SUBSCRIPTION_DELETED", {}, {"id": sid})
    servico.aplicar_evento(banco, "PAYMENT_RECEIVED", {"subscription": sid, "paymentDate": "2026-11-27"}, {})
    assert servico.plano_atual(banco, "u1")["status_acesso"] == "cancelado"


def test_erro_de_negocio_chega_ao_cliente_no_formato_de_antes(api):
    http, _, _ = preparar(api)
    r = http.put("/billing/assinatura/plano", json={"plano": "bronze"})
    assert r.status_code == 409
    assert r.json() == {"detail": {"codigo": "nao_e_upgrade", "mensagem": "Por aqui só dá para subir de plano. Para um plano menor, fale com a equipe."}}
