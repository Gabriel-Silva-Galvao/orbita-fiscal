# Backend da Órbita e segurança

Documento do item 17 da rodada de testes (25/11/2026). Descreve a API inteira (`api/`) e analisa a segurança
ponto a ponto. Revisado a partir do código no commit `710141f`; 66 testes automatizados passando.

Legenda de risco: **Crítico** (impede publicar), **Alto** (resolver antes de ter clientes), **Médio**
(resolver no primeiro ciclo depois de publicar), **Baixo** (melhoria).

---

## 1. Visão geral

| Peça | O que é |
|---|---|
| Site | Astro 7 com servidor Node (`src/`). Páginas públicas geradas no build; Entrar, Checkout, Portal e Instalar rodam no servidor. |
| API | Python 3.11 + FastAPI (`api/app/`). Toda regra de negócio fica aqui. |
| Banco | SQLite (`api/orbita.db`, ou `orbita-dev.db` no desenvolvimento), um arquivo, sem servidor. |
| Pagamentos | Asaas (API v3). Hoje, uma **simulação** local fiel (`app/asaas_sim/`), até haver CNPJ. |
| E-mail | SMTP do provedor (`app/correio.py`); sem SMTP configurado, o código vai para o log. |
| Plugin | Servidor MCP da Órbita (já existe, ligado depois). Hoje o download entrega um zip de demonstração. |

Fluxo: o navegador chama a API direto (`fetch` com cookie, CORS liberado só para o site). O servidor do site
pergunta à API se a sessão vale antes de abrir rotas protegidas (`src/middleware.ts`).

```
Navegador ──(cookie orbita_sessao)──> API FastAPI ──> SQLite
    │                                     └──────> Asaas (simulação hoje) ──webhook──> /webhooks/asaas
    └──> Site Astro (Node) ──(repasse do cookie)──> GET /auth/sessao
```

## 2. Arquivos

| Arquivo | Responsabilidade |
|---|---|
| `app/main.py` | Monta a aplicação: banco, migrações, CORS, rotas, webhook da simulação. |
| `app/config.py` | Configuração lida do ambiente / `api/.env` (pydantic-settings). |
| `app/db.py` | Classe `Banco` (SQLite com trava), tabelas de cobrança. |
| `app/auth.py` | Conta, login, código de 6 dígitos (2FA), sessões e aparelhos. |
| `app/correio.py` | Envio do código por SMTP. |
| `app/billing.py` | Assinatura, forma de pagamento, cancelamento, reembolso, webhook do Asaas. |
| `app/plugin.py` | Link de download do plugin (15 min) e zip de demonstração. |
| `app/asaas/client.py` | Cliente HTTP do Asaas (igual para simulação, sandbox e produção). |
| `app/asaas_sim/` | Simulação do Asaas: clientes, assinaturas, cobranças, Pix (BR Code + QR), boleto, webhooks. |
| `tests/` | 66 testes (pytest): login, sessões, cobrança, webhook, simulação, Pix, download. |

## 3. Banco de dados

| Tabela | Campos principais | Observação |
|---|---|---|
| `usuarios` | id (UUID), email (único), nome, senha_hash, criado_em | Senha com scrypt (n=2^14, r=8, p=1, sal de 16 bytes). |
| `desafios` | token_hash, finalidade, email, nome, senha_hash, codigo_hash, expira, tentativas, enviado_em | Código de 6 dígitos pendente. Conta só nasce depois do código. |
| `sessoes` | token_hash, usuario_id, expira, id, criada, ultimo_uso, aparelho, manter | Token só como SHA-256. |
| `assinantes` | usuario_id, email, nome, cpf_cnpj, customer_id | Dados da nota fiscal. **CPF/CNPJ em texto puro.** |
| `assinaturas` | usuario_id, subscription_id, plano, forma, status_acesso, datas, final_cartao | Só os 4 últimos dígitos do cartão. |
| `eventos_webhook` | id, evento, recebido_em | Idempotência do webhook. |
| `downloads` | token_hash, usuario_id, expira, criado | Links do plugin. |

Migrações: colunas novas são acrescentadas na inicialização (`ALTER TABLE ... ADD COLUMN`), sem apagar dados.

## 4. Rotas

Todas as rotas do assinante identificam a pessoa **pela sessão**, nunca por id no endereço ou no corpo.

### Conta e login (`/auth`)

| Método e rota | Entrada | Respostas |
|---|---|---|
| POST `/auth/cadastro` | nome, email, senha (≥ 8), plano? | 202 código enviado · 409 e-mail em uso · 422 |
| POST `/auth/login` | email, senha | 202 código enviado · 401 não confere · 429 (10 falhas em 15 min por e-mail) |
| POST `/auth/codigo` | codigo, manter? | 200 sessão criada · 400 errado (5 tentativas) · 410 expirado (10 min) · 429 |
| POST `/auth/codigo/reenviar` | — | 202 · 429 espere 60 s · 410 |
| POST `/auth/senha/esqueci` | email | 202 sempre (link de senha nova ainda não existe) |
| GET `/auth/sessao` | cookie | 200 {id, email, nome} · 401 |
| GET `/auth/sessoes` | cookie | aparelhos conectados, marcando o atual |
| DELETE `/auth/sessoes/{id}` | cookie | 204 · 404 (só acha sessões da própria conta) |
| POST `/auth/sair-de-todos` | cookie | 204 |
| PUT `/auth/conta` | nome | 200 · 422 |
| DELETE `/auth/conta` | cookie | 204 · 409 assinatura ativa |
| POST `/auth/sair` | cookie | 204 |

Sessão: 30 dias com "manter conectado" (cookie persistente); sem ele, cookie de sessão do navegador e 12 h no
servidor. Cookies `HttpOnly`, `SameSite=Lax`, `Secure` em produção (`COOKIE_SECURE=true`).

### Cobrança (`/billing`)

| Método e rota | O que faz |
|---|---|
| GET `/billing/plano` | Plano e se dá acesso (leve, para o header). |
| POST `/billing/assinatura` | Cria cliente e assinatura no Asaas (cartão, Pix ou boleto). 409 se já assinante. |
| GET `/billing/assinatura` | Resumo com cobranças, Pix (copia e cola + QR) ou boleto. |
| PUT `/billing/assinatura/forma` | Troca para Pix ou boleto. |
| DELETE `/billing/assinatura` | Cancela: se pago, acesso até o fim do período; se não, na hora. |
| POST `/billing/assinatura/reativar` | Desfaz o cancelamento dentro do período. |
| POST `/billing/assinatura/reembolso` | Estorna tudo em até 7 dias do primeiro pagamento (CDC, art. 49). |
| POST `/billing/assinatura/simular-pagamento` | **Só na simulação**: confirma Pix/boleto pendentes. |
| POST `/webhooks/asaas` | Recebe eventos do Asaas (token no cabeçalho `asaas-access-token`). |

Regra de acesso: libera com `PAYMENT_CONFIRMED`/`PAYMENT_RECEIVED`; suspende com atraso, chargeback ou reprovação
de risco; encerra com reembolso ou exclusão da assinatura. Cancelado e reembolsado não voltam por evento atrasado.

### Plugin (`/plugin`)

| Método e rota | O que faz |
|---|---|
| POST `/plugin/link` | Link de 15 min (exige assinatura com acesso; senão 403). |
| GET `/plugin/baixar/{token}` | Zip de demonstração como anexo · 410 expirado · 404 desconhecido. |

### Outras

`GET /saude` (estado), `/docs` e `/openapi.json` (documentação automática do FastAPI) e, com a simulação ligada,
`/asaas-sim/v3/...` (imita o Asaas, exige a chave `access_token` da simulação).

## 5. Configuração (`api/.env`)

| Variável | Desenvolvimento | Produção |
|---|---|---|
| `ASAAS_BASE_URL` | simulação local | `https://api.asaas.com/v3` |
| `ASAAS_API_KEY` | chave fixa da simulação | chave `$aact_prod_...` (segredo) |
| `ASAAS_SIM_ENABLED` | `true` | **`false`** |
| `ASAAS_WEBHOOK_TOKEN` | valor de exemplo | **segredo aleatório** (32 a 255 caracteres), igual ao cadastrado no Asaas |
| `API_PUBLIC_URL` | `http://127.0.0.1:8000` | endereço HTTPS da API |
| `DATABASE_PATH` | `orbita-dev.db` | caminho em disco com backup |
| `SITE_URL` | `http://localhost:4321` | domínio do site (único liberado no CORS) |
| `COOKIE_SECURE` | `false` | **`true`** |
| `AUTH_CODIGO_NA_RESPOSTA` | `true` | **`false`** |
| `SMTP_*` | vazio (código no log) | provedor de e-mail |

O `api/.env` está no `.gitignore` e nunca vai para o repositório.

---

## 6. Segurança, ponto a ponto

### 6.1 O que já está bem feito

- **Senhas** com scrypt e sal por usuário; comparação em tempo constante (`hmac.compare_digest`).
- **Segredos guardados só como hash**: tokens de sessão, de desafio e de download e o código de 6 dígitos
  ficam como SHA-256. Um vazamento do banco não entrega sessões abertas.
- **2FA obrigatório**: todo cadastro e todo login passam pelo código no e-mail; 10 minutos, 5 tentativas,
  reenvio a cada 60 s.
- **Conta só nasce depois do código**: não dá para criar conta com e-mail de outra pessoa.
- **Cookies** `HttpOnly` (o JavaScript não lê), `SameSite=Lax` (não vão em POST vindo de outro site),
  `Secure` configurável.
- **CORS fechado** no domínio do site, com credenciais.
- **Autorização pela sessão**: nenhuma rota aceita id de usuário de fora; encerrar sessão de outra conta
  devolve 404 (testado).
- **Redirecionamento seguro**: o `next` do Entrar só aceita caminho interno (`/...`), recusa `//` e `/\`.
- **Webhook idempotente** e protegido por token; eventos atrasados não ressuscitam assinatura encerrada.
- **Cartão**: só os 4 últimos dígitos são guardados.
- **SQL parametrizado** em todas as consultas (sem montagem de texto com dados do usuário).
- **Página do site fora do Google** nas áreas de conta e compra (`noindex`).

### 6.2 Pontos críticos e o que fazer

| # | Ponto | Risco | Situação hoje | O que fazer |
|---|---|---|---|---|
| S1 | **Simulação do Asaas ligada por padrão** | **Crítico** | `ASAAS_SIM_ENABLED` vale `true` se o `.env` não disser nada. Com ela ligada, `/asaas-sim/.../confirm` e `/billing/assinatura/simular-pagamento` dão acesso sem pagar, e a chave da simulação é pública no repositório. | Padrão `false` no código; a API **se recusa a subir** em produção com a simulação ligada. |
| S2 | **Token do webhook de exemplo** | **Crítico** | O padrão está no código e no repositório. Quem o souber pode mandar um `PAYMENT_RECEIVED` falso e liberar acesso. | Recusar subir sem um token próprio fora da simulação; comparar com `hmac.compare_digest`; opcional: conferir o pagamento no Asaas (`GET /payments/{id}`) antes de liberar. |
| S3 | **Dados do cartão passam pela API** | **Alto** | O Checkout envia número, validade e CVV para a nossa API, que repassa ao Asaas. Isso coloca a Órbita no escopo mais pesado do PCI DSS. | Usar a tokenização do Asaas no navegador ou o checkout/link de pagamento do Asaas, para o número nunca tocar nosso servidor. Já está na lista do Checkout ("campos seguros do provedor"). |
| S4 | **Código de 2FA no log e na resposta** | **Alto** | Sem SMTP, o código vai para o log; com `AUTH_CODIGO_NA_RESPOSTA=true`, vai na resposta. | Em produção: SMTP obrigatório e `AUTH_CODIGO_NA_RESPOSTA=false` (a API recusa subir com ele ligado fora da simulação). |
| S5 | **Limite de tentativas na memória e só no login** | **Alto** | O limite de 10 falhas/15 min é por e-mail, fica na memória (zera ao reiniciar) e não existe no cadastro, no reenvio por e-mail diferente nem no "esqueci a senha". Dá para disparar e-mails de código para qualquer endereço (incômodo e custo do provedor). | Limite por IP e por e-mail em todas as rotas de `/auth` (tabela no banco ou Redis); CAPTCHA invisível depois de N tentativas. |
| S6 | **`/docs` e `/openapi.json` abertos** | Médio | Mostram todas as rotas a qualquer um. | Desligar em produção (`docs_url=None`) ou proteger. |
| S7 | **Cabeçalhos de segurança** | Médio | A API e o site não mandam HSTS, CSP, `X-Frame-Options`, `Referrer-Policy`. | Configurar no proxy (Nginx/Caddy) ou num middleware: HSTS, CSP restrita, `frame-ancestors 'none'`, `nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`. |
| S8 | **CSRF** | Médio | `SameSite=Lax` + CORS fechado já bloqueiam o ataque comum. Um subdomínio comprometido do mesmo site ainda poderia. | Conferir o cabeçalho `Origin` nas rotas que mudam estado (POST/PUT/DELETE). |
| S9 | **Descoberta de contas** | Médio | Cadastro responde 409 para e-mail existente; login com e-mail inexistente responde mais rápido (não roda o scrypt). | Aceito no cadastro (é útil para a pessoa). No login, rodar o scrypt também quando o e-mail não existe, para igualar o tempo. |
| S10 | **CPF/CNPJ em texto puro** | Médio | Necessário para a nota, mas fica legível no banco e nos backups. | Disco criptografado no servidor, backups criptografados, acesso ao banco só pela API. Avaliar criptografia do campo. |
| S11 | **Banco SQLite** | Médio | Um arquivo, um processo. Bom para o MVP. | Backup diário fora do servidor; ao crescer, PostgreSQL. Rodar a API com um processo só enquanto for SQLite. |
| S12 | **Sessões vencidas e eventos antigos** | Baixo | Ficam no banco para sempre. | Rotina diária que apaga sessões e desafios vencidos e eventos com mais de 90 dias. |
| S13 | **Troca de senha** | Baixo | Ainda não existe; quando existir, precisa derrubar todas as sessões. | Implementar com `DELETE FROM sessoes WHERE usuario_id = ?` (já anotado). |
| S14 | **Token de download no endereço** | Baixo | Aparece em logs do servidor. Vale 15 min. | Aceitável; não registrar o caminho completo no log de acesso. |
| S15 | **Nome e e-mail no `sessionStorage`** | Baixo | Cópia para o avatar aparecer sem piscar; some ao fechar a aba. | Aceitável; some também no Sair. |
| S16 | **Dependências** | Baixo | Versões fixas no `requirements.txt` e no `package-lock.json`. | `pip-audit` e `npm audit` mensais; atualizar com testes. |

### 6.3 LGPD

- **Dados tratados**: nome, e-mail, senha (hash), CPF/CNPJ, aparelho (navegador e sistema) e horários de uso,
  dados de cobrança (no Asaas).
- **Base legal**: execução de contrato (conta e assinatura) e obrigação legal (guarda fiscal dos dados de cobrança).
- **Exclusão de conta**: apaga usuário, sessões e desafios; mantém `assinantes`/`assinaturas` pelo prazo de guarda
  fiscal. Isso precisa estar escrito na Política de privacidade (hoje "a definir").
- **Pendências**: prazos de guarda, encarregado de dados, se as consultas no plugin são guardadas e se treinam
  modelos; botão "baixar meus dados" (item 9).

### 6.4 Lista do dia da publicação

1. `ASAAS_SIM_ENABLED=false`, chave de produção do Asaas e token de webhook novo (S1, S2).
2. `AUTH_CODIGO_NA_RESPOSTA=false`, SMTP configurado e testado (S4).
3. `COOKIE_SECURE=true`, HTTPS no site e na API, site e API no mesmo domínio (ex.: `api.` do domínio do site).
4. `/docs` desligado (S6) e cabeçalhos de segurança no proxy (S7).
5. Limite de tentativas por IP em `/auth` (S5).
6. Backup do banco e disco criptografado (S10, S11).
7. Checkout com tokenização do Asaas (S3) antes de aceitar cartão de verdade.

---

## 7. Testes

`cd api` e `.venv\Scripts\python.exe -m pytest`. Cobrem: cadastro só depois do código, senha com hash, código
errado/expirado/sem tentativas, reenvio, limite de login, cookies HttpOnly, CORS, sessões (manter, expiração,
aparelhos, sair de um, sair de todos, não encerrar sessão alheia), troca de nome, exclusão de conta, assinatura
nas três formas, webhook (token, idempotência, eventos atrasados), cancelamento, reativação, reembolso no prazo e
fora dele, Pix com BR Code e QR, plano para o header, download do plugin (acesso, zip, expiração).

Não cobertos por testes ainda: envio SMTP real (só com servidor falso), limite por IP (não existe), cabeçalhos
de segurança (são do proxy).
