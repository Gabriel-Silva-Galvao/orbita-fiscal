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
- Limite de 10 falhas de login por e-mail em 15 minutos (na memória; ver S5).

**Entrada de dados** (todas as rotas)
- Todo texto que entra tem tamanho máximo (`max_length`); acima dele, 422 antes de processar.
- Validação de e-mail com regex linear (sem ReDoS; incidente S17).
- Corpo de pedido limitado a 64 KB (413), por middleware em `api/app/main.py`.
- Valores de listas fechadas (planos, formas, fontes, áreas, dias) validados pelo tipo (`Literal`).
- SQL sempre parametrizado.

**Autorização**
- Nenhuma rota aceita id de usuário de fora: tudo sai da sessão.
- Recurso do Ouro (alertas e resumo) conferido na API, não só na tela: 403 nos outros planos.
- Download do plugin só com assinatura ativa; link de 15 minutos.
- Rotas de simulação (`simular-pagamento`, `simular-conexao`, `/asaas-sim`) só existem com `ASAAS_SIM_ENABLED=true`.

**Pagamento**
- Webhook do Asaas com token, idempotente, e eventos atrasados não reativam assinatura encerrada.
- Só os 4 últimos dígitos do cartão ficam conosco.
- A API não sobe com configuração perigosa (`problemas_de_producao`): simulação com cookie seguro, token de exemplo,
  chave da simulação, código do 2FA na resposta, segredo do MCP curto.

**Site** (Astro)
- Páginas da conta e de compra fora do Google (`noindex`, `X-Robots-Tag`).
- O `next` do Entrar só aceita caminho interno.
- Valores vindos da API entram na tela por `textContent`, não por HTML.

## 4. Riscos em aberto

Os riscos S1 a S17 estão detalhados em [backend-e-seguranca.md](backend-e-seguranca.md). Resumo do que falta, em ordem:

| # | Risco | Gravidade | O que fazer | Quando |
|---|---|---|---|---|
| S18 | **Assinatura em dobro por pedidos simultâneos** (novo, 26/11/2026; **corrigido** em 26/11/2026, ver 5.1) | ~~Alto~~ | Hoje `POST /billing/assinatura` confere se já existe assinatura e só depois cria a cobrança no Asaas e grava com `INSERT OR REPLACE`. Dois pedidos ao mesmo tempo (clique duplo, duas abas) passam os dois pela conferência: o Asaas cria duas assinaturas e a primeira fica órfã, cobrando. Corrigir com uma trava por usuário (reserva gravada no banco antes de chamar o Asaas, com `INSERT` que falha se já houver) e chave de idempotência no Asaas; teste com pedidos em paralelo. | Item 37 |
| S3 | Cartão passa pela API | Alto | Tokenização do Asaas no navegador; a API recebe só o token. | Com o Sandbox (item 29) |
| S5 | Limite de tentativas só na memória e só no login | Alto | Limite por IP e por e-mail em todo `/auth`, guardado no banco; CAPTCHA invisível depois de N falhas. | Antes de publicar |
| S4 | Código do 2FA no log sem SMTP | Alto | Exigir SMTP fora da simulação. | Antes de publicar |
| S6 | `/docs` aberto | Médio | Desligar em produção. | Antes de publicar |
| S7 | Sem cabeçalhos de segurança | Médio | HSTS, CSP restrita, `frame-ancestors 'none'`, `nosniff`, `Referrer-Policy` no proxy. | Antes de publicar |
| S8 | CSRF por subdomínio | Médio | Conferir `Origin` nas rotas que mudam estado. | Antes de publicar |
| S9 | Descoberta de contas pelo tempo do login | Médio | Rodar o scrypt também quando o e-mail não existe. | Antes de publicar |
| S10, S11 | CPF/CNPJ legível; SQLite | Médio | Disco e backups criptografados; PostgreSQL ao crescer. | Infra |
| S12 | Sessões e desafios vencidos ficam no banco | Baixo | Rotina diária de limpeza. | Infra |
| S16 | Dependências | Baixo | `pip-audit` e `npm audit` mensais. | Rotina |

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

## 6. Plano de testes de segurança

**Automáticos** (`cd api` e `.venv\Scripts\python.exe -m pytest`, 92 testes em 26/11/2026)
- Conta e sessão: `test_auth.py`, `test_conta.py`.
- Cobrança e webhook: `test_billing.py`, `test_config.py`.
- Entrada de dados e ReDoS: `test_limites.py`.
- Plugin e segredo do servidor MCP: `test_plugin.py`.
- Regra do Ouro nos alertas: `test_alertas.py`.

**A acrescentar**
- Item 37: pedidos de assinatura em paralelo (S18), webhook repetido e fora de ordem, troca de plano e de forma ao mesmo tempo.
- Limite por IP (S5), quando existir.
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
