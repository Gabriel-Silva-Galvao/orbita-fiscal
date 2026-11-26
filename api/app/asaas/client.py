"""Cliente do Asaas (API v3).

Fala do mesmo jeito com a simulação local, com o sandbox e com a produção do Asaas:
só mudam ASAAS_BASE_URL e ASAAS_API_KEY. Erros do Asaas viram AsaasError com os códigos originais.
"""
from __future__ import annotations

from typing import Any

import httpx

USER_AGENT = "Orbita/0.1"


class AsaasError(Exception):
    def __init__(self, status: int, erros: list[dict[str, str]]):
        self.status = status
        self.erros = erros
        self.codigo = erros[0]["code"] if erros else "unknown"
        self.descricao = erros[0]["description"] if erros else "Erro desconhecido no Asaas."
        super().__init__(f"{status} {self.codigo}: {self.descricao}")


class AsaasClient:
    def __init__(self, base_url: str, api_key: str, http: httpx.Client | None = None):
        self.base_url = base_url.rstrip("/")
        self.headers = {"access_token": api_key, "User-Agent": USER_AGENT, "Content-Type": "application/json"}
        self.http = http or httpx.Client(timeout=20)

    def _req(self, metodo: str, caminho: str, json: dict | None = None, params: dict | None = None) -> Any:
        try:
            r = self.http.request(metodo, f"{self.base_url}{caminho}", json=json, params=params, headers=self.headers)
        except httpx.HTTPError as e:
            # Asaas fora do ar ou endereço errado: vira um erro claro em vez de um 500 genérico.
            raise AsaasError(503, [{"code": "asaas_indisponivel", "description": f"Não foi possível falar com o Asaas agora ({type(e).__name__}). Tente de novo em instantes."}])
        if r.status_code >= 400:
            try:
                erros = r.json().get("errors") or []
            except ValueError:
                erros = []
            if not erros:
                erros = [{"code": f"http_{r.status_code}", "description": r.text[:200] or "Sem detalhes."}]
            raise AsaasError(r.status_code, erros)
        return r.json()

    # Clientes
    def criar_cliente(self, **dados: Any) -> dict:
        return self._req("POST", "/customers", dados)

    def atualizar_cliente(self, cid: str, **dados: Any) -> dict:
        return self._req("PUT", f"/customers/{cid}", dados)

    # Assinaturas
    def criar_assinatura(self, **dados: Any) -> dict:
        return self._req("POST", "/subscriptions", dados)

    def obter_assinatura(self, sid: str) -> dict:
        return self._req("GET", f"/subscriptions/{sid}")

    def atualizar_assinatura(self, sid: str, **dados: Any) -> dict:
        return self._req("PUT", f"/subscriptions/{sid}", dados)

    def cancelar_assinatura(self, sid: str) -> dict:
        return self._req("DELETE", f"/subscriptions/{sid}")

    def cobrancas_da_assinatura(self, sid: str, offset: int = 0, limit: int = 100) -> list[dict]:
        return self._req("GET", f"/subscriptions/{sid}/payments", params={"offset": offset, "limit": limit})["data"]

    # Cobranças
    def obter_cobranca(self, pid: str) -> dict:
        return self._req("GET", f"/payments/{pid}")

    def pix_qrcode(self, pid: str) -> dict:
        return self._req("GET", f"/payments/{pid}/pixQrCode")

    def linha_digitavel(self, pid: str) -> dict:
        return self._req("GET", f"/payments/{pid}/identificationField")

    def estornar(self, pid: str, valor: float | None = None, descricao: str | None = None) -> dict:
        corpo = {k: v for k, v in {"value": valor, "description": descricao}.items() if v is not None}
        return self._req("POST", f"/payments/{pid}/refund", corpo)

    def confirmar_no_sandbox(self, pid: str) -> dict:
        """Só existe no sandbox (e na simulação): dá um Pix ou boleto como pago."""
        return self._req("POST", f"/sandbox/payment/{pid}/confirm")

    # Webhooks
    def cadastrar_webhook(self, **dados: Any) -> dict:
        return self._req("POST", "/webhooks", dados)
