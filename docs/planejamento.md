# Órbita: planejamento das próximas frentes

Atualizado em 24/11/2026. Seis frentes discutidas com o Gabriel. Cada uma traz o que foi decidido, o que a pesquisa mostrou e o que falta decidir. As subtarefas estão em `docs/etapas.json` e no painel de progresso.

## Decisões desta rodada

| Assunto | Decisão |
| --- | --- |
| Formato do plugin | Servidor MCP remoto na nossa API (Python/FastAPI), com login OAuth ligado à assinatura, mais skills. Publicado na loja do Claude como plugin. |
| IAs cobertas | Claude, ChatGPT, Microsoft Copilot e Gemini. Tutorial próprio para cada uma, e as quatro aparecem na landing com animação. |
| Onde fica o backend | Pasta `api/` neste repositório por enquanto. Na publicação, vai para o servidor. |
| Novidades | Painel de administração na API para a equipe publicar. **Observação:** ainda não se sabe se esse painel será integrado; enquanto isso, fica planejado e não construído. |
| Pro x Max | Além do limite de consultas, o Max tem alertas por tema, resumo semanal por área, acesso antecipado e suporte prioritário. |
| Asaas | **Integração real suspensa:** ainda não há CNPJ. Será feita uma simulação fiel da API do Asaas no backend, para trocar pela real depois. |
| Formas de pagamento | Cartão, Pix e boleto em todas as páginas que falam de pagamento. |
| Liberação do acesso | Só depois da confirmação do pagamento (webhook do Asaas). Enquanto não houver Asaas, a confirmação é simulada. |
| Animação da explosão do átomo | Toca uma vez, quando o pagamento é confirmado, com botão Pular, e termina no Portal. |
| Cartão: página do Asaas ou formulário próprio | **Em aberto.** O Asaas está interrompido no momento; decidir quando ele voltar. A recomendação é a página segura do Asaas, para o número do cartão não passar pelo nosso servidor (escopo PCI). |
| Conta de revisão das lojas (sem MFA) | **Só documentado, não executar sem ordem direta do Gabriel.** Ideia: uma conta específica, marcada no banco, com assinatura de teste, que entra só com senha, só lê e é desligada depois da aprovação. Alternativa: código fixo informado aos revisores. |
| Repositório do plugin | Repositório público só do plugin (skills, `.mcp.json` com a nossa URL, README e licença). Servidor e base jurídica continuam privados. |
| Por onde começar | Pagamentos e área do assinante: API em `api/` com a simulação do Asaas, Checkout com cartão, Pix e boleto, liberação após confirmação, abas novas do Portal e, por fim, a animação da explosão. |

## 1. Entrega do plugin

Fluxo do cliente: assina no site, recebe acesso, instala o plugin pela loja da IA que usa, entra com a conta da Órbita (OAuth) e a nossa API confere a assinatura a cada consulta. A listagem na loja é pública; quem não assina vê a tela de login e um convite para assinar.

O que já se sabe da loja do Claude: a submissão é pelo portal de diretório do Claude (claude.ai/directory/manage, segundo o repositório oficial de plugins da Anthropic), aberta a contas de planos pagos. Aceita um servidor MCP remoto como conector ou um pacote de plugin (MCP + skills) hospedado no GitHub. Depois de aprovado, há acompanhamento da revisão e números de uso.

_Detalhes de requisitos e materiais: ver a seção "Pesquisa: loja do Claude e outras IAs" no fim._

### Servidor MCP: fora do escopo do site (decisão de 25/11/2026)

O servidor MCP com a base jurídica já existe e vai ser ligado depois. **Nada a construir agora.** O site não depende dele: conta, login, Checkout, cobrança e Portal funcionam sem ele. Ele só entra em ação quando o cliente pergunta dentro da IA.

- **Plugin:** o pacote que o cliente instala (skills e o endereço do servidor MCP). Pode ser público.
- **Servidor MCP:** recebe as perguntas, confere o login e a assinatura e pesquisa na base. Fica no nosso servidor.
- **O que se vende:** a assinatura (o acesso), não o arquivo do plugin.

**Lugares do site que esperam o servidor** (todos marcados "a definir" na tela e funcionando em demonstração):

| Onde | O que espera | Hoje |
| --- | --- | --- |
| Instalar: "Baixar o plugin" (`src/pages/instalar.astro`) | O arquivo do plugin e a versão atual | Simula o download |
| Instalar: "Gerar código de conexão" | Código para ligar a conta Órbita à IA (ou o login OAuth do próprio servidor) | Código de demonstração |
| Portal, Status do plugin (`src/pages/conta.astro`) | Consultas do mês, limite do plano, última consulta, versão do plugin | "0", "Nenhuma ainda" e "a definir" |
| Portal: conexões e Tutoriais (`src/data/tutoriais.ts`) | Se a IA está conectada; endereço do servidor para ChatGPT, Copilot e Gemini | Passos marcados no Instalar; outras IAs "em preparação" |

**Na hora de ligar:**

1. O login do servidor usa a conta da Órbita: a sessão e as rotas de `/auth`.
2. A cada consulta, o servidor confere a assinatura: `tem_acesso` em `GET /billing/assinatura`, ou uma rota interna equivalente.
3. A contagem de consultas alimenta o Portal.
4. O pacote do plugin aponta para o endereço do servidor e vai para o repositório público.

## 2. Área do assinante

Nova parte inteira no perfil logado, pensada para o serviço como empresa, não só para o plugin:

| Aba | O que mostra | Pro | Max |
| --- | --- | --- | --- |
| Status do plugin | Conexão por IA, última consulta, uso do mês contra o limite, versão do plugin e das bases | Sim | Sim |
| Novidades | Atualizações nossas (bases novas, melhorias) e mudanças do Claude e das outras IAs que afetam plugins | Sim | Sim, com itens de acesso antecipado marcados |
| Tutoriais | Instalação e uso em Claude, ChatGPT, Copilot e Gemini, um tutorial por IA | Sim | Sim |
| Alertas por tema | Temas salvos (ex.: ICMS-ST, PIS/Cofins) e avisos de julgado ou norma nova | Não | Sim |
| Resumo semanal | Decisões e normas da semana nas áreas escolhidas, na página e por e-mail | Não | Sim |
| Assinatura e pagamento | Plano, forma de pagamento (cartão, Pix, boleto), faturas, notas, troca de plano, cancelamento e reembolso | Sim | Sim |
| Suporte | Canal, prazo e histórico de chamados | Prazo padrão | Prioritário, com conversa de implantação |

Ideias para um serviço mais premium (para discutir):

- Biblioteca pessoal: citações e pesquisas salvas, com a fonte, para reaproveitar em peças.
- Modelos de peças e roteiros de pesquisa prontos por tema, mantidos pela equipe.
- Painel de uso com o tempo economizado estimado, útil para justificar o custo ao escritório.
- Indicação com crédito: um mês grátis para quem indica e para o indicado.
- Status público do serviço (página de disponibilidade da API e das bases).
- Webinars curtos mensais sobre novidades tributárias e uso do plugin.
- Plano para equipes (já previsto depois do MVP), com assentos e cobrança única.

## 3. Asaas

Integração real suspensa até haver CNPJ. Enquanto isso, a API ganha uma simulação com os mesmos endpoints, campos, status e webhooks do Asaas, ligada ao Checkout e ao Portal, para trocar pela real mudando só a URL e a chave.

_Mapa completo da plataforma: ver a seção "Pesquisa: Asaas" no fim._

## 4. Cartão, Pix e boleto

Páginas que mudam: Checkout (nova opção Boleto, com linha digitável, PDF e vencimento), Portal (forma de pagamento e faturas com as três), landing (rodapé dos planos), Ajuda (artigo de cobrança), Termos e Reembolso (prazos de compensação e estorno por forma de pagamento), e o fluxo de confirmação (acesso só depois de pago).

## 5. Ranqueamento no Google

_Ver a seção "Pesquisa: SEO" no fim._

## 6. Reformular a landing para vender (pedido de 25/11/2026)

Objetivo: a landing passa a ser uma página de vendas. Toda decisão de design responde a uma pergunta: isso ajuda a vender a assinatura? Menos efeito e mais argumento. Etapas, uma por vez, cada uma testada e aprovada antes da próxima:

| Etapa | O que é |
| --- | --- |
| 10a | **Pesquisa aprofundada:** o que é uma landing page de vendas e o que ela precisa ter para converter. Estrutura, ordem das seções, título, prova, preço, garantia, chamadas para ação, objeções e o que atrapalha. Com fontes. Sai num relatório. |
| 10b | **Plano da nova landing,** a partir da pesquisa: ordem das seções e o papel de cada uma. É aprovado antes de mexer no código. |
| 10c | **Tirar os efeitos visuais desnecessários do site inteiro,** inclusive os da parte principal (topo). Menos "vida": movimento só onde ajuda a entender ou a vender. |
| 10d | **Tirar o carrossel vertical e resumir tudo numa linha só.** |
| 10e | **Exemplos como respostas reais do Claude Opus 5.5,** tiradas do artefato de exemplos, com a **comparação com e sem o plugin**, igual ao artefato. |
| 10f | **Reformular o visual** para vender o máximo: chamadas para ação, prova, preço e garantia em destaque, seguindo o plano da 10b. |

A animação da explosão continua sendo a última etapa do projeto, depois da 10f.

## 7. Animação da explosão do átomo

Quando o pagamento é confirmado, o átomo da marca cresce no centro da tela, o núcleo pulsa, os anéis se rompem e os elétrons saem em órbitas largas. Cada elétron vira o cartão de uma página nova (Status do plugin, Novidades, Tutoriais, Assinatura, Suporte e, no Max, Alertas e Resumo semanal), que voa até o lugar dela no Portal. Toca uma vez, com Pular, e respeita movimento reduzido (sem explosão: o Portal aparece com um destaque nas abas novas).

---

# Pesquisas desta rodada (24/11/2026)

Legenda: **[a conferir]** marca o que não foi confirmado em fonte oficial ou em que as fontes divergem.

## Pesquisa: loja do Claude e outras IAs

### Claude

- **Onde submeter:** claude.ai/directory/manage, em "Submit new". A recomendação oficial é fazer **duas submissões** da mesma organização, que ficam pareadas. Fonte: https://claude.com/docs/directory/publish
  - **MCP connector:** o servidor. Dá a listagem, o painel de saúde, o uso por ferramenta e a configuração de login.
  - **Plugin bundle:** as skills, apontando para a mesma URL do conector. Skills não podem ser submetidas sozinhas.
- **Quem submete:** a pessoa com papel Owner, numa conta paga (Pro, Max, Ultra, Team ou Enterprise). Não há programa de parceiros. A listagem pertence à organização que submeteu, então é preciso submeter já pela conta definitiva da empresa.
- **Regras do conector:** https://claude.com/docs/connectors/building/review-criteria
  - URL https pública, num domínio da própria Órbita (ex.: mcp.orbitafiscal.com.br).
  - Toda ferramenta com `title` e `readOnlyHint: true` (pesquisa é leitura). Nome com até 64 caracteres.
  - Nenhuma ferramenta que misture leitura e escrita. Descrições sem instruções ao modelo e sem propaganda.
  - Erros claros: um "Internal Server Error" genérico reprova.
  - Não coletar dados da conversa além do necessário.
- **Login (OAuth):** https://claude.com/docs/connectors/building/authentication
  - O servidor responde 401 com `WWW-Authenticate` apontando para `/.well-known/oauth-protected-resource`.
  - PKCE S256 obrigatório; refresh token com rotação.
  - Registro de cliente por CIMD ou DCR, ou cliente confidencial cadastrado no portal.
  - Endereços de retorno (redirect): `https://claude.ai/api/mcp/auth_callback` e loopback com qualquer porta, para o Claude Code.
  - A assinatura é conferida na emissão do token e em cada chamada. Assinatura vencida responde 401 ou 403 com mensagem clara.
- **Plugin:** lido de um repositório no GitHub (`.claude-plugin/plugin.json`, README, LICENSE, `skills/`, `.mcp.json`).
  - Pode ficar privado durante a validação, mas **precisa ser público** para entrar no ar.
  - Validar com `claude plugin validate`.
  - Atualizações chegam a cada push.
  - Fonte: https://claude.com/docs/plugins/submit
- **Revisão:**
  - O conector passa por varredura automática e entra como "Community". A Anthropic pode escalar para "Verified", com teste humano e pedido de conta de teste.
  - O plugin tem revisão humana na primeira listagem.
  - Não há prazo fixo; depende da fila.
- **Cobrança:** nada proíbe exigir assinatura externa; o portal até pergunta o que o usuário precisa antes de conectar. São proibidos anúncios e mover dinheiro. [a conferir] Não há regra explícita sobre upsell; o prudente é não pôr link de compra nas respostas.
- **Quem pode usar:** custom connectors existem em todos os planos do Claude (o Free fica limitado a 1). Valem na web, no Desktop, no mobile, no Cowork e no Claude Code. [a conferir] Quais planos instalam pelo diretório.

**Materiais a preparar para submeter:**
1. Conta paga com papel Owner na organização definitiva.
2. Servidor MCP em https estável, no domínio da Órbita.
3. OAuth conforme acima.
4. Ferramentas anotadas e testadas no MCP Inspector e como custom connector.
5. Textos da listagem: nome, frase de até 200 caracteres, descrição de até 2.000 caracteres e categorias.
6. Ícone.
7. Slug definitivo, que não muda depois de publicado.
8. Documentação pública.
9. Política de privacidade e termos.
10. Contato de suporte.
11. Dados da empresa.
12. Pré-requisito declarado: assinatura ativa.
13. Conta de teste com assinatura ativa, sem MFA.
14. Repositório público do plugin.

### ChatGPT

- **Como o usuário conecta:** Plugins → "+" → "Add custom MCP server". Só no ChatGPT web.
  - Business, Enterprise e Edu: leitura e escrita.
  - Pro: só leitura.
  - [a conferir] Plus e Free.
  - Fonte: https://help.openai.com/en/articles/12584461
- **Diretório público:** há submissões abertas.
  - Exige verificação de domínio em `/.well-known/openai-apps-challenge`.
  - Exige URLs de site, suporte, privacidade e termos, e um ícone.
  - A revisão pede casos de teste positivos e negativos, vídeo e conta demo sem MFA.
  - Fonte: https://developers.openai.com/apps-sdk/deploy/submission
- **Monetização:** o usuário pode entrar com a conta paga que já tem. É **proibido vender ou mostrar planos dentro do app**: só dá para explicar a limitação e levar a uma página informativa.

### Microsoft Copilot

- **Copilot Studio:** Agente → Tools → Model Context Protocol, com OAuth (descoberta dinâmica ou manual). Só Streamable HTTP. Fonte: https://learn.microsoft.com/microsoft-copilot-studio/mcp-add-existing-server-to-agent
- **Microsoft 365 Copilot:** o registro de cliente precisa **emitir client_secret** (cliente confidencial).
- **Licença para usar:** Microsoft 365 Copilot, ou Copilot Chat com cobrança por uso.
- **Quem configura:** normalmente o TI do cliente cria o agente e o publica no tenant. O tutorial precisa falar com o TI.

### Gemini

- **Gemini Enterprise:** tem conector "Custom MCP Server", configurado pelo admin no Console do Google Cloud. Redirect: `https://vertexaisearch.cloud.google.com/oauth-redirect`.
- **Gemini CLI:** aceita MCP remoto com OAuth automático.
- **App Gemini para o usuário final:** só via "Connected Apps Platform", com acesso por formulário e revisão. Fonte: https://developers.google.com/connected-apps/mcp
- [a conferir] Se o usuário comum pode colar a URL de um MCP próprio no app Gemini (as fontes divergem).

### O que isso muda no servidor (API FastAPI)

- Streamable HTTP, PKCE S256 e metadados de OAuth (RFC 9728 e 8414).
- Registro de cliente por DCR que emita client_secret quando pedido (exigência da Microsoft) e por CIMD (Claude e OpenAI).
- Lista de redirects do Claude, do loopback, do Google e os que OpenAI e Microsoft exibirem no cadastro.
- `readOnlyHint` e `openWorldHint` em todas as ferramentas.
- Conta demo sem MFA. Isso conflita com a nossa verificação em duas etapas: é preciso um modo de revisão para essa conta.
- Endpoint de verificação de domínio da OpenAI.
- Nenhum link de compra dentro das respostas.

## Pesquisa: Asaas

Mapa para a simulação seguir o formato real. Índice da documentação: https://docs.asaas.com/llms.txt

- **Ambientes e autenticação:**
  - Sandbox `https://api-sandbox.asaas.com/v3`; produção `https://api.asaas.com/v3`.
  - Header `access_token` sem "Bearer"; chaves `$aact_hmlg_` (sandbox) e `$aact_prod_` (produção). `User-Agent` obrigatório.
- **Erros e limites:**
  - Formato `{"errors":[{"code","description"}]}`.
  - Paginação por `offset` e `limit` (máximo 100), com `hasMore` e `totalCount`.
  - Limite: HTTP 429, com 25.000 requisições a cada 12 h.
- **Clientes:** `POST /v3/customers`, com `name` e `cpfCnpj` obrigatórios. Ids no formato `cus_...`.
- **Assinaturas:**
  - Criar: `POST /v3/subscriptions` com `customer`, `billingType` (`CREDIT_CARD|PIX|BOLETO|UNDEFINED`), `value`, `nextDueDate` e `cycle: MONTHLY`. Ids no formato `sub_...`.
  - Trocar a forma de pagamento: `PUT /v3/subscriptions/{id}` com outro `billingType`.
  - Trocar só o cartão: `POST /v3/subscriptions/{id}/updateCreditCard`.
  - Cancelar: `DELETE /v3/subscriptions/{id}`.
  - Cada cobrança nasce 40 dias antes do vencimento (configurável).
- **Cobranças:**
  - `POST /v3/payments`, com ids no formato `pay_...`.
  - Status: `PENDING`, `CONFIRMED`, `RECEIVED`, `OVERDUE`, `REFUNDED`, `REFUND_REQUESTED`, `REFUND_IN_PROGRESS`, `CHARGEBACK_*`, `AWAITING_RISK_ANALYSIS` e outros.
  - Campos úteis: `invoiceUrl`, `bankSlipUrl`, `transactionReceiptUrl`.
- **Boleto:** `GET /v3/payments/{id}/identificationField` devolve a linha digitável, o código de barras e o nosso número.
- **Pix:** `GET /v3/payments/{id}/pixQrCode` devolve `encodedImage`, `payload` (copia e cola) e `expirationDate`.
- **Cartão:**
  - Envia `creditCard`, `creditCardHolderInfo` e `remoteIp`. Aprovado: 200 e `PAYMENT_CONFIRMED`. Recusado: 400 `invalid_creditCard`.
  - Tokenização: `POST /v3/creditCard/tokenizeCreditCard`. Em produção, precisa ser liberada pelo suporte.
- **Estorno:** `POST /v3/payments/{id}/refund`, total ou parcial. No cartão leva até 10 dias úteis para aparecer na fatura. As taxas não voltam.
- **Pix Automático:** autorização com `paymentCreationMode: SUBSCRIPTION`; na assinatura, `pixAutomaticAuthorizationMode`.
- **Checkout hospedado:** `POST /v3/checkouts` aceita cartão e Pix (boleto não), com cobrança recorrente.
- **Nota fiscal (NFS-e):** `POST /v3/invoices`, integrada ao Asaas, depende das configurações fiscais da conta.
- **Webhooks:**
  - Cadastro em `POST /v3/webhooks` (até 10 por conta). Header `asaas-access-token` para autenticar.
  - O Asaas só considera sucesso a resposta HTTP 200. Depois de 15 falhas seguidas, a fila pausa; os eventos ficam guardados por 14 dias.
  - Entrega "pelo menos uma vez": deduplicar pelo `id` do evento.
- **Liberar e cortar o acesso:**
  - Liberar: cartão com `PAYMENT_CONFIRMED`; Pix e boleto com `PAYMENT_RECEIVED`. O que chegar primeiro libera.
  - Nunca liberar com `PAYMENT_CREATED` ou com o redirecionamento de sucesso.
  - Cortar: `PAYMENT_OVERDUE` (com carência), `PAYMENT_REFUNDED`, `PAYMENT_CHARGEBACK_REQUESTED`, `PAYMENT_REPROVED_BY_RISK_ANALYSIS`, `SUBSCRIPTION_DELETED`.
- **Testes no sandbox:**
  - Cartão aprovado `4444 4444 4444 4444` (CVV 123).
  - Cartões recusados `5184019740373151` e `4916561358240741`.
  - Confirmar Pix ou boleto: `POST /v3/sandbox/payment/{id}/confirm`.
- **Segurança:** para o número do cartão nunca passar pelo nosso servidor (escopo PCI), o recomendado é usar a página do Asaas (`invoiceUrl` ou Checkout) no cartão.
- **Taxas:** Pix e boleto aparecem a R$ 1,08 ou R$ 2,15 por transação recebida. [a conferir] Taxa do cartão de crédito e prazo de recebimento.
- **Conta de produção:** passa por validação cadastral. [a conferir] O Asaas aceita CPF ou CNPJ; a decisão de esperar o CNPJ é da empresa.

## Pesquisa: SEO

Feita sem navegação ao vivo. Os itens [a conferir] devem ser checados na URL indicada antes da publicação.

**No Google e no Bing**
- **Search Console:**
  - Propriedade "Domínio" verificada por registro TXT no DNS; não apagar o TXT depois.
  - Mais de um proprietário.
  - Enviar `sitemap-index.xml`.
  - Inspecionar as páginas principais e pedir indexação.
  - Fonte: https://support.google.com/webmasters/answer/9008080
- **Google Business Profile:** não se aplica a um SaaS 100% online. Fonte: https://support.google.com/business/answer/3038177
- **GA4, Tag Manager e consentimento:**
  - Consent Mode v2 com padrão "negado".
  - Banner LGPD com "Rejeitar" tão visível quanto "Aceitar", seguindo o guia de cookies da ANPD.
  - Nada de dados pessoais no GA4.
  - Medir início de checkout, assinatura, cadastro e instalação.
- **Bing Webmaster Tools:** importar do Search Console e ativar o IndexNow. O Bing alimenta o Copilot e parte do ChatGPT Search.

**No código Astro**
- `@astrojs/sitemap` filtrando /conta, /instalar e /assinar.
- `robots.txt` liberando tudo e apontando o sitemap. Não bloquear a área logada por robots: usar **noindex** (header `X-Robots-Tag` no middleware), senão o Google não lê o noindex.
- Canonical absoluto e uma só versão do domínio (sem www, com 301). `lang="pt-BR"`; hreflang não é necessário.
- Title e description únicos por página; favicon com no mínimo 48 px.
- Open Graph com imagem de 1200x630, decisivo no WhatsApp e no LinkedIn.
- **Dados estruturados:**
  - Organization (logo, sameAs, CNPJ), WebSite (nome do site), SoftwareApplication com Offer em BRL, BreadcrumbList e Article nas novidades e tutoriais.
  - FAQ não gera rich result para SaaS desde 2023, e HowTo foi descontinuado.
  - Validar no Rich Results Test.
- **404 real** (status 404, não página de erro com status 200).
- **Core Web Vitals:** LCP ≤ 2,5 s, INP ≤ 200 ms, CLS ≤ 0,1.
  - O que mais pesa aqui: o título do topo entra animado (opacity 0 atrasa o LCP); GSAP e Lenis ocupam a thread principal; imagens sem width e height.
  - Ação: o elemento de LCP aparece sem animação de entrada.
- **Imagens:** AVIF ou WebP com `<Picture>`, alt descritivo e fotos baixadas para o próprio site.
- **Fontes:** woff2 auto-hospedadas com acentos, `font-display: swap` e fallback ajustado.

**Respostas de IA (AI Overviews, ChatGPT, Perplexity)**
- O Google diz que não há otimização especial: valem as mesmas práticas. Fonte: https://developers.google.com/search/docs/appearance/ai-features
- O `llms.txt` não é usado pelo Google. [a conferir em 2026]
- Liberar OAI-SearchBot, PerplexityBot, Claude-SearchBot e Bingbot, e conferir se a CDN não os bloqueia.
- Páginas que respondem perguntas específicas, com data e fonte, são as mais citadas. Os tutoriais por IA são exatamente esse tipo.

**Conteúdo e autoridade (tema jurídico, YMYL)**
- Página Sobre com autores qualificados (OAB e CRC), "revisado por" e datas.
- Fonte primária com link; CNPJ e contato no rodapé.
- Aviso de que a ferramenta não substitui parecer.
- **Conteúdo com demanda:**
  - Guias da Reforma Tributária.
  - Páginas tema → precedentes do STF e do STJ.
  - Súmulas do CARF e soluções de consulta da COSIT.
  - Obrigações acessórias.
  - Tutoriais por IA.
- **Cuidados:**
  - Revisão humana de cada conteúdo.
  - Nada de jurisprudência inventada ou ementas copiadas em massa.
  - Respeitar o Provimento 205/2021 da OAB.
  - Nunca comprar links.

**Lista do dia da publicação:** está no fim do relatório original. Os itens viraram subtarefas da etapa "Ranqueamento no Google" no painel.
