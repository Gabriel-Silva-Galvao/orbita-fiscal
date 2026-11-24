# API da Órbita

Backend em Python com FastAPI (decisão de 24/11/2026). Fica nesta pasta enquanto o projeto não vai ao ar; na publicação, vai para o servidor.

**Etapa atual (3):** só a **simulação do Asaas** e o **cliente** que fala com ela. As rotas de cobrança da Órbita e o webhook de liberação do acesso são a etapa 4.

## Por que uma simulação

A empresa ainda não tem CNPJ, então a integração real com o Asaas está suspensa. A simulação imita a API v3 do Asaas (caminhos, campos, status, erros e webhooks, conforme https://docs.asaas.com). Para trocar pela real depois, só mudam `ASAAS_BASE_URL` e `ASAAS_API_KEY`.

## Instalar e rodar

```powershell
cd api
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

- Saúde: http://localhost:8000/saude
- Documentação interativa: http://localhost:8000/docs
- Simulação: http://localhost:8000/asaas-sim/v3/... (cabeçalho `access_token` obrigatório, com a chave do `.env.example`)

## Testes

```powershell
cd api
.venv\Scripts\python.exe -m pytest
```

Os testes usam o próprio cliente (`app/asaas/client.py`) contra a simulação: autenticação, cliente, assinatura no Pix, no boleto e no cartão (aprovado e recusado), confirmação, estorno total e parcial, troca de forma de pagamento, cancelamento, vencimento e entrega de webhooks (com token e pausa depois de 15 falhas).

## O que a simulação cobre

| Asaas | Rota |
| --- | --- |
| Clientes | `POST /v3/customers`, `GET /v3/customers/{id}` |
| Assinaturas | `POST /v3/subscriptions`, `GET`, `PUT` e `DELETE /v3/subscriptions/{id}`, `GET /v3/subscriptions/{id}/payments` |
| Cobranças | `GET /v3/payments/{id}`, `GET /v3/payments/{id}/pixQrCode`, `GET /v3/payments/{id}/identificationField`, `POST /v3/payments/{id}/refund` |
| Só sandbox | `POST /v3/sandbox/payment/{id}/confirm` (dá Pix ou boleto como pago) |
| Webhooks | `POST` e `GET /v3/webhooks`; entrega com o cabeçalho `asaas-access-token` |
| Extensões da simulação | `POST /v3/sandbox/payment/{id}/overdue` (força vencimento) e `GET /asaas-sim/_eventos` (eventos gerados e entregas) |

Regras imitadas:
- **Cartão aprovado** (qualquer número, por exemplo `4444 4444 4444 4444`): a cobrança nasce `CONFIRMED` e sai o evento `PAYMENT_CONFIRMED`.
- **Cartão recusado** (`5184019740373151` ou `4916561358240741`): erro 400 `invalid_creditCard`, e nada fica gravado.
- **Pix e boleto:** a cobrança nasce `PENDING` e só vira `RECEIVED` (evento `PAYMENT_RECEIVED`) na confirmação.
- **Webhooks:** só a resposta HTTP 200 conta como entregue; depois de 15 falhas seguidas, a fila pausa.

Limitação: o estado fica em memória e some quando a API reinicia. O QR Code do Pix é uma imagem fixa, sem leitura real.
