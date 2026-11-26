"""Estado e regras da simulação do Asaas, em memória (some quando a API reinicia).

Cada função devolve o objeto no formato do Asaas ou levanta SimError com o código de erro do Asaas.
Os eventos gerados vão para `eventos` e são entregues aos webhooks cadastrados por `entregar`.
"""
from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Callable

import httpx

BILLING_TYPES = {"CREDIT_CARD", "PIX", "BOLETO", "UNDEFINED"}
CYCLES = {"WEEKLY", "BIWEEKLY", "MONTHLY", "BIMONTHLY", "QUARTERLY", "SEMIANNUALLY", "YEARLY"}
# Cartões de teste do sandbox do Asaas que são recusados. Qualquer outro número é aprovado.
CARTOES_RECUSADOS = {"5184019740373151", "4916561358240741"}
MSG_CARTAO_RECUSADO = "Transação não autorizada. Verifique os dados do cartão de crédito e tente novamente."
FALHAS_PARA_PAUSAR = 15


class SimError(Exception):
    def __init__(self, status: int, code: str, description: str):
        super().__init__(description)
        self.status, self.code, self.description = status, code, description


def _id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(6)}"


def _hoje() -> str:
    return date.today().isoformat()


def _agora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _data(valor: Any, campo: str) -> str:
    try:
        return date.fromisoformat(str(valor)).isoformat()
    except ValueError:
        raise SimError(400, f"invalid_{campo}", f"O campo {campo} deve estar no formato AAAA-MM-DD.")


def _obrigatorio(corpo: dict, *campos: str) -> None:
    for c in campos:
        if corpo.get(c) in (None, ""):
            raise SimError(400, f"invalid_{c}", f"O campo {c} deve ser informado.")


def _modulo10(numero: str) -> int:
    soma, peso = 0, 2
    for d in reversed(numero):
        p = int(d) * peso
        soma += p // 10 + p % 10
        peso = 1 if peso == 2 else 2
    return (10 - soma % 10) % 10


Enviar = Callable[[str, dict, dict], int]


def enviar_http(url: str, corpo: dict, headers: dict) -> int:
    """Entrega real por HTTP. Só 200 conta como sucesso, como no Asaas."""
    try:
        return httpx.post(url, json=corpo, headers=headers, timeout=10).status_code
    except httpx.HTTPError:
        return 0


@dataclass
class Store:
    clientes: dict[str, dict] = field(default_factory=dict)
    assinaturas: dict[str, dict] = field(default_factory=dict)
    cobrancas: dict[str, dict] = field(default_factory=dict)
    webhooks: dict[str, dict] = field(default_factory=dict)
    eventos: list[dict] = field(default_factory=list)
    entregas: list[dict] = field(default_factory=list)
    enviar: Enviar = enviar_http
    base_publica: str = "http://localhost:8000/asaas-sim"
    trava: threading.RLock = field(default_factory=threading.RLock)

    # ---------- Eventos e webhooks ----------
    def _evento(self, nome: str, **dados: Any) -> None:
        evento = {"id": _id("evt"), "event": nome, "dateCreated": _agora(), "account": {"id": "acc_simulacao", "ownerId": None}, **dados}
        self.eventos.append(evento)
        self.entregar(evento)

    def entregar(self, evento: dict) -> None:
        for wh in self.webhooks.values():
            if not wh["enabled"] or wh["interrupted"] or evento["event"] not in wh["events"]:
                continue
            headers = {"asaas-access-token": wh["authToken"]}
            status = self.enviar(wh["url"], evento, headers)
            self.entregas.append({"webhook": wh["id"], "evento": evento["id"], "status": status})
            if status == 200:
                wh["_falhas"] = 0
            else:
                wh["_falhas"] = wh.get("_falhas", 0) + 1
                if wh["_falhas"] >= FALHAS_PARA_PAUSAR:
                    wh["interrupted"] = True

    def cadastrar_webhook(self, corpo: dict) -> dict:
        _obrigatorio(corpo, "name", "url", "email", "sendType")
        if not isinstance(corpo.get("events"), list) or not corpo["events"]:
            raise SimError(400, "invalid_events", "Informe ao menos um evento.")
        if len(self.webhooks) >= 10:
            raise SimError(400, "invalid_webhook", "Limite de 10 webhooks por conta atingido.")
        token = corpo.get("authToken") or secrets.token_urlsafe(32)
        if not 32 <= len(token) <= 255:
            raise SimError(400, "invalid_authToken", "O authToken deve ter entre 32 e 255 caracteres.")
        wh = {
            "object": "webhook",
            "id": _id("wh"),
            "name": corpo["name"],
            "url": corpo["url"],
            "email": corpo["email"],
            "enabled": bool(corpo.get("enabled", True)),
            "interrupted": bool(corpo.get("interrupted", False)),
            "apiVersion": 3,
            "sendType": corpo["sendType"],
            "events": list(corpo["events"]),
            "authToken": token,
        }
        self.webhooks[wh["id"]] = wh
        return {k: v for k, v in wh.items() if not k.startswith("_")}

    # ---------- Clientes ----------
    def criar_cliente(self, corpo: dict) -> dict:
        _obrigatorio(corpo, "name", "cpfCnpj")
        doc = "".join(ch for ch in str(corpo["cpfCnpj"]) if ch.isdigit())
        if len(doc) not in (11, 14):
            raise SimError(400, "invalid_cpfCnpj", "O CPF ou CNPJ informado é inválido.")
        cli = {
            "object": "customer",
            "id": _id("cus"),
            "dateCreated": _hoje(),
            "name": corpo["name"],
            "email": corpo.get("email"),
            "mobilePhone": corpo.get("mobilePhone"),
            "cpfCnpj": doc,
            "personType": "FISICA" if len(doc) == 11 else "JURIDICA",
            "externalReference": corpo.get("externalReference"),
            "notificationDisabled": bool(corpo.get("notificationDisabled", False)),
            "deleted": False,
        }
        self.clientes[cli["id"]] = cli
        return cli

    def atualizar_cliente(self, cid: str, corpo: dict) -> dict:
        cli = self.cliente(cid)
        if "cpfCnpj" in corpo:
            doc = "".join(ch for ch in str(corpo["cpfCnpj"]) if ch.isdigit())
            if len(doc) not in (11, 14):
                raise SimError(400, "invalid_cpfCnpj", "O CPF ou CNPJ informado é inválido.")
            cli["cpfCnpj"] = doc
            cli["personType"] = "FISICA" if len(doc) == 11 else "JURIDICA"
        for campo in ("name", "email", "address", "addressNumber", "postalCode", "mobilePhone"):
            if campo in corpo:
                cli[campo] = corpo[campo]
        return cli

    def cliente(self, cid: str) -> dict:
        cli = self.clientes.get(cid)
        if not cli:
            raise SimError(400, "invalid_customer", "Cliente inexistente ou removido.")
        return cli

    # ---------- Cobranças ----------
    def _nova_cobranca(self, cliente: str, billing: str, valor: float, vencimento: str, descricao: str | None, assinatura: str | None, ref: str | None) -> dict:
        pid = _id("pay")
        cob = {
            "object": "payment",
            "id": pid,
            "dateCreated": _hoje(),
            "customer": cliente,
            "subscription": assinatura,
            "installment": None,
            "paymentLink": None,
            "value": round(valor, 2),
            "netValue": round(valor, 2),
            "originalValue": None,
            "interestValue": None,
            "description": descricao,
            "billingType": billing,
            "creditCard": None,
            "canBePaidAfterDueDate": True,
            "pixTransaction": None,
            "status": "PENDING",
            "dueDate": vencimento,
            "originalDueDate": vencimento,
            "paymentDate": None,
            "clientPaymentDate": None,
            "invoiceUrl": f"{self.base_publica}/fatura/{pid}",
            "invoiceNumber": str(len(self.cobrancas) + 1).zfill(8),
            "externalReference": ref,
            "deleted": False,
            "anticipated": False,
            "anticipable": False,
            "bankSlipUrl": f"{self.base_publica}/boleto/{pid}.pdf" if billing == "BOLETO" else None,
            "transactionReceiptUrl": None,
            "nossoNumero": str(10_000_000 + len(self.cobrancas)) if billing == "BOLETO" else None,
            "refunds": None,
        }
        self.cobrancas[pid] = cob
        self._evento("PAYMENT_CREATED", payment=dict(cob))
        return cob

    def cobranca(self, pid: str) -> dict:
        cob = self.cobrancas.get(pid)
        if not cob or cob["deleted"]:
            raise SimError(404, "not_found", "Cobrança não encontrada.")
        return cob

    @staticmethod
    def _validar_cartao(corpo: dict) -> str:
        """Confere os dados do cartão antes de gravar qualquer coisa. Devolve só os dígitos."""
        cartao = corpo.get("creditCard") or {}
        numero = "".join(ch for ch in str(cartao.get("number", "")) if ch.isdigit())
        if not corpo.get("creditCardToken"):
            if not numero:
                raise SimError(400, "invalid_creditCard", "Informe os dados do cartão de crédito ou o creditCardToken.")
            if not corpo.get("creditCardHolderInfo"):
                raise SimError(400, "invalid_creditCardHolderInfo", "Informe os dados do titular do cartão.")
            if not corpo.get("remoteIp"):
                raise SimError(400, "invalid_remoteIp", "Informe o IP de onde o cliente está fazendo a compra.")
        if numero in CARTOES_RECUSADOS:
            raise SimError(400, "invalid_creditCard", MSG_CARTAO_RECUSADO)
        return numero

    def _cobrar_cartao(self, cob: dict, corpo: dict, numero: str) -> None:
        token = corpo.get("creditCardToken")
        final = numero[-4:] if numero else "0000"
        cob["creditCard"] = {
            "creditCardNumber": final,
            "creditCardBrand": "MASTERCARD" if numero.startswith("5") else "VISA",
            "creditCardToken": token or f"tok_{secrets.token_hex(8)}",
        }
        cob["status"] = "CONFIRMED"
        cob["paymentDate"] = cob["clientPaymentDate"] = _hoje()
        cob["transactionReceiptUrl"] = f"{self.base_publica}/comprovante/{cob['id']}"
        self._evento("PAYMENT_CONFIRMED", payment=dict(cob))

    def pix_qrcode(self, pid: str) -> dict:
        cob = self.cobranca(pid)
        if cob["billingType"] not in ("PIX", "UNDEFINED"):
            raise SimError(400, "invalid_billingType", "Esta cobrança não é Pix.")
        # Item 4 da rodada de testes: código no formato oficial do Pix (BR Code/EMV, com CRC16) e QR de verdade,
        # como o Asaas devolve. A chave é de simulação: um app de banco lê o código, mas não acha o recebedor.
        payload = br_code(chave=f"simulacao-orbita-{pid}"[:77], valor=cob["value"], nome="ORBITA SIMULACAO", cidade="SAO PAULO", txid=pid)
        return {"encodedImage": qr_png_base64(payload), "payload": payload, "expirationDate": f"{cob['dueDate']} 23:59:59"}

    def linha_digitavel(self, pid: str) -> dict:
        cob = self.cobranca(pid)
        if cob["billingType"] != "BOLETO":
            raise SimError(400, "invalid_billingType", "Esta cobrança não é boleto.")
        base = f"{len(self.cobrancas):09d}{int(cob['value'] * 100):010d}"
        campo1 = "001900000"
        campo2 = base[:10].rjust(10, "0")
        campo3 = base[-10:].rjust(10, "0")
        linha = (
            campo1 + str(_modulo10(campo1))
            + campo2 + str(_modulo10(campo2))
            + campo3 + str(_modulo10(campo3))
            + "1"
            + "0000" + f"{int(cob['value'] * 100):010d}"
        )
        barras = "0019" + "1" + "0000" + f"{int(cob['value'] * 100):010d}" + campo1[4:] + campo2 + campo3
        return {"identificationField": linha[:47].ljust(47, "0"), "nossoNumero": cob["nossoNumero"], "barCode": barras[:44].ljust(44, "0")}

    def confirmar_no_sandbox(self, pid: str) -> dict:
        cob = self.cobranca(pid)
        if cob["billingType"] not in ("PIX", "BOLETO", "UNDEFINED"):
            raise SimError(400, "invalid_action", "Só cobranças Pix ou boleto podem ser confirmadas manualmente.")
        if cob["status"] not in ("PENDING", "OVERDUE"):
            raise SimError(400, "invalid_action", "Esta cobrança não está aguardando pagamento.")
        cob["status"] = "RECEIVED"
        cob["paymentDate"] = cob["clientPaymentDate"] = _hoje()
        self._evento("PAYMENT_RECEIVED", payment=dict(cob))
        return cob

    def forcar_vencimento(self, pid: str) -> dict:
        cob = self.cobranca(pid)
        if cob["status"] != "PENDING":
            raise SimError(400, "invalid_action", "Só cobranças pendentes podem vencer.")
        cob["status"] = "OVERDUE"
        self._evento("PAYMENT_OVERDUE", payment=dict(cob))
        return cob

    def estornar(self, pid: str, corpo: dict) -> dict:
        cob = self.cobranca(pid)
        if cob["status"] not in ("CONFIRMED", "RECEIVED"):
            raise SimError(400, "invalid_action", "Só é possível estornar cobranças pagas.")
        ja = sum(r["value"] for r in cob["refunds"] or [])
        resta = round(cob["value"] - ja, 2)
        valor = round(float(corpo.get("value") or resta), 2)
        if valor <= 0 or valor > resta:
            raise SimError(400, "invalid_value", f"O valor do estorno deve ser maior que zero e no máximo R$ {resta:.2f}.")
        estorno = {"dateCreated": _agora(), "status": "DONE", "value": valor, "description": corpo.get("description"), "transactionReceiptUrl": None}
        cob["refunds"] = (cob["refunds"] or []) + [estorno]
        if round(ja + valor, 2) >= cob["value"]:
            cob["status"] = "REFUNDED"
            self._evento("PAYMENT_REFUNDED", payment=dict(cob))
        else:
            self._evento("PAYMENT_PARTIALLY_REFUNDED", payment=dict(cob))
        return cob

    # ---------- Assinaturas ----------
    def criar_assinatura(self, corpo: dict) -> dict:
        _obrigatorio(corpo, "customer", "billingType", "value", "nextDueDate", "cycle")
        self.cliente(corpo["customer"])
        if corpo["billingType"] not in BILLING_TYPES:
            raise SimError(400, "invalid_billingType", "Forma de pagamento inválida.")
        if corpo["cycle"] not in CYCLES:
            raise SimError(400, "invalid_cycle", "Periodicidade inválida.")
        valor = float(corpo["value"])
        if valor <= 0:
            raise SimError(400, "invalid_value", "O valor deve ser maior que zero.")
        vencimento = _data(corpo["nextDueDate"], "nextDueDate")

        # No cartão, os dados são conferidos antes de salvar: recusado, nada fica gravado.
        numero = self._validar_cartao(corpo) if corpo["billingType"] == "CREDIT_CARD" else ""

        sid = _id("sub")
        sub = {
            "object": "subscription",
            "id": sid,
            "dateCreated": _hoje(),
            "customer": corpo["customer"],
            "paymentLink": None,
            "billingType": corpo["billingType"],
            "cycle": corpo["cycle"],
            "value": round(valor, 2),
            "nextDueDate": vencimento,
            "endDate": corpo.get("endDate"),
            "description": corpo.get("description"),
            "status": "ACTIVE",
            "discount": corpo.get("discount"),
            "fine": corpo.get("fine"),
            "interest": corpo.get("interest"),
            "deleted": False,
            "maxPayments": corpo.get("maxPayments"),
            "externalReference": corpo.get("externalReference"),
        }
        self.assinaturas[sid] = sub
        self._evento("SUBSCRIPTION_CREATED", subscription=dict(sub))
        cob = self._nova_cobranca(sub["customer"], sub["billingType"], valor, vencimento, sub["description"], sid, sub["externalReference"])
        if sub["billingType"] == "CREDIT_CARD":
            self._cobrar_cartao(cob, corpo, numero)
        return sub

    def assinatura(self, sid: str) -> dict:
        sub = self.assinaturas.get(sid)
        if not sub or sub["deleted"]:
            raise SimError(404, "not_found", "Assinatura não encontrada.")
        return sub

    def atualizar_assinatura(self, sid: str, corpo: dict) -> dict:
        sub = self.assinatura(sid)
        if "billingType" in corpo and corpo["billingType"] not in BILLING_TYPES:
            raise SimError(400, "invalid_billingType", "Forma de pagamento inválida.")
        if "status" in corpo and corpo["status"] not in ("ACTIVE", "INACTIVE"):
            raise SimError(400, "invalid_status", "Status inválido.")
        for campo in ("billingType", "value", "nextDueDate", "cycle", "description", "status", "endDate", "externalReference"):
            if campo in corpo:
                sub[campo] = _data(corpo[campo], campo) if campo == "nextDueDate" else corpo[campo]
        if corpo.get("updatePendingPayments"):
            for cob in self.cobrancas.values():
                if cob["subscription"] == sid and cob["status"] == "PENDING" and not cob["deleted"]:
                    cob["billingType"] = sub["billingType"]
                    cob["value"] = cob["netValue"] = round(float(sub["value"]), 2)
                    self._evento("PAYMENT_UPDATED", payment=dict(cob))
        self._evento("SUBSCRIPTION_INACTIVATED" if corpo.get("status") == "INACTIVE" else "SUBSCRIPTION_UPDATED", subscription=dict(sub))
        return sub

    def cancelar_assinatura(self, sid: str) -> dict:
        sub = self.assinatura(sid)
        for cob in self.cobrancas.values():
            if cob["subscription"] == sid and cob["status"] in ("PENDING", "OVERDUE") and not cob["deleted"]:
                cob["deleted"] = True
                self._evento("PAYMENT_DELETED", payment=dict(cob))
        sub["deleted"] = True
        sub["status"] = "INACTIVE"
        self._evento("SUBSCRIPTION_DELETED", subscription=dict(sub))
        return {"deleted": True, "id": sid}

    def cobrancas_da_assinatura(self, sid: str) -> list[dict]:
        self.assinatura(sid)
        return [c for c in self.cobrancas.values() if c["subscription"] == sid and not c["deleted"]]


def _campo(id_: str, valor: str) -> str:
    return f"{id_}{len(valor):02d}{valor}"


def _crc16(dados: str) -> str:
    """CRC16-CCITT (polinômio 0x1021, início 0xFFFF), exigido no fim do BR Code do Pix."""
    crc = 0xFFFF
    for byte in dados.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return f"{crc:04X}"


def br_code(chave: str, valor: float, nome: str, cidade: str, txid: str) -> str:
    """Pix copia e cola no padrão EMV do Banco Central (Manual do BR Code)."""
    conta = _campo("00", "br.gov.bcb.pix") + _campo("01", chave)
    txid = "".join(c for c in txid if c.isalnum())[:25] or "***"
    corpo = (
        _campo("00", "01")
        + _campo("26", conta)
        + _campo("52", "0000")
        + _campo("53", "986")
        + _campo("54", f"{valor:.2f}")
        + _campo("58", "BR")
        + _campo("59", nome[:25])
        + _campo("60", cidade[:15])
        + _campo("62", _campo("05", txid))
        + "6304"
    )
    return corpo + _crc16(corpo)


def qr_png_base64(texto: str) -> str:
    import base64
    import io

    import segno

    buf = io.BytesIO()
    segno.make(texto, error="m").save(buf, kind="png", scale=8, border=2)
    return base64.b64encode(buf.getvalue()).decode()
