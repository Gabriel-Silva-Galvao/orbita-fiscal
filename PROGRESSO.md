# Órbita: progresso do site

Atualizado em 24/11/2026. As 7 páginas do MVP existem e o fluxo completo funciona em **modo de demonstração**: nada é cobrado, nenhum e-mail é enviado e a “conta” fica só no navegador. Para ir ao ar, faltam decisões da empresa, a revisão jurídica e a parte de servidor.

Painel interativo (status, bloqueios e etapas editáveis): https://claude.ai/artifact/ExDnSrxKMBgHBUrDG3Xskm (republicado em 24/11/2026 na conta atual; o link antigo não abre mais).

## Situação das páginas

| Página | Rota | Situação | O que falta |
| --- | --- | --- | --- |
| 1. Landing | `/` | Pronta | Revisão jurídica dos exemplos e das 125 citações em revezamento; contatos reais |
| 2. Entrar e criar conta | `/entrar` | Tela pronta, demonstração | Servidor de autenticação (Google ou e-mail e senha + código por e-mail) |
| 3. Checkout | `/assinar/pro`, `/assinar/max` | Tela pronta, demonstração | Provedor de pagamento, campos seguros do cartão, Pix, nota fiscal |
| 4. Instalar o plugin | `/instalar` | Tela pronta, demonstração | Arquivo real do plugin, link expirável, código de conexão real, nomes dos menus do Claude |
| 5. Portal do cliente | `/conta` | Tela pronta, demonstração | Dados reais da assinatura, notas, reembolso e cancelamento pelo provedor |
| 6. Ajuda | `/ajuda` | Pronta | Canal de suporte e prazo de resposta definitivos |
| 7. Textos legais | `/privacidade`, `/termos`, `/reembolso` | Rascunho | Revisão por advogado; razão social, CNPJ, prazos |
| 8. Para equipes | `/equipes` | Depois do MVP | Só depois do fluxo individual no ar |

## Passo a passo

86 de 159 subtarefas feitas. Cada etapa separa o que já foi feito do que falta. O mesmo conteúdo, com caixas que dá para marcar, está no painel interativo. A fonte das etapas é `docs/etapas.json`.

| Etapa | Feito | Situação |
| --- | --- | --- |
| 1. Base do projeto | 7 de 7 | Concluída |
| 2. Landing | 12 de 16 | Em andamento |
| 3. Movimento | 9 de 10 | Em andamento |
| 4. Fotos reais | 4 de 5 | Em andamento |
| 5. Auditoria de traços de IA | 6 de 6 | Concluída |
| 6. Textos legais | 4 de 9 | Em andamento |
| 7. Entrar e criar conta | 7 de 10 | Em andamento |
| 8. Checkout | 6 de 11 | Em andamento |
| 9. Instalar o plugin | 5 de 11 | Em andamento |
| 10. Portal do cliente | 5 de 10 | Em andamento |
| 11. Ajuda | 3 de 4 | Em andamento |
| 12. Arquitetura e servidor | 6 de 9 | Em andamento |
| 13. Artefatos e entregas | 5 de 5 | Concluída |
| 14. Entrega do plugin (loja do Claude e outras IAs) | 2 de 10 | Em andamento |
| 15. Área do assinante | 1 de 8 | Em andamento |
| 16. Pagamentos (Asaas) | 2 de 8 | Em andamento |
| 17. Ranqueamento no Google | 1 de 9 | Em andamento |
| 18. Animação da explosão do átomo | 1 de 3 | Em andamento |
| 19. Publicação | 0 de 6 | Não iniciada |
| 20. Para equipes (depois do MVP) | 0 de 2 | Não iniciada |

### 1. Base do projeto (7 de 7)

**Feito**

- [x] Importar briefings, persona e mapa de páginas
- [x] Importar o design system Limiar Esmeralda
- [x] Criar o projeto em Astro com os tokens da marca
- [x] Temas claro e escuro, com escolha salva
- [x] Fontes Newsreader e Hanken Grotesk servidas pelo site
- [x] Repositório no GitHub (privado)
- [x] Repositório movido para Gabriel-Silva-Galvao/orbita-fiscal

**Falta**

- Nada pendente.

### 2. Landing (12 de 16)

**Feito**

- [x] Cabeçalho com logo, links e botão
- [x] Topo com título, frase de apoio e átomo
- [x] Exemplo em três abas, marcado como ilustrativo
- [x] O dia a dia: texto e moldura fixa que troca de foto
- [x] Como funciona: três passos
- [x] Planos Pro e Max, diferença por tarefa
- [x] Confiança com garantias do CDC e da LGPD
- [x] Dúvidas: perguntas frequentes
- [x] Contato com formulário validado
- [x] Rodapé revelado ao final, com tema e cookies
- [x] Reembolso só em letra miúda abaixo dos planos
- [x] Logo e átomo do topo sem o disco verde

**Falta**

- [ ] Revisão jurídica das 8 citações dos exemplos
- [ ] Revisão jurídica das 125 citações em revezamento
- [ ] Trocar contatos provisórios pelos reais
- [ ] Imagem de compartilhamento (Open Graph)

### 3. Movimento (9 de 10)

**Feito**

- [x] GSAP e ScrollTrigger
- [x] Rolagem suave com Lenis
- [x] Logo com órbita sozinha e no mouse
- [x] Entradas em cascata e títulos palavra por palavra
- [x] Parallax nas cenas com foto
- [x] Página completa e parada com movimento reduzido (no código)
- [x] Cartões de lei em revezamento no topo, nos livros e em Brasília
- [x] Trocas automáticas a cada 6 s: órbita, página e carimbo
- [x] Virada do cartão no hover

**Falta**

- [ ] Conferir na tela com movimento reduzido ativado

### 4. Fotos reais (4 de 5)

**Feito**

- [x] 8 fotos do Unsplash escolhidas pela folha de contato
- [x] Créditos no código e no rodapé
- [x] Foto da base em duotone, sem lente que segue o mouse
- [x] Foto de Brasília que se abre em órbita

**Falta**

- [ ] Baixar as fotos para o próprio site

### 5. Auditoria de traços de IA (6 de 6)

**Feito**

- [x] Instalar 4 skills de auditoria de design
- [x] Relatório com achados e prioridades
- [x] Remover sobretítulos, ícones decorativos e laços de flutuação
- [x] Nada que tenha ação se move sob o cursor; preço fixo
- [x] Tipografia em rem e alturas sem unidade
- [x] Design system atualizado com as regras

**Falta**

- Nada pendente.

### 6. Textos legais (4 de 9)

**Feito**

- [x] Layout com índice lateral, vigência e aviso de rascunho
- [x] Rascunho da Política de privacidade (LGPD, Marco Civil)
- [x] Rascunho dos Termos de uso (CDC)
- [x] Rascunho da Política de reembolso (CDC art. 49)

**Falta**

- [ ] Revisão por advogado
- [ ] Razão social, CNPJ, endereço e encarregado de dados
- [ ] Prazos de guarda de dados e de estorno
- [ ] Decidir se as consultas são guardadas e se treinam modelos
- [ ] Definir a data de vigência

### 7. Entrar e criar conta (7 de 10)

**Feito**

- [x] Tela com abas Entrar e Criar conta
- [x] Botão Continuar com Google
- [x] E-mail e senha, com mostrar senha e Esqueci a senha
- [x] Verificação em duas etapas por código no e-mail, no cadastro e no login
- [x] Faixa do plano escolhido, com troca
- [x] Estados: código enviado, reenvio, código errado, expirado, já cadastrado, erro
- [x] Volta para a página pedida depois de entrar

**Falta**

- [ ] Servidor de autenticação na API FastAPI
- [ ] Login com Google de verdade (OAuth)
- [ ] Envio dos e-mails com o código e com o link de senha nova

### 8. Checkout (6 de 11)

**Feito**

- [x] Resumo do plano com próxima cobrança
- [x] Cartão com conferência de número, validade e código
- [x] Pix com código copia e cola e contagem
- [x] Dados da nota com CPF ou CNPJ validados
- [x] Estados: processando, recusado, aguardando Pix, aprovado
- [x] Conta antes da compra: só abre com login

**Falta**

- [ ] Escolher o provedor de pagamento
- [ ] Trocar os campos do cartão pelos campos seguros do provedor
- [ ] Confirmar pagamentos pelo provedor (webhooks)
- [ ] Pix Automático para a renovação
- [ ] Emissão de nota fiscal

### 9. Instalar o plugin (5 de 11)

**Feito**

- [x] Quatro passos marcáveis com barra de progresso
- [x] Download com estados preparando e link expirado
- [x] Código de conexão (demonstração)
- [x] Pergunta de teste com botão de copiar
- [x] Deu certo? levando ao Portal ou à Ajuda certa

**Falta**

- [ ] Arquivo real do plugin e formato de entrega
- [ ] Link de download que expira em 15 minutos
- [ ] Código de conexão real
- [ ] Confirmar os nomes dos menus do Claude
- [ ] Confirmar quais planos do Claude aceitam plugins
- [ ] Imagem curta do caminho no Claude

### 10. Portal do cliente (5 de 10)

**Feito**

- [x] Quatro abas com endereço próprio
- [x] Plano, próxima cobrança e forma de pagamento
- [x] Reembolso com prazo de 7 dias à vista e acompanhamento
- [x] Cancelar e reativar a assinatura
- [x] Nome, sair e excluir conta

**Falta**

- [ ] Dados reais da assinatura vindos do servidor
- [ ] Notas fiscais para baixar
- [ ] Novidades da base com data
- [ ] Regra de troca de plano no meio do mês
- [ ] Aviso de pagamento atrasado

### 11. Ajuda (3 de 4)

**Feito**

- [x] Seis artigos curtos
- [x] Link direto para cada artigo
- [x] Voltar à página de origem

**Falta**

- [ ] Canal de suporte e prazo de resposta definitivos

### 12. Arquitetura e servidor (6 de 9)

**Feito**

- [x] Pesquisa Astro ou React, publicada como artefato
- [x] Decisão: site todo em Astro e backend em Python com FastAPI
- [x] React e adaptador Node instalados (Plano A)
- [x] Rotas do assinante e Checkout renderizadas no servidor
- [x] Middleware que protege as rotas pela sessão da API
- [x] Contrato da API de login documentado

**Falta**

- [ ] Criar a API em FastAPI
- [ ] GET /auth/sessao e rotas de cadastro, login e código
- [ ] Escolher onde hospedar o servidor Node e a API

### 13. Artefatos e entregas (5 de 5)

**Feito**

- [x] Design system publicado e atualizado
- [x] Briefings e pendências publicados
- [x] Painel de progresso interativo, republicado na conta atual
- [x] Zips do projeto e dos artefatos
- [x] Projeto no GitHub

**Falta**

- Nada pendente.

### 14. Entrega do plugin (loja do Claude e outras IAs) (2 de 10)

**Feito**

- [x] Decidir o formato: conector MCP remoto + skills
- [x] Pesquisar requisitos da loja do Claude, ChatGPT, Copilot e Gemini

**Falta**

- [ ] Servidor MCP na API com OAuth (PKCE, CIMD e DCR com client_secret)
- [ ] Ferramentas de pesquisa anotadas como leitura e testadas no MCP Inspector
- [ ] Conta de teste para revisão, compatível com a verificação em duas etapas
- [ ] Repositório público do plugin com skills, README e licença
- [ ] Textos, ícone, slug, documentação e suporte da listagem
- [ ] Submeter conector e plugin no diretório do Claude
- [ ] Submeter no diretório do ChatGPT
- [ ] Guia para o TI do cliente no Copilot Studio e no Gemini Enterprise

### 15. Área do assinante (1 de 8)

**Feito**

- [x] Definir as abas e as diferenças entre Pro e Max

**Falta**

- [ ] Status do plugin: conexão por IA, uso do mês, versão
- [ ] Novidades (painel de admin na API: integração ainda em aberto)
- [ ] Tutoriais de instalação: Claude, ChatGPT, Copilot e Gemini
- [ ] Alertas por tema (Max)
- [ ] Resumo semanal por área (Max)
- [ ] Acesso antecipado e suporte prioritário (Max)
- [ ] As quatro IAs na landing, com animação

### 16. Pagamentos (Asaas) (2 de 8)

**Feito**

- [x] Mapear a API do Asaas
- [x] Integração real suspensa até haver CNPJ

**Falta**

- [ ] Simulação da API do Asaas no backend (clientes, assinaturas, cobranças, webhooks)
- [ ] Cartão, Pix e boleto no Checkout
- [ ] Formas de pagamento e faturas no Portal
- [ ] Liberar acesso só com pagamento confirmado (simulado)
- [ ] Ajustar Termos, Reembolso, Ajuda e landing para as três formas
- [ ] Trocar a simulação pela API real (quando houver CNPJ)

### 17. Ranqueamento no Google (1 de 9)

**Feito**

- [x] Pesquisa aprofundada de SEO

**Falta**

- [ ] Sitemap, robots.txt e noindex na área logada
- [ ] Canonical, títulos, descrições e Open Graph por página
- [ ] Dados estruturados: Organization, WebSite, SoftwareApplication
- [ ] Página 404 real e domínio único com redirecionamentos
- [ ] Core Web Vitals: topo sem atraso no LCP, imagens e fontes
- [ ] Banner de cookies LGPD e GA4 com Consent Mode v2
- [ ] Search Console, Bing Webmaster e IndexNow na publicação
- [ ] Página Sobre com autores e conteúdo revisado

### 18. Animação da explosão do átomo (1 de 3)

**Feito**

- [x] Definir quando toca: uma vez, na confirmação do pagamento

**Falta**

- [ ] Explosão do átomo e elétrons virando as abas novas
- [ ] Versão para movimento reduzido e botão Pular

### 19. Publicação (0 de 6)

**Feito**

- Nada concluído ainda.

**Falta**

- [ ] Escolher hospedagem e domínio
- [ ] Formulário de contato enviando de verdade
- [ ] sitemap.xml e robots.txt
- [ ] Teste com leitor de tela
- [ ] Tirar o modo de demonstração
- [ ] Publicar o site

### 20. Para equipes (depois do MVP) (0 de 2)

**Feito**

- Nada concluído ainda.

**Falta**

- [ ] Página /equipes
- [ ] Formulário de interesse

## Onde está cada coisa

| Caminho | O que é |
| --- | --- |
| `src/pages/` | Páginas: `index`, `entrar`, `assinar/[plano]`, `instalar`, `conta`, `ajuda`, `privacidade`, `termos`, `reembolso` |
| `src/components/` | Peças da landing e do site (Hero, Nav, Footer, Contact, Story, cenas, PlanCard, Icon, Photo…) |
| `src/layouts/` | `Base` (tema e movimento), `Legal` (textos legais), `Focus` (Entrar e Checkout) |
| `src/scripts/` | `motion.ts` (GSAP, Lenis), `orbit.ts` (logo), `hero-chips.ts` (cartões de lei em revezamento), `validate.ts` (CPF, CNPJ, cartão), `demo.ts` |
| `src/data/` | `plans.ts`, `photos.ts` (créditos), `site.ts` (contatos provisórios), `examples.ts`, `citacoes.ts` (125 citações) |
| `src/middleware.ts` | Porta das rotas do assinante e do Checkout, pela sessão da API FastAPI |
| `src/styles/` | `tokens.css` (marca), `global.css`, `forms.css` |
| `docs/` | Briefings, mapa, análise de animações, auditoria de IA, painel de progresso (`progresso.html`) |
| `design-system/` | Design system exportado (tokens, componentes, regras) |
| `.claude/skills/` | Skills de auditoria de design usadas no projeto |
