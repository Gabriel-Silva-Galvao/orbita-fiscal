# Cibersegurança da Órbita

Documento vivo, aberto em 26/11/2026 (item 50 da rodada de testes). Junta o que protege o site e a API hoje, as ameaças que
consideramos, os riscos em aberto e o plano de testes. O detalhe técnico de cada rota continua em
[backend-e-seguranca.md](backend-e-seguranca.md) (seção 6, riscos S1 a S17); aqui fica a visão de segurança e o que fazer.

Próximas partes deste documento: a revisão da assinatura com o Asaas (item 37) e a segurança das áreas de suporte e de
administração (itens 51 e 52), que terão regras mais duras que o resto do site.

---

## 1. O que protegemos

| Ativo | Onde fica | Por que importa |
|---|---|---|
| Contas (e-mail, nome, senha) | SQLite da API (`usuarios`) | Senha guardada só como hash scrypt; a conta abre o Portal e o plugin. |
| Sessões | Cookie `orbita_sessao` + `sessoes` (só o SHA-256 do token) | Quem rouba a sessão entra na conta. |
| Códigos de 6 dígitos (2FA) | `desafios` (só o SHA-256) | Liberam cadastro, login, troca de senha e de e-mail. |
| Dados de cobrança e nota | `assinantes`, `assinaturas`; cartão no Asaas | CPF/CNPJ é dado pessoal; o cartão nunca deve ficar conosco. |
| Acesso pago | `assinaturas.status_acesso` | Se alguém libera sem pagar, perdemos receita; se cobra em dobro, perdemos a confiança. |
| Temas de alerta e preferências | `alertas`, `preferencias` | Revelam a área de atuação do cliente. |
| Segredos do servidor | `api/.env` (fora do git) | Chave do Asaas, token do webhook, segredo do servidor MCP, SMTP. |

## 2. Quem pode atacar e como

| Quem | O que tenta | Onde olhamos |
|---|---|---|
| Visitante anônimo | Derrubar a API, adivinhar contas, disparar e-mails, abrir páginas da conta | Limites de tamanho, regex sem ReDoS, limite de tentativas, middleware de sessão |
| Assinante curioso | Ver ou mexer em dados de outra conta, usar recurso do Ouro sem pagar, assinar duas vezes | Autorização sempre pela sessão; regra de plano conferida na API; item 37 |
| Quem rouba uma sessão | Usar a conta de outra pessoa | Cookie HttpOnly e SameSite; lista de aparelhos e "Sair dos outros aparelhos" |
| Quem finge ser o Asaas | Liberar acesso com um webhook falso | Token do webhook com `compare_digest`; recusa token de exemplo em produção |
| Quem finge ser o servidor MCP | Marcar o plugin como ativo de outra conta | Segredo `PLUGIN_SERVIDOR_TOKEN` em `X-Orbita-Servidor`, comparação em tempo constante |
| Pessoa de dentro (futuro: suporte e admin) | Ver dados demais, mudar plano sem registro | Itens 51 e 52: papéis, 2FA obrigatório, registro de auditoria |

## 3. Controles que já existem

**Conta e sessão** (`api/app/auth.py`)
- Senha com scrypt e sal por usuário; comparação em tempo constante. Senha de 8 a 128 caracteres.
- 2FA por e-mail em todo cadastro, login, troca de senha e troca de e-mail: código de 6 dígitos, 10 minutos, 5 tentativas
  por desafio e no máximo 10 códigos errados por conta em 15 minutos.
- Tokens de sessão, desafio e download guardados só como SHA-256.
- Cookie `HttpOnly`, `SameSite=Lax` e `Secure` em produção (`COOKIE_SECURE=true`).
- Troca de senha e troca de e-mail derrubam as outras sessões; a troca de e-mail pede a senha atual e avisa o endereço
  antigo. Lista de aparelhos com "este aparelho", "Sair dos outros" e "Sair de todos".
- Limites na memória com tamanho contido (classe `Limitador`, que não cria chave na leitura e varre as vencidas):
  10 falhas de login por e-mail em 15 minutos; 5 erros da senha atual por conta na troca de senha ou de e-mail;
  10 códigos errados por conta somando todos os desafios. Falta o limite por IP (ver S5).
- O login roda o scrypt mesmo quando o e-mail não existe (`SENHA_FICTICIA`): o tempo não revela quem tem conta.

**Entrada de dados** (todas as rotas)
- Todo texto que entra tem tamanho máximo (`max_length`); acima dele, 422 antes de processar.
- Validação de e-mail com regex linear (sem ReDoS; incidente S17).
- Corpo de pedido limitado a 64 KB (413), por middleware em `api/app/main.py`.
- Valores de listas fechadas (planos, formas, fontes, áreas, dias) validados pelo tipo (`Literal`).
- SQL sempre parametrizado.
- CPF e CNPJ (inclusive o alfanumérico de 2026) com dígito verificador conferido na API (`app/documentos.py`) e no site
  (`src/scripts/validate.ts`).
- Nome e empresa do contato sem caractere de controle (nada de quebra de linha no assunto do e-mail).

**Pedidos de outros sites** (`api/app/main.py`)
- CORS só para o `SITE_URL`, com cookies.
- `ConfereOrigem`: POST, PUT, PATCH e DELETE com `Origin` diferente do `SITE_URL` recebem 403 (CSRF por subdomínio, S8).
- Cabeçalhos em toda resposta da API: `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, CSP que proíbe tudo
  e HSTS com `COOKIE_SECURE`.

**Autorização**
- Nenhuma rota aceita id de usuário de fora: tudo sai da sessão.
- Recurso do Ouro (alertas e resumo) conferido na API, não só na tela: 403 nos outros planos.
- Download do plugin só com assinatura ativa; link de 15 minutos.
- Rotas de simulação (`simular-pagamento`, `simular-conexao`, `/asaas-sim`) só existem com `ASAAS_SIM_ENABLED=true`.

**Pagamento**
- Webhook do Asaas com token, idempotente, e eventos atrasados não reativam assinatura encerrada.
- Uma operação de cobrança por conta de cada vez (`uma_operacao_por_vez`, tabela `operacoes_cobranca`): assinar,
  trocar plano ou forma, cancelar, reativar e reembolsar. O pedido concorrente recebe 409 `em_andamento`.
- Só os 4 últimos dígitos do cartão ficam conosco (o número ainda passa pela API; ver S3).

**Ambiente** (`api/app/config.py`)
- `ORBITA_ENV` diz onde a API roda; o padrão é `production`. O desenvolvimento declara `ORBITA_ENV=development`.
- A API não sobe com configuração perigosa (`problemas_de_producao`). Em produção: simulação ligada, `COOKIE_SECURE=false`
  ou SMTP vazio. Em qualquer ambiente: simulação fora de localhost. Sem a simulação: token de exemplo, chave da
  simulação, código do 2FA na resposta, segredo do MCP curto.
- `/docs`, `/redoc` e `/openapi.json` só em desenvolvimento.

**Site** (Astro)
- Páginas da conta e de compra fora do Google (`noindex`, `X-Robots-Tag`).
- O `next` do Entrar só aceita caminho interno (`caminhoSeguro`: sem caractere de controle, sem barra invertida, mesma origem).
- Valores vindos da API entram na tela por `textContent`, não por HTML.
- Formulários com dado pessoal usam `method="post"`: sem JavaScript, nada vai para o endereço.
- Cabeçalhos de segurança nas páginas renderizadas no servidor (`src/scripts/cabecalhos.ts`); as estáticas dependem do proxy (S7).

## 4. Riscos em aberto

Os riscos S1 a S17 estão detalhados em [backend-e-seguranca.md](backend-e-seguranca.md). Resumo do que falta, em ordem:

| # | Risco | Gravidade | O que fazer | Quando |
|---|---|---|---|---|
| S18 | **Assinatura em dobro por pedidos simultâneos** (novo, 26/11/2026; **corrigido** em 26/11/2026, ver 4.1 e 5.1) | ~~Alto~~ | Hoje `POST /billing/assinatura` confere se já existe assinatura e só depois cria a cobrança no Asaas e grava com `INSERT OR REPLACE`. Dois pedidos ao mesmo tempo (clique duplo, duas abas) passam os dois pela conferência: o Asaas cria duas assinaturas e a primeira fica órfã, cobrando. Corrigir com uma trava por usuário (reserva gravada no banco antes de chamar o Asaas, com `INSERT` que falha se já houver) e chave de idempotência no Asaas; teste com pedidos em paralelo. | Item 37 |
| S3 | Cartão passa pela API (ARES-ARC-001) | Alto | Tokenização do Asaas no navegador ou página de pagamento do Asaas; a API recebe só o token. **Decisão pendente** (4.2). | Com o Sandbox (item 29) |
| QA-008 | **Upgrade libera o Ouro sem cobrar a diferença** (piorou em 26/11/2026: alertas e resumo dependem do plano) | Médio (proposta) | Quem paga Prata e sobe para Ouro usa o recurso Ouro até a próxima cobrança sem pagar a diferença. Definir a regra (cobrança proporcional na hora, ou o plano novo só vale depois do pagamento). **Decisão pendente** (4.2). | Antes de publicar |
| S5 | Limite de tentativas só na memória (em parte corrigido: limites por conta e memória contida, ver 5.1) | Alto | Falta: limite por IP em todo `/auth` e no contato, guardado no banco ou no Redis; CAPTCHA invisível depois de N falhas. Depende de saber qual proxy vai na frente da API (o IP real vem dele). | Antes de publicar |
| S4 | Código do 2FA no log sem SMTP (**corrigido** em 26/11/2026: produção exige SMTP, ver 5.1) | ~~Alto~~ | — | — |
| S6 | `/docs` aberto (**corrigido** em 26/11/2026: só em desenvolvimento, ver 5.1) | ~~Médio~~ | — | — |
| S7 | Cabeçalhos de segurança (em parte corrigido: API e páginas do servidor, ver 5.1) | Médio | Falta: os mesmos cabeçalhos nas páginas estáticas, no proxy; e uma CSP que restrinja scripts e estilos (exige revisar fontes, fotos e scripts). | Antes de publicar |
| S8 | CSRF por subdomínio (**corrigido** em 26/11/2026: `Origin` conferido, ver 5.1) | ~~Médio~~ | — | — |
| S9 | Descoberta de contas (login corrigido: mesmo tempo com ou sem conta, ver 5.1) | Baixo | Falta: o cadastro responde 409 para e-mail que já tem conta. O time tinha aceitado (é útil para quem se cadastra); a alternativa é responder sempre 202 e mandar "você já tem conta" por e-mail. **Decisão pendente** (4.2). | Antes de publicar |
| SEC-009 | Contato empresarial (em parte corrigido: confirmação sem texto digitado e limite por destino, ver 5.1) | Baixo | Falta: IP real atrás do proxy (`--proxy-headers` e `--forwarded-allow-ips` no uvicorn) e CAPTCHA. | Com o proxy |
| CAND-04 | Reembolso aceito depois de cancelar | — | Hoje uma assinatura cancelada dentro dos 7 dias ainda pode pedir reembolso. Pode ser o certo pelo CDC, art. 49. **Decisão pendente** (4.2). | Com o jurídico |
| S10, S11 | CPF/CNPJ legível; SQLite | Médio | Disco e backups criptografados; PostgreSQL ao crescer. | Infra |
| S12 | Sessões e desafios vencidos ficam no banco | Baixo | Rotina diária de limpeza. | Infra |
| S16 | Dependências | Baixo | `pip-audit` e `npm audit` mensais. | Rotina |

## 4.1 Correção do S18: assinatura em dobro (feita em 26/11/2026)

**O problema, passo a passo** (`api/app/billing.py`, `criar_assinatura`, antes da correção):
1. Lia `assinaturas` e, se já houvesse assinatura viva, respondia 409.
2. Criava o cliente no Asaas (se ainda não existia) e gravava em `assinantes`.
3. Criava a assinatura no Asaas (`asaas.criar_assinatura`).
4. Gravava em `assinaturas` com `INSERT OR REPLACE`.

Entre o passo 1 e o 4 passa o tempo da chamada ao Asaas (centenas de milissegundos). Dois pedidos no mesmo intervalo
(clique duplo, duas abas, repetição automática do navegador) passavam os dois pelo passo 1: duas assinaturas no Asaas, a
segunda substituía a primeira no nosso banco e a primeira ficava órfã, cobrando todo mês sem aparecer no Portal. O passo 2
tinha o mesmo defeito: dois clientes no Asaas para a mesma pessoa e um erro 500 no segundo `INSERT`.

**O que foi feito** (commit `81e7a5c`, ARES-QA-003; estendido às outras rotas de cobrança em `2f10846`, CAND-01 a 03):
1. **Reserva por conta antes de chamar o Asaas:** `uma_operacao_por_vez` faz `INSERT` na tabela `operacoes_cobranca`
   (chave `usuario_id`); se a linha já existe, o pedido recebe **409 `em_andamento`**. A chave primária do SQLite garante
   isso mesmo com mais de um processo da API.
2. **A conferência de "já é assinante" acontece dentro da reserva,** sem janela entre as duas.
3. **A reserva sai no fim do pedido** (`finally`), com sucesso ou erro; reserva com mais de 120 s é tratada como
   abandonada e apagada.
4. **Cliente do Asaas criado uma vez só,** porque a criação também fica dentro da reserva.
5. **No site:** com o 409 `em_andamento`, o Checkout mostra o aviso e o link para Plano e pagamento, sem mexer no pedido da
   outra aba.
6. **Testes:** `test_pedidos_simultaneos_criam_uma_assinatura_so` (falha no código antigo com 4× 201),
   `test_reserva_esquecida_expira` e `test_reembolsos_simultaneos_estornam_uma_vez_so`.

**O que ficou do plano e ainda não foi feito:**
- O `INSERT OR REPLACE` continua; hoje só substitui assinatura em estado final, porque a conferência já roda dentro da
  reserva. Trocar por `INSERT` + `UPDATE` explícito deixaria isso garantido pelo código, não pela ordem das linhas.
- **Rede de segurança no Asaas:** ao criar, consultar se já existe assinatura ativa com a mesma `externalReference` e
  reaproveitar; conferir se o Asaas aceita chave de idempotência quando o Sandbox estiver ligado (item 29).
- Testes que faltam: nova assinatura depois de uma cancelada ou reembolsada, e erro do Asaas no meio do pedido liberando a
  reserva para o pedido seguinte.

**Fica para o item 37** (precisa do Sandbox): webhook repetido e fora de ordem com o Asaas real, troca de plano e de forma
ao mesmo tempo, e a conferência periódica de assinaturas órfãs no Asaas (relatório para o Admin, item 52).

## 4.2 Decisões pendentes (26/11/2026)

O que a revisão ARES deixou em aberto porque depende de uma escolha do time, do jurídico ou da infraestrutura. Todo o
resto dos achados foi corrigido (seção 5.1).

| Decisão | Quem decide | Opções | Achado |
|---|---|---|---|
| Como cobrar o upgrade no meio do mês | Empresa | (a) cobrança proporcional na hora, via Asaas; (b) o plano novo só vale depois do pagamento da diferença; (c) o plano novo só vale na próxima cobrança | ARES-QA-008 |
| Como receber o cartão | Empresa e técnico | (a) página de pagamento do Asaas; (b) tokenização do Asaas no navegador, com o formulário próprio | ARES-ARC-001 (S3) |
| Cadastro com e-mail que já tem conta | Empresa | (a) manter o 409 "Esse e-mail já tem conta"; (b) responder sempre 202 e avisar por e-mail | ARES-SEC-007 (S9) |
| Reembolso depois de cancelar | Jurídico | (a) manter (direito de arrependimento em 7 dias); (b) recusar depois do cancelamento | CAND-04 |
| Proxy de produção | Técnico | Nginx, Caddy ou Cloudflare: dele dependem o IP real, o limite por IP, o CAPTCHA e os cabeçalhos das páginas estáticas | S5, S7, SEC-009 |
| CNPJ alfanumérico no Asaas | Técnico, com o Sandbox | Confirmar se o Asaas real aceita o formato; API e site já aceitam | ARES-QA-009 |

## 5. Incidentes

| Data | O que houve | Causa | Correção |
|---|---|---|---|
| 26/11/2026 | A API parou de responder; o site devolvia 503 nas páginas da conta. | ReDoS no regex de e-mail: um e-mail com domínio longo cheio de pontos segurava o processo (S17). | Regex linear, limite de tamanho em todos os campos e corpo de até 64 KB; testes em `api/tests/test_limites.py`. |

Para cada incidente novo: o que o usuário viu, a causa confirmada, a correção, o teste que impede a volta e a linha aqui.

## 5.1 Correções da revisão ARES (a partir de 26/11/2026)

Achados das revisões REVIEW-001 a 005 do ARES (registro completo no artefato
[Vulnerabilidades da Órbita](https://claude.ai/artifact/UqJWvjZsAcGB94uDhCssjD), cópia em `artefatos/06-vulnerabilidades/`).
Cada correção tem um commit próprio e um teste de regressão que falha no código antigo.

| ID | Gravidade | O que estava errado | Correção | Teste |
|---|---|---|---|---|
| ARES-SEC-017 e ARES-QA-012 | Alta | Com uma sessão roubada, dava para trocar o e-mail sem a senha; o dono ficava trancado fora (a recuperação vai para o e-mail) e as outras sessões continuavam abertas. | `POST /auth/email/trocar` exige a senha atual (401 `senha_atual`); ao confirmar, as outras sessões caem e o e-mail antigo recebe aviso (`correio.avisar_troca_de_email`). Na tela, campo "Sua senha atual". | `test_conta.py::test_troca_de_email_exige_senha_derruba_sessoes_e_avisa_o_antigo` |
| ARES-QA-003 (risco S18) | Alta | Quatro `POST /billing/assinatura` ao mesmo tempo (clique duplo, duas abas) criavam quatro assinaturas cobradas no Asaas; a Órbita guardava uma e as outras ficavam órfãs, cobrando. | Reserva por conta na tabela `operacoes_cobranca` (INSERT atômico) antes de chamar o Asaas, liberada no fim mesmo com erro e vencida após 120 s; o segundo pedido recebe 409 `em_andamento`. O Checkout mostra o aviso e não mexe no pedido da outra aba. | `test_billing.py::test_pedidos_simultaneos_criam_uma_assinatura_so`, `test_reserva_esquecida_expira` |
| ARES-SEC-018 | Média (Alta junto com a SEC-017) | Com uma sessão roubada, a senha atual podia ser chutada sem limite na troca de senha, contornando o limite do login. | Contador de erros da senha atual por conta, o mesmo na troca de senha e na de e-mail: no 5º erro em 15 minutos, 429 até a janela passar. | `test_conta.py::test_senha_atual_tem_limite_de_tentativas` |
| ARES-SEC-002 | Média | O código de 6 dígitos tinha 5 tentativas por desafio, mas cada login novo abria outro desafio com mais 5: sem teto por conta. | Teto de 10 códigos errados por e-mail em 15 minutos, somando todos os desafios: acima dele, nem o código certo passa e o login não abre desafio novo (429). Acerto zera o contador. | `test_auth.py::test_codigo_tem_teto_por_conta_somando_os_logins` |
| ARES-SEC-016 | Média | O contador de falhas do login criava uma chave por e-mail digitado (até numa leitura) e nunca apagava: um anônimo fazia a memória da API crescer sem limite com e-mails inventados. | Classe `Limitador` em `auth.py`: ler não cria chave, fila vazia sai, chave é hash curto, cada fila guarda no máximo o teto e há varredura das chaves vencidas a cada 1.000 falhas. A memória fica proporcional às falhas dos últimos 15 minutos. Ainda falta o limite por IP (S5). | `test_auth.py::test_limitador_de_login_nao_cresce_sem_limite`, `test_limitador_guarda_no_maximo_o_teto_por_chave` |
| ARES-QA-010 | Baixa | "Reenviar o código" na troca de senha ou de e-mail criava um desafio sem dono, e a confirmação sempre respondia 410. | `/auth/codigo/reenviar` repassa o `usuario_id` do desafio original. | `test_conta.py::test_reenviar_o_codigo_da_troca_funciona` |
| ARES-QA-011 | Informativa | Se outra conta pegasse o mesmo e-mail entre a conferência e a gravação (corrida), a confirmação da troca de e-mail ou do cadastro respondia 500. | O `UPDATE`/`INSERT` trata o `IntegrityError` do UNIQUE e responde 409 `email_em_uso`. | `test_conta.py::test_corrida_na_confirmacao_da_troca_de_email_responde_409`, `test_corrida_na_confirmacao_do_cadastro_responde_409` |
| ARES-QA-002 | Baixa | Quebra de linha em "empresa" (vai no assunto do e-mail) derrubava `/contato/empresarial` com 500, e a mensagem se perdia porque era gravada só depois do envio. | Nome e empresa com caractere de controle recebem 422; a mensagem é gravada antes do envio e marcada como enviada depois. | `test_contato.py::test_quebra_de_linha_em_nome_ou_empresa_e_recusada_sem_500`, `test_mensagem_fica_registrada_mesmo_se_o_envio_falhar` |
| ARES-SEC-004 | Baixa | O `?next=` do Entrar só barrava `//` e `/\` no começo; `/%09/site` passava e o navegador, que remove o TAB, ia para outro domínio (open redirect, útil para phishing). | Função única `caminhoSeguro` (`src/scripts/caminho-seguro.ts`), usada no middleware e no `entrar.astro`: recusa caractere de controle e barra invertida e confere que o caminho resolvido continua na mesma origem. Primeiro teste automático do site: `npm run test:site`. | `scripts/testes/caminho-seguro.test.ts` |
| ARES-SEC-007 (parte do login; risco S9) | Baixa | O login com e-mail inexistente pulava o scrypt e respondia mais rápido: o tempo revelava quais e-mails têm conta. | O login confere a senha contra um hash fictício quando a conta não existe (`SENHA_FICTICIA`), então o tempo é o mesmo. **Falta decidir** o 409 do cadastro, que o time tinha aceitado (seção 4, S9). | `test_auth.py::test_login_com_email_inexistente_tambem_roda_o_scrypt` |
| ARES-QA-009 | Informativa | A API só contava se o CPF/CNPJ tinha 11 ou 14 dígitos; número inventado ia para o Asaas e para a nota (o site conferia, mas a API não). | `app/documentos.py` confere os dígitos verificadores de CPF, CNPJ e CNPJ alfanumérico (Receita, julho de 2026) na assinatura e nos dados da nota; os limites de tamanho já existiam. O site também aceita o CNPJ alfanumérico (campo com letras, máscara e o mesmo cálculo em `src/scripts/validate.ts`, testes em `scripts/testes/documentos.test.ts`). **Pendente:** confirmar se o Asaas real aceita CNPJ alfanumérico. | `test_documentos.py` |
| CAND-01 a CAND-03 (novos, achados ao conferir o código do pull) | Não classificados | Reembolso, troca de plano, troca de forma, cancelar e reativar conferiam o estado e só depois chamavam o Asaas: pedidos simultâneos pediam o estorno mais de uma vez ou deixavam o banco e o Asaas em estados opostos. | As cinco rotas usam a mesma reserva por conta da ARES-QA-003 (`uma_operacao_por_vez`); o pedido concorrente recebe 409 `em_andamento`. | `test_billing.py::test_reembolsos_simultaneos_estornam_uma_vez_so` |
| CAND-05 (novo, a partir de um alerta do ZAP) | Não classificado | Os formulários não declaravam `method`, então o padrão era GET: se o script da página falhasse ou demorasse e a pessoa apertasse Enter, a senha (e, no Checkout, o número e o CVV do cartão) iam para o endereço, o histórico e o log do servidor. O ZAP viu `/entrar?email=…&senha=…`. | `method="post"` nos 12 formulários com dado pessoal (Entrar, Checkout, Conta e segurança, Alertas, forma de pagamento e os dois de contato). A busca do Portal continua GET de propósito. | Revisão do HTML (`grep "<form"`); o site ainda não tem teste de navegador |
| ARES-SEC-006 (riscos S1 e S2) | Precisava validar | "Produção" era deduzida do `COOKIE_SECURE`: com `COOKIE_SECURE=false`, a simulação (acesso sem pagar, token público do webhook) subia num servidor público. | Variável `ORBITA_ENV` (`production` por padrão). Em produção: simulação proibida e `COOKIE_SECURE` obrigatório. Em qualquer ambiente: simulação só com site e API em localhost. O desenvolvimento declara `ORBITA_ENV=development` (`.claude/launch.json`, `api/.env.example`, testes). | `test_config.py::test_simulacao_em_producao_e_recusada_mesmo_sem_cookie_secure`, `test_producao_e_o_padrao`, `test_simulacao_so_roda_em_localhost` |
| ARES-QA-007 (parte; riscos S4 e S5) | Informativa | Produção subia sem SMTP, e o código do 2FA ia para o log; e-mails entravam no log com `%s`. | Em produção a API se recusa a subir sem `SMTP_HOST`; e-mails no log com `%r`. **Pendente:** limite por IP em `/auth`, que depende de saber qual proxy vai na frente da API (mesma questão da SEC-009). | `test_config.py::test_producao_sem_smtp_nao_sobe` |
| ARES-QA-005 (risco S6) | Informativa | `/docs`, `/redoc` e `/openapi.json` mostravam todas as rotas (inclusive as da simulação) a qualquer um. | Só existem com `ORBITA_ENV=development`; em produção, 404. | `test_config.py::test_docs_fechados_em_producao` |
| ARES-SEC-005 | Precisava validar | `/asaas-sim/_eventos` (só com a simulação ligada) respondia sem autenticação e listava eventos de cobrança. | Exige a mesma chave `access_token` das rotas `/v3` da simulação. Com a SEC-006, a simulação também só roda em localhost. | `test_asaas_sim.py::test_eventos_da_simulacao_exigem_a_chave` |
| ARES-QA-004 (risco S7; parte do S8) | Informativa | Site e API sem CSP, anti-clickjacking, nosniff, Referrer-Policy e HSTS (o ZAP confirmou nos dois). | API: middleware `CabecalhosDeSeguranca` com nosniff, `X-Frame-Options: DENY`, Referrer-Policy, CSP que proíbe tudo (a API só devolve JSON) e HSTS com `COOKIE_SECURE`. Site: `src/scripts/cabecalhos.ts` no middleware, com CSP que barra moldura, `base`, plugins e envio de formulário para fora. **Pendente:** (1) as páginas estáticas do site não passam pelo middleware, então o proxy de produção precisa mandar os mesmos cabeçalhos; (2) uma CSP que restrinja scripts e estilos; (3) conferência de `Origin` nas rotas que mudam estado (S8). | `test_limites.py::test_cabecalhos_de_seguranca_em_toda_resposta`, `scripts/testes/cabecalhos.test.ts`; conferido com `curl` no build (`/conta` e `/entrar` com os cabeçalhos, `/` estática sem eles) |
| ARES-DEP-001 e ARES-DEP-002 (risco S16) | Informativa | fastapi 0.115.6 trazia a starlette 0.41.3, com 8 CVEs (nenhum alcançável pelo código, mas vulnerável); o pytest 8.3.4 (1 CVE) estava no `requirements.txt` de produção. | fastapi 0.162.5 e starlette 1.10.0, agora fixada explicitamente; pytest 9.2.0 em `requirements-dev.txt`, separado do de produção. Versões com pelo menos duas semanas de publicação. | `pip-audit` do ambiente: 9 alertas antes, "No known vulnerabilities found" depois; os 128 testes passam nas versões novas |
| ARES-SEC-009 (parte) | Precisava validar | O formulário de contato aceita qualquer e-mail e mandava a ele uma confirmação com o nome e a empresa digitados (texto de um estranho assinado pela Órbita); o limite era só por IP, que muda fácil. | A confirmação não repete nada do que foi digitado; limite de 5 mensagens por hora também por endereço de destino (mesmo `Limitador` da SEC-016). **Pendente:** IP real atrás do proxy e CAPTCHA, que dependem da produção. | `test_contato.py::test_confirmacao_nao_repete_o_texto_de_quem_escreveu`, `test_limite_por_destino_mesmo_mudando_de_ip` |
| Risco S8 (parte da ARES-QA-004) | Média (no doc. do projeto) | CSRF por subdomínio: `SameSite=Lax` e o CORS fechado barram o ataque comum, mas um subdomínio comprometido do mesmo site ainda conseguiria mandar um POST com o cookie. | Middleware `ConfereOrigem`: pedido que muda estado (POST, PUT, PATCH, DELETE) com `Origin` diferente do `SITE_URL` recebe 403 `origem_recusada`; sem `Origin` (webhook, servidor MCP) segue como antes; o preflight do CORS continua funcionando. | `test_limites.py::test_pedido_de_outra_origem_que_muda_estado_e_recusado` |

## 6. Plano de testes de segurança

**Automáticos da API** (`cd api` e `.venv\Scripts\python.exe -m pytest`, 131 testes em 26/11/2026)
- Conta e sessão, limites de tentativas, troca de senha e de e-mail: `test_auth.py`, `test_conta.py`.
- Cobrança, webhook e pedidos em paralelo (assinatura e reembolso): `test_billing.py`.
- Configuração de produção (`ORBITA_ENV`, SMTP, `/docs`): `test_config.py`.
- Entrada de dados, ReDoS, cabeçalhos e `Origin`: `test_limites.py`.
- CPF e CNPJ: `test_documentos.py`. Contato: `test_contato.py`. Simulação: `test_asaas_sim.py`.
- Plugin e segredo do servidor MCP: `test_plugin.py`. Regra do Ouro nos alertas: `test_alertas.py`.

**Automáticos do site** (`npm run test:site`, 9 testes): `next` do Entrar, cabeçalhos e CPF/CNPJ, em `scripts/testes/`.

**A acrescentar**
- Item 37: webhook repetido e fora de ordem com assinaturas reais do Sandbox.
- Limite por IP (S5), quando existir.
- Upgrade seguido de recurso do Ouro (QA-008), depois da decisão.
- Para cada rota nova: sem sessão (401), sessão de outra conta (404 ou 403), plano errado (403), campo gigante (422),
  corpo gigante (413).

**Revisões**
- Rodar a revisão de segurança (`/security-review`) em toda mudança de cobrança, login e, no futuro, admin e suporte.
- Antes de publicar: varredura com o OWASP ZAP contra o ambiente de teste, `pip-audit` e `npm audit`.
- A cada trimestre: revisar este documento, os riscos em aberto e quem tem acesso aos segredos.

## 7. Regras para quem mexe no código

1. Todo campo de texto novo nasce com `max_length`.
2. Nenhuma regex sobre texto do usuário com quantificadores aninhados ou sobrepostos; quando houver dúvida, limitar o
   tamanho antes e testar com 100 mil caracteres.
3. Regra de plano ou de dono sempre na API; a tela só esconde.
4. Segredo só no `api/.env`; nunca no código, no git, no log ou no chat.
5. Comparar segredos com `hmac.compare_digest`.
6. Valor que veio de fora entra na tela por `textContent`.
7. Toda rota de simulação ou de teste fica atrás de `ASAAS_SIM_ENABLED` e entra em `problemas_de_producao` se for perigosa.
8. Mudança em cobrança, login, admin ou suporte passa pela revisão de segurança antes do commit.
9. Rota de cobrança que confere o estado e depois chama o Asaas roda dentro de `uma_operacao_por_vez`; teste com
   pedidos em paralelo.
10. Toda correção de segurança tem um teste de regressão que falha no código antigo e um commit próprio.
11. Configuração que só vale no desenvolvimento depende de `ORBITA_ENV=development`, nunca de outra variável.
12. Formulário com dado pessoal usa `method="post"`; destino de redirecionamento passa por `caminhoSeguro`.
