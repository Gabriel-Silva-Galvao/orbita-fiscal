# Preparação interna para o suporte e o admin

Documento de planejamento, aberto em 27/11/2026. Diz o que precisa mudar **no app atual** (API e site) para que o
suporte ([suporte.md](suporte.md)) e a administração ([admin.md](admin.md)) funcionem bem quando forem construídos:
as conexões entre as partes e a reorganização interna. Nada disto está feito.

A ideia central: hoje cada rota do cliente faz tudo sozinha (confere, chama o Asaas, grava). A equipe vai precisar
fazer as **mesmas operações** sobre a conta de outra pessoa, com registro de quem fez. Então as regras saem das rotas
e vão para funções reutilizáveis, e toda mudança passa a saber **quem a pediu**.

---

## 1. Como a API está hoje (27/11/2026)

| Módulo | O que faz | Linhas |
|---|---|---|
| `auth.py` | Cadastro, login com código, sessões, troca de senha e e-mail, aparelhos | 630 |
| `billing.py` | Assinatura, plano, forma, cancelar, reativar, reembolso, webhook do Asaas | 470 |
| `plugin.py` | Download, status, uso por IA (`resumo_de_uso`) | 235 |
| `alertas.py`, `contato.py`, `correio.py`, `documentos.py` | Alertas do Ouro, contato empresarial, e-mail, CPF/CNPJ | ~400 |
| `db.py` + `ESQUEMA` de cada módulo | SQLite; tabelas criadas na subida; colunas novas por `ALTER` solto | 83 |
| `main.py` | Monta a API, middlewares (64 KB, `Origin`, cabeçalhos, CORS) e a simulação do Asaas | 215 |

Pontos que atrapalham a área da equipe:
- A regra de negócio mora dentro das rotas (ex.: `reembolsar`, `cancelar` em `billing.py`): a equipe não tem como
  reaproveitar.
- Nenhuma mudança registra quem a fez (cliente, equipe ou sistema).
- A conta não tem estado próprio: não dá para suspender um cliente, só a assinatura.
- As migrações do banco são `ALTER` espalhados, sem número de versão.
- Não existe rotina agendada (tudo acontece num pedido).
- O e-mail é enviado na hora, sem fila nem nova tentativa.
- CORS e conferência de `Origin` aceitam uma origem só (o site).

## 2. Camada de serviços (a mudança principal)

Separar cada módulo em duas partes:

```
api/app/
  servicos/            regras de negócio, sem FastAPI
    contas.py          suspender, reativar, apagar, encerrar sessões, reenviar verificação
    assinaturas.py     assinar, trocar plano/forma, cancelar, reativar, pedir/aprovar/recusar reembolso
    plugin.py          resumo de uso, status
    chamados.py        abrir, responder, mudar situação (novo)
    auditoria.py       registrar (novo)
  rotas/               só HTTP: valida a entrada, pega o ator, chama o serviço
    cliente/           as rotas de hoje (/auth, /billing, /plugin, /alertas, /contato, /suporte)
    equipe/            rotas da equipe (/equipe/...), novas
```

- **Toda função de serviço recebe o `ator`**: `{tipo: "cliente" | "equipe" | "sistema", id, papel?, motivo?}`.
  - O cliente só age sobre a própria conta (o id vem da sessão, nunca do pedido).
  - A equipe age sobre `usuario_id` informado, depois da checagem de papel.
  - O sistema são as rotinas e o webhook.
- **A auditoria é gravada dentro do serviço**, não na rota: nenhuma ação da equipe escapa do registro, venha de onde
  vier. Ações do cliente e do sistema entram num histórico da conta (seção 4), não na auditoria da equipe.
- `uma_operacao_por_vez` continua valendo para a equipe: cliente e equipe mexendo na mesma assinatura ao mesmo tempo
  recebem 409 `em_andamento`.
- **Migração sem quebrar nada:** mover uma rota por vez para o serviço, com os testes atuais (134) passando a cada
  passo. As rotas do cliente mantêm o mesmo caminho e a mesma resposta.

## 3. Banco de dados

**Migrações numeradas**
- Tabela `migracoes (versao, aplicada_em)` e uma pasta `api/migracoes/` com arquivos `0001_…sql`, `0002_…sql`.
- Na subida, a API aplica as que faltam, em ordem, dentro de uma transação. Substitui os `ALTER` soltos de `db.py` e
  `auth.migrar`.
- A primeira migração registra o esquema de hoje como está (bancos existentes não perdem nada).

**SQLite até a produção**
- Ligar `PRAGMA journal_mode=WAL` e `busy_timeout`: com a área da equipe, haverá leituras longas (filas, auditoria)
  ao lado das escritas do cliente.
- A auditoria só de inserção e a separação de permissões (admin.md, seção 5) pedem PostgreSQL; a camada de serviços
  e as migrações numeradas deixam essa troca possível sem reescrever as rotas.

**Colunas e tabelas novas no que já existe**

| Onde | O que | Para quê |
|---|---|---|
| `usuarios` | `situacao` (ativa, suspensa, apagada), `suspensa_em`, `suspensa_motivo` | O admin suspende a conta; `usuario_logado` passa a recusar conta suspensa (403 `conta_suspensa`) |
| `usuarios` | `ultima_atividade` | Usuários online (admin.md); gravada no máximo uma vez por minuto |
| `sessoes` | `ip_prefixo` (só os 3 primeiros blocos) | A ficha mostra aparelhos sem guardar o IP inteiro |
| `assinaturas` | situação `reembolso_em_analise` | O reembolso vira pedido (seção 5) |
| `pedidos_reembolso` (nova) | id, usuario_id, valor, situação, motivo, melhorar, uso_plugin, pedido_em, prazo, decidido_por, decidido_em, motivo_decisao | Substitui `reembolso_feedback` (os dados atuais migram) |
| `historico_conta` (nova) | usuario_id, quando, ator_tipo, ator_id, acao, detalhe | A linha do tempo da ficha: plano trocado, cancelou, reembolso, suspensão |
| `avisos_portal` (nova) | id, titulo, texto, publicado_em, despublicado_em | Hoje as novidades estão fixas em `src/data/novidades.ts` |
| `emails_saida` (nova) | id, para, modelo, dados, situacao, tentativas, proxima_tentativa | Fila de e-mail (seção 7) |

## 4. Conexões com o que já existe

| Parte atual | O que muda para a equipe funcionar |
|---|---|
| **Conta** (`auth.py`) | Situação da conta conferida em toda sessão; `ultima_atividade`; serviço para a equipe encerrar sessões, reenviar verificação e suspender; o cliente vê no Portal quando a equipe encerrou uma sessão dele. |
| **Assinatura** (`billing.py`) | Todas as ações viram serviço com `ator`; a equipe ganha "trocar plano a pedido" (inclusive descer de plano, que hoje só existe "fale com a equipe"); suspender e reativar assinatura; cada mudança entra em `historico_conta`. |
| **Webhook do Asaas** | Passa a usar o mesmo serviço com `ator = sistema`; uma cobrança que falha vira alerta no Painel. |
| **Reembolso** | Sai o estorno na hora; entra o pedido em análise (seção 5). |
| **Plugin** (`plugin.py`) | `resumo_de_uso` já existe; a equipe lê pelo serviço, e o Suporte recebe só o resumo (sem número de perguntas, decisão do suporte.md). |
| **Contato empresarial** (`contato.py`) | As mensagens gravadas viram uma lista "Interessados no Empresarial" no admin. |
| **Novidades** | Saem de `src/data/novidades.ts` para `avisos_portal`, com `GET /avisos` público para o Portal. |
| **Portal** (`/conta/suporte`) | "Seus chamados": lista, conversa e formulário (suporte.md, seção 3). |
| **Portal** (`/conta/plano`) | Trilha do reembolso com "Em análise", prazo e resultado; texto do pop-up muda para "pedido" em vez de "devolvido na hora". |
| **Portal** (geral) | Aviso de conta suspensa no lugar do conteúdo, com o motivo e como falar com a equipe. |

## 5. O reembolso como pedido

1. `POST /billing/assinatura/reembolso` passa a criar o pedido (`pedidos_reembolso`, situação `em_analise`), guardar o
   questionário e a foto de uso, e suspender o acesso. Nada é estornado.
2. Responde 202 com o prazo da análise; o Portal mostra a trilha.
3. A equipe aprova (serviço chama o estorno no Asaas, cancela a assinatura, avisa o cliente) ou recusa (motivo de
   lista fechada, acesso volta, aviso ao cliente).
4. A rotina diária aprova sozinha o que passou de 2 dias úteis sem decisão (`ator = sistema`, motivo "aprovado por
   prazo").
5. O teste atual `test_reembolso_dentro_de_7_dias` muda de "estornou" para "pedido criado"; os de pedidos simultâneos
   continuam.

## 6. Rotinas agendadas

Um processo separado, `python -m app.rotinas`, rodando a cada minuto no servidor (ou o agendador do sistema), com uma
trava no banco para nunca rodar duas vezes ao mesmo tempo. Cada rotina é idempotente (rodar de novo não repete efeito).

| Rotina | Quando |
|---|---|
| Aprovar reembolsos vencidos | A cada hora |
| Fechar chamados "aguardando cliente" há 7 dias | Diária |
| Enviar a fila de e-mail e repetir as falhas | A cada minuto |
| Contar usuários online (para o gráfico de 24 h) | A cada 5 minutos |
| Resumo diário do suporte às 9h | Diária, dias úteis |
| Limpeza: sessões e desafios vencidos (S12), auditoria com mais de 5 anos, contagens de online com mais de 90 dias | Diária |

## 7. E-mail

- **Saída:** tudo passa por `emails_saida`; o envio de verdade é feito pela rotina, com até 5 tentativas. Os e-mails
  de código (2FA) continuam saindo na hora (não podem esperar a fila), mas também ficam registrados.
- **Modelos** em `api/app/emails/`: código, troca de e-mail, resposta de chamado, chamado resolvido, reembolso em
  análise, aprovado, recusado, conta suspensa. Texto do cliente sempre escapado.
- **Entrada** (chamados por e-mail): a decidir entre IMAP e encaminhamento do provedor (suporte.md, seção 12).

## 8. Três origens e três cookies

| Origem | Cookie | Rotas aceitas |
|---|---|---|
| Site (`<domínio>`) | `orbita_sessao` | `/auth`, `/billing`, `/plugin`, `/alertas`, `/contato`, `/suporte`, `/avisos` |
| `suporte.<domínio>` | `__Host-orbita_suporte` | `/equipe/...` (papéis Suporte, Financeiro, Admin) |
| `admin.<domínio>` | `__Host-orbita_admin` | `/equipe/...` (só Admin) |

- `CORS` e `ConfereOrigem` passam de uma origem para uma lista por grupo de rotas: as rotas do cliente só aceitam o
  site; as da equipe só aceitam `suporte.` e `admin.`.
- A dependência `equipe_logada(papeis=...)` lê o cookie da área de onde veio o pedido e confere o papel; a sessão de
  uma área não vale na outra.
- Configuração nova (`api/.env` e `problemas_de_producao`): `SUPORTE_URL`, `ADMIN_URL`, `EQUIPE_CHAVE_TOTP` (cifra
  do segredo do app autenticador), e a API não sobe em produção com essas faltando ou com `http://`.
- **Decisão pendente** (admin.md, seção 10): a API da equipe no mesmo processo, com rotas presas ao host, ou num
  processo separado. A camada de serviços serve aos dois jeitos.

## 9. O site da equipe

- **Projeto separado** no mesmo repositório: `equipe/` (Astro, sem as páginas públicas), publicado em `suporte.` e
  `admin.`. Assim nenhum código da equipe vai junto com o site público.
- Reaproveita os tokens de cor e fontes (`src/styles/tokens.css`) e o componente de ícones.
- A estrutura de hoje (`src/pages/equipe/`, layout `Equipe.astro`, `src/data/equipe-exemplo.ts`) muda para lá quando
  a construção começar; até lá continua só no `astro dev`.
- CSP própria, sem script de terceiros e sem fontes externas.

## 10. Testes

- Fixtures novas: `sessao_equipe(papel)`, `cliente_com_assinatura`, `pedido_de_reembolso`.
- Os testes atuais das rotas do cliente continuam como estão e garantem que a mudança para serviços não quebrou nada.
- Cada serviço ganha teste próprio, chamado direto, com `ator` cliente, equipe e sistema.
- Teste de que **nenhuma** rota `/equipe` responde sem sessão da equipe (lista de rotas lida do próprio app, para
  uma rota nova não escapar).

## 11. Ordem da preparação

Cada passo é um commit testado; nenhum muda o que o cliente vê, exceto o 6.

1. Migrações numeradas e WAL no SQLite.
2. Camada de serviços para `billing` (com `ator`), sem mudar as rotas.
3. Camada de serviços para `auth` e `plugin`; situação da conta e `ultima_atividade`.
4. `historico_conta` e o serviço de auditoria (ainda sem a equipe gravar nada).
5. Fila de e-mail e o processo de rotinas (começando pela limpeza do S12).
6. Reembolso como pedido (muda o Portal e o pop-up).
7. Origens, cookies e `equipe_logada`; só então o login da equipe (admin.md, seção 9, passo 1).

## 12. Para decidir

- API da equipe no mesmo processo ou separado (seção 8).
- Se a suspensão da conta também cancela a cobrança no Asaas ou só bloqueia o acesso.
- Onde roda o processo de rotinas em produção (depende da hospedagem).
- Quando trocar o SQLite pelo PostgreSQL (antes ou depois de ligar a área da equipe).
