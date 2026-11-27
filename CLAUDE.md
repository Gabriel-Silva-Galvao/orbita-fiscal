# Órbita: contexto do projeto

Este arquivo é lido automaticamente no começo de toda conversa sobre o projeto. Ele diz o que é a Órbita, como
trabalhar aqui e em que ponto o projeto está. **Mantenha-o atualizado** (seção "Manter este arquivo").

Última atualização: 27/11/2026 (commit `c711188`).

---

## 1. O que é

- **Órbita:** plugin que liga a IA do cliente (Claude, ChatGPT, Copilot, Gemini) a uma base de legislação e
  jurisprudência brasileira, sempre com a fonte. Público: advogados, contadores e empresários.
- **Este repositório:** o site de vendas, o Checkout, o Portal do assinante e a API de conta e cobrança.
- **O servidor MCP do plugin já existe em outro lugar e não é construído aqui;** aqui só se documenta e se integra
  (rota `POST /plugin/uso`).
- Planos: Bronze, Prata e Ouro (mensais; Pix, boleto e cartão) e Empresarial (sob consulta).
- Marca: só "Órbita". Domínio `orbitafiscal.com.br`, e-mails e @orbitafiscal são provisórios até comprar o domínio.

## 2. Pilha e como rodar

- **Site:** Astro 7 (páginas públicas estáticas; Portal e Checkout no servidor Node), ilhas React só quando
  preciso, GSAP e Lenis no movimento. Pastas: `src/pages`, `src/components`, `src/layouts`, `src/scripts`, `src/data`.
- **API:** Python + FastAPI em `api/`, SQLite em modo WAL. Mudança no banco = nova migração numerada em
  `api/app/migracoes.py` (nunca editar uma publicada). Regra de negócio nova vai para `api/app/servicos/` (sem FastAPI,
  recebendo o `Ator` de `servicos/base.py`); as rotas só validam a entrada e chamam o serviço. Toda regra de negócio fica na API; o Astro só protege rotas
  (`src/middleware.ts`) e repassa.
- **Cobrança:** Asaas. Hoje roda a **simulação local** (`api/app/asaas_sim`), guardada em `api/orbita-dev-asaas-sim.json`.
- **Rodar:** pelo `.claude/launch.json`, iniciar **"api"** e **"site-com-api"** (o "site" sozinho é modo
  demonstração, sem API). Site em http://localhost:4321, API em http://localhost:8000. Depois de mexer na API,
  reiniciar o "api".
- **Conta de teste:** `fetch` em `/auth/cadastro` e `/auth/codigo` (o `codigo_dev` vem na resposta no
  desenvolvimento); `POST /billing/assinatura` com Pix e `POST /billing/assinatura/simular-pagamento`.
- **Testes da API** (152 passando): em `api/`,
  `.venv/Scripts/python -m pytest -q -p no:cacheprovider --basetemp="$TEMP/orbita-pt-$RANDOM$RANDOM" -W ignore`
  (sempre um `basetemp` novo; reaproveitar dá erro no Windows).
- **Testes do site:** `npm run test:site`.
- Estilos com escopo do Astro não pegam em elementos criados por JS: use `:global()`.
- Edições longas: script Python no scratchpad (heredoc com crase falha no bash).

## 3. Como trabalhar aqui (regras do usuário)

1. **Responder em português.**
2. **Um item por vez**, testado, e esperar o ok antes do próximo.
3. **Perguntar antes de todo commit e de todo push.** Antes de commitar: `git pull --rebase`.
4. **Em todo commit:** atualizar e republicar o guia interativo `docs/guia-de-uso.html`
   (https://claude.ai/artifact/7dMuyNgvf4dLt8BdcprgXp) e commitá-lo junto.
5. Commit termina com `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
6. **Nunca** digitar senhas ou chaves, nem colocar segredo no git ou no chat. A chave do Asaas fica só em `api/.env`.
7. **Dependência nova só com aprovação do usuário.**
8. Depoimentos só reais e autorizados. Não chamar rotas não documentadas de servidores com tokens.
9. Conta de revisão das lojas: só documentada, não executar sem ordem direta.
10. **A animação da explosão do átomo é a última etapa de todo o projeto.**

## 4. Segurança em toda funcionalidade nova

- Antes de construir, passe pelo checklist de `docs/ciberseguranca.md`, seção 0.1.
- Riscos que a funcionalidade traz e que não forem resolvidos na hora entram em `docs/seguranca/registro.json`
  (situação `futura` ou `observacao`) no mesmo commit.
- Vulnerabilidade encontrada ou corrigida: atualize a ficha no `registro.json` (situação, teste, commit), a seção 5.1
  de `docs/ciberseguranca.md` e republique o painel `docs/seguranca/painel.html` no mesmo link
  (https://claude.ai/artifact/HPpHTMdkdzKGD2T5Xr41d6), publicando o `registro.json` junto como `registro.json`.
- Toda correção de segurança tem teste de regressão e commit próprio.

## 5. Estado atual

**Pronto e funcionando (local, com a simulação do Asaas)**
- Site: landing, `/planos` (comparação antes do Empresarial), `/bases`, `/ajuda`, `/empresas`, textos legais
  (rascunho), 404. Header só com logo, Entrar e Assinar; barra de seções ao rolar; caminho ("Órbita › …") no topo.
- Conta: cadastro e login com código por e-mail, troca de senha e de e-mail, aparelhos conectados.
- Checkout e Portal (`/conta/*`, 7 páginas): plano e pagamento (Pix, boleto; trocar forma; upgrade; cancelar;
  reembolso em dois pop-ups com questionário opcional), plugin e conexões, alertas e resumo (Ouro), novidades,
  suporte, conta e segurança.
- Plugin: download de demonstração, status ativo/inativo, contagem de perguntas por IA e downloads; cada reembolso
  grava a foto de uso do plugin.
- Segurança: fase encerrada em 27/11/2026 (`docs/ciberseguranca.md`, seção 8). 63 fichas no registro.

**Planejado, não construído**
- Suporte e administração: planos em `docs/suporte.md` e `docs/admin.md`; estrutura das telas para discussão em
  `/equipe` (só no `astro dev`, 404 em produção). Decisões: subdomínios `admin.` e `suporte.`, app autenticador
  para a equipe, sem "entrar como o cliente", auditoria por 5 anos, chamados próprios pelo Portal e por e-mail,
  reembolso aprovado pela equipe.

**Próximo passo:** preparar o app atual para a equipe, na ordem de `docs/preparacao-suporte-admin.md`, seção 11.
Feito: passos 1 (migrações numeradas e WAL), 2 (cobrança em `api/app/servicos/assinaturas.py`, com `Ator`) e 3
(conta e plugin em `servicos/contas.py` e `servicos/plugin.py`; conta pode ser suspensa; `ultima_atividade`).
Próximo: passo 4 (histórico da conta e serviço de auditoria); depois fila de e-mail e rotinas, reembolso como pedido,
origens e cookies. Depois, o login da equipe (`docs/admin.md`, seção 9).

**Pendências que dependem de terceiros ou de decisão**
- Sandbox do Asaas (item 29) e o resto do item 37; cartão por página ou tokenização do Asaas (S3).
- Decisões da seção 4.2 de `docs/ciberseguranca.md`: cobrança do upgrade, 409 do cadastro, reembolso depois de
  cancelar, proxy de produção.
- Domínio, hospedagem, SMTP, revisão jurídica dos textos, item 28 (avaliações reais).
- Por último: a animação do átomo.

## 6. Onde está cada coisa

| Arquivo | Para quê |
|---|---|
| `PROGRESSO.md` | Situação das páginas e histórico do que foi feito |
| `docs/rodada-de-testes.md` | Todos os itens pedidos (numerados), com diagnóstico e testes |
| `docs/ciberseguranca.md` | Segurança: sistema, checklist, controles, riscos, correções, encerramento da fase |
| `docs/seguranca/registro.json` e `painel.html` | Registro único de vulnerabilidades e o painel interativo |
| `docs/backend-e-seguranca.md` | Rotas da API e riscos S1 a S18 |
| `docs/suporte.md`, `docs/admin.md`, `docs/suporte-e-admin.md` | Planos do suporte e da administração |
| `docs/preparacao-suporte-admin.md` | O que muda no app atual (API e site) antes de construir suporte e admin |
| `docs/guia-de-uso.html` | Guia interativo de uso e testes (republicado a cada commit) |
| `docs/etapas.json` e `docs/progresso.html` | Etapas do painel de progresso |
| `artefatos/LEIA-ME.md` | Lista dos artefatos publicados no claude.ai |

**Artefatos (claude.ai)**
- Guia de uso: https://claude.ai/artifact/7dMuyNgvf4dLt8BdcprgXp
- Painel de progresso: https://claude.ai/artifact/ExDnSrxKMBgHBUrDG3Xskm (banco: coleções `etapas`, `paginas`,
  `bloqueios`; manter `docs/etapas.json` igual)
- Segurança da Órbita: https://claude.ai/artifact/HPpHTMdkdzKGD2T5Xr41d6
- Vulnerabilidades (histórico da revisão ARES): https://claude.ai/artifact/UqJWvjZsAcGB94uDhCssjD

## 7. Manter este arquivo

Atualize este CLAUDE.md **no mesmo commit** sempre que mudar algo que uma conversa nova precisa saber:

- uma funcionalidade fica pronta ou muda de situação (seção 5);
- o próximo passo muda (seção 5);
- o usuário cria ou muda uma regra de trabalho (seção 3);
- uma decisão de produto, de arquitetura ou de segurança é tomada (seções 1, 2 e 5);
- muda como rodar ou testar o projeto, ou o número de testes (seção 2);
- surge um documento ou artefato novo (seção 6).

Troque também a data e o commit em "Última atualização". Mantenha curto: detalhe vai para `PROGRESSO.md` e `docs/`;
aqui fica só o que orienta o trabalho.
