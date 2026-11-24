# API da Órbita

Backend em Python com FastAPI (decisão de 24/11/2026). Fica nesta pasta enquanto o projeto não vai ao ar; na publicação, vai para o servidor.

**Etapas prontas:**
- **Etapa 3:** simulação do Asaas e o cliente que fala com ela.
- **Etapa 4:** rotas de cobrança da Órbita (`/billing`) e o webhook que libera e corta o acesso (`/webhooks/asaas`).

O site ainda não chama essas rotas; ligar o Checkout e o Portal à API é uma etapa futura.

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

## Rotas da Órbita (para o site)

Hoje o usuário vem no corpo da requisição; quando houver login, virá da sessão.

| Rota | O que faz |
| --- | --- |
| `POST /billing/assinaturas` | Cria o cliente no Asaas (se ainda não existir) e a assinatura mensal. Corpo: `usuario_id`, `nome`, `email`, `cpf_cnpj`, `plano` (`pro` ou `max`), `forma` (`cartao`, `pix` ou `boleto`), `cartao` (só no cartão: `titular`, `numero`, `mes`, `ano`, `cvv`) e `ip`. Responde 201 com o resumo, 409 se já houver assinatura, 400 com a mensagem do Asaas se o cartão for recusado. |
| `GET /billing/assinaturas/{usuario_id}` | Resumo: plano, valor, forma, `status_acesso` e cobranças. No Pix vem o copia e cola e a imagem do QR; no boleto, a linha digitável, o código de barras e o PDF. |
| `PUT /billing/assinaturas/{usuario_id}/forma` | Troca para `pix` ou `boleto` (as cobranças pendentes também mudam). O cartão espera a decisão entre a página segura do Asaas e o formulário próprio. |
| `DELETE /billing/assinaturas/{usuario_id}` | Cancela a assinatura. Depois disso, a pessoa pode assinar de novo. |
| `POST /billing/assinaturas/{usuario_id}/reembolso` | Estorna tudo o que foi pago e encerra, só até 7 dias do primeiro pagamento (CDC, art. 49). Fora do prazo: 400 `fora_do_prazo`. |
| `POST /webhooks/asaas` | Recebe os eventos do Asaas. Exige o cabeçalho `asaas-access-token`; cada evento é processado uma vez só (o repetido responde 200 com `duplicado: true`). |

**Status do acesso** (`status_acesso`):
- `pendente`: assinatura criada, pagamento ainda não confirmado. O plugin não funciona.
- `ativo`: liberado por `PAYMENT_CONFIRMED` (cartão) ou `PAYMENT_RECEIVED` (Pix e boleto). Nunca por `PAYMENT_CREATED`.
- `suspenso`: `PAYMENT_OVERDUE`, `PAYMENT_CHARGEBACK_REQUESTED` ou `PAYMENT_REPROVED_BY_RISK_ANALYSIS`.
- `reembolsado` e `cancelado`: finais; eventos atrasados não reabrem o acesso.

Erros saem como `{"detail": {"codigo", "mensagem"}}`. Asaas fora do ar vira 502 `asaas_indisponivel`.

**Variáveis** (ver `.env.example`): `ASAAS_BASE_URL`, `ASAAS_API_KEY`, `ASAAS_SIM_ENABLED`, `ASAAS_WEBHOOK_TOKEN`, `API_PUBLIC_URL` (endereço desta API, para cadastrar o webhook) e `DATABASE_PATH` (SQLite).

**Com o Asaas real:** cadastre o webhook no painel do Asaas (Integrações > Webhooks) apontando para `{API_PUBLIC_URL}/webhooks/asaas`, com o mesmo token de `ASAAS_WEBHOOK_TOKEN` e os eventos listados em `app/main.py`. Na simulação, ele já nasce cadastrado.

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
