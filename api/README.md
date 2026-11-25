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
| `POST /billing/assinatura` | Cria o cliente no Asaas (se ainda não existir) e a assinatura mensal da conta logada. Corpo: `nome` e `cpf_cnpj` da nota, `plano` (`pro` ou `max`), `forma` (`cartao`, `pix` ou `boleto`) e `cartao` (só no cartão: `titular`, `numero`, `mes`, `ano`, `cvv`). E-mail e IP vêm da sessão e da conexão. Responde 201 com o resumo, 409 se já houver assinatura, 400 com a mensagem do Asaas se o cartão for recusado. |
| `GET /billing/assinatura` | Resumo: plano, valor, forma, `status_acesso` e cobranças. No Pix vem o copia e cola e a imagem do QR; no boleto, a linha digitável, o código de barras e o PDF. |
| `PUT /billing/assinatura/forma` | Troca para `pix` ou `boleto` (as cobranças pendentes também mudam). O cartão espera a decisão entre a página segura do Asaas e o formulário próprio. |
| `DELETE /billing/assinatura` | Cancela a assinatura. Depois disso, a pessoa pode assinar de novo. |
| `POST /billing/assinatura/reembolso` | Estorna tudo o que foi pago e encerra, só até 7 dias do primeiro pagamento (CDC, art. 49). Fora do prazo: 400 `fora_do_prazo`. |
| `POST /billing/assinatura/simular-pagamento` | Só com a simulação ligada: confirma as cobranças pendentes de Pix ou boleto, como o banco faria. A liberação segue pelo webhook. |

Desde a etapa 7c, todas essas rotas usam a sessão (cookie `orbita_sessao`): sem sessão, 401; cada pessoa só vê e altera a própria assinatura.
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

## Conta e login (etapa 7a)

E-mail e senha, sempre com código de 6 dígitos por e-mail. A conta só nasce depois do código confirmado.

| Rota | Resposta |
| --- | --- |
| `POST /auth/cadastro` `{nome, email, senha, plano?}` | 202 código enviado, 409 e-mail já tem conta, 422 dados inválidos ou senha com menos de 8 caracteres |
| `POST /auth/login` `{email, senha}` | 202 código enviado, 401 não confere, 429 depois de 10 erros em 15 minutos |
| `POST /auth/codigo` `{codigo}` | 200 sessão criada (cookie `orbita_sessao`, 30 dias), 400 `{tentativas_restantes}`, 410 expirado (10 minutos), 429 sem tentativas (5) |
| `POST /auth/codigo/reenviar` | 202, 429 `{espere_segundos}` antes de 60 s, 410 sem código pendente |
| `POST /auth/senha/esqueci` `{email}` | 202 sempre, para não revelar se a conta existe |
| `GET /auth/sessao` | 200 `{id, email, nome}` ou 401. É a rota que o middleware do site consulta |
| `POST /auth/sair` | 204, e a sessão é apagada no servidor |

- Senha guardada com scrypt; código e tokens só como SHA-256; cookies HttpOnly e SameSite=Lax (`COOKIE_SECURE=true` em produção).
- CORS liberado só para `SITE_URL`, com cookies.
- Ainda não há provedor de e-mail: o código vai para o log da API. Em desenvolvimento, `AUTH_CODIGO_NA_RESPOSTA=true` também devolve o código em `codigo_dev`. Em produção, deixe `false`.
- Ainda não feito: login pelo Google e o link de troca de senha.
