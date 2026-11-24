# Órbita Fiscal: progresso do site

Atualizado em 24/11/2026. As 7 páginas do MVP existem e o fluxo completo funciona em **modo de demonstração**: nada é cobrado, nenhum e-mail é enviado e a “conta” fica só no navegador. Para ir ao ar, faltam decisões da empresa, a revisão jurídica e a parte de servidor.

Painel interativo (status e bloqueios editáveis): https://claude.ai/artifact/Ea4BJ3bdkkshfCkQemurZu

## Situação das páginas

| Página | Rota | Situação | O que falta |
| --- | --- | --- | --- |
| 1. Landing | `/` | Pronta | Revisão jurídica dos exemplos; contatos reais |
| 2. Entrar e criar conta | `/entrar` | Tela pronta, demonstração | Servidor de autenticação (Google + link por e-mail) |
| 3. Checkout | `/assinar/pro`, `/assinar/max` | Tela pronta, demonstração | Provedor de pagamento, campos seguros do cartão, Pix, nota fiscal |
| 4. Instalar o plugin | `/instalar` | Tela pronta, demonstração | Arquivo real do plugin, link expirável, código de conexão real, nomes dos menus do Claude |
| 5. Portal do cliente | `/conta` | Tela pronta, demonstração | Dados reais da assinatura, notas, reembolso e cancelamento pelo provedor |
| 6. Ajuda | `/ajuda` | Pronta | Canal de suporte e prazo de resposta definitivos |
| 7. Textos legais | `/privacidade`, `/termos`, `/reembolso` | Rascunho | Revisão por advogado; razão social, CNPJ, prazos |
| 8. Para equipes | `/equipes` | Depois do MVP | Só depois do fluxo individual no ar |

## Passo a passo

64 de 103 subtarefas feitas. Cada etapa separa o que já foi feito do que falta. O mesmo conteúdo, com caixas que dá para marcar, está no painel interativo. A fonte das etapas é `docs/etapas.json`.

| Etapa | Feito | Situação |
| --- | --- | --- |
| 1. Base do projeto | 6 de 6 | Concluída |
| 2. Landing | 10 de 13 | Em andamento |
| 3. Movimento | 6 de 7 | Em andamento |
| 4. Fotos reais | 4 de 5 | Em andamento |
| 5. Auditoria de traços de IA | 6 de 6 | Concluída |
| 6. Textos legais | 4 de 9 | Em andamento |
| 7. Entrar e criar conta | 5 de 9 | Em andamento |
| 8. Checkout | 5 de 10 | Em andamento |
| 9. Instalar o plugin | 5 de 11 | Em andamento |
| 10. Portal do cliente | 5 de 10 | Em andamento |
| 11. Ajuda | 3 de 4 | Em andamento |
| 12. Artefatos e entregas | 5 de 5 | Concluída |
| 13. Publicação | 0 de 6 | Não iniciada |
| 14. Para equipes (depois do MVP) | 0 de 2 | Não iniciada |

### 1. Base do projeto (6 de 6)

**Feito**

- [x] Importar briefings, persona e mapa de páginas
- [x] Importar o design system Limiar Esmeralda
- [x] Criar o projeto em Astro com os tokens da marca
- [x] Temas claro e escuro, com escolha salva
- [x] Fontes Newsreader e Hanken Grotesk servidas pelo site
- [x] Repositório no GitHub (privado)

**Falta**

- Nada pendente.

### 2. Landing (10 de 13)

**Feito**

- [x] Cabeçalho com logo, links e botão
- [x] Topo com título, frase de apoio e átomo
- [x] Exemplo em três abas, marcado como ilustrativo
- [x] O dia a dia: texto e moldura fixa que troca de foto
- [x] Como funciona: três passos
- [x] Planos Pro e Max, diferença por tarefa
- [x] Confiança com garantias do CDC e da LGPD
- [x] Dúvidas: quatro perguntas
- [x] Contato com formulário validado
- [x] Rodapé revelado ao final, com tema e cookies

**Falta**

- [ ] Revisão jurídica das 8 citações dos exemplos
- [ ] Trocar contatos provisórios pelos reais
- [ ] Imagem de compartilhamento (Open Graph)

### 3. Movimento (6 de 7)

**Feito**

- [x] GSAP e ScrollTrigger
- [x] Rolagem suave com Lenis
- [x] Logo com órbita sozinha e no mouse
- [x] Entradas em cascata e títulos palavra por palavra
- [x] Parallax nas cenas com foto
- [x] Página completa e parada com movimento reduzido (no código)

**Falta**

- [ ] Conferir na tela com movimento reduzido ativado

### 4. Fotos reais (4 de 5)

**Feito**

- [x] 8 fotos do Unsplash escolhidas pela folha de contato
- [x] Créditos no código e no rodapé
- [x] Lente que revela a cor na foto da base
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

### 7. Entrar e criar conta (5 de 9)

**Feito**

- [x] Tela com abas Entrar e Criar conta
- [x] Botão Continuar com Google
- [x] Link de acesso por e-mail, sem senha
- [x] Faixa do plano escolhido, com troca
- [x] Estados: link enviado, reenvio, já cadastrado, expirado, erro

**Falta**

- [ ] Servidor de autenticação
- [ ] Login com Google de verdade (OAuth)
- [ ] Envio dos e-mails com o link
- [ ] Sessão da pessoa entre as páginas

### 8. Checkout (5 de 10)

**Feito**

- [x] Resumo do plano com próxima cobrança
- [x] Cartão com conferência de número, validade e código
- [x] Pix com código copia e cola e contagem
- [x] Dados da nota com CPF ou CNPJ validados
- [x] Estados: processando, recusado, aguardando Pix, aprovado

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

### 12. Artefatos e entregas (5 de 5)

**Feito**

- [x] Design system publicado e atualizado
- [x] Briefings e pendências publicados
- [x] Painel de progresso interativo
- [x] Zips do projeto e dos artefatos
- [x] Projeto no GitHub

**Falta**

- Nada pendente.

### 13. Publicação (0 de 6)

**Feito**

- Nada concluído ainda.

**Falta**

- [ ] Escolher hospedagem e domínio
- [ ] Formulário de contato enviando de verdade
- [ ] sitemap.xml e robots.txt
- [ ] Teste com leitor de tela
- [ ] Tirar o modo de demonstração
- [ ] Publicar o site

### 14. Para equipes (depois do MVP) (0 de 2)

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
| `src/scripts/` | `motion.ts` (GSAP, Lenis), `orbit.ts` (logo), `lens.ts`, `validate.ts` (CPF, CNPJ, cartão), `demo.ts` |
| `src/data/` | `plans.ts`, `photos.ts` (créditos), `site.ts` (contatos provisórios), `examples.ts` |
| `src/styles/` | `tokens.css` (marca), `global.css`, `forms.css` |
| `docs/` | Briefings, mapa, análise de animações, auditoria de IA, painel de progresso (`progresso.html`) |
| `design-system/` | Design system exportado (tokens, componentes, regras) |
| `.claude/skills/` | Skills de auditoria de design usadas no projeto |
