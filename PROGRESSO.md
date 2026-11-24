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

### Feito

1. **Base do projeto** (23/11): briefings, mapa de páginas e design system Limiar Esmeralda importados para `docs/` e `design-system/`; site em Astro com os tokens da marca, temas claro e escuro.
2. **Landing** (23/11): topo, exemplo em três abas, como funciona, planos (Pro R$ 50 e Max R$ 75,90, diferença por tarefa), confiança, dúvidas.
3. **Movimento** (23–24/11): GSAP + ScrollTrigger, rolagem suave com Lenis, logo com órbita que acelera no mouse, entradas em cascata, parallax; tudo parado com movimento reduzido.
4. **Fotos reais** (24/11): 8 fotos do Unsplash com crédito (`src/data/photos.ts` e rodapé); lente na foto da base, “O dia a dia” com moldura fixa que troca de foto, Brasília que se abre em órbita.
5. **Contato e rodapé** (24/11): seção “Fale com a equipe” com formulário validado; rodapé escuro revelado ao final, com resumo legal, tema e preferências de cookies.
6. **Logo** (24/11): de volta à versão simples, 64 px no cabeçalho, só o símbolo em telas de até 400 px.
7. **Auditoria de traços de IA** (24/11): skills instaladas em `.claude/skills/`; sem sobretítulos, ícones decorativos, botões que fogem do cursor ou contagem de preço; tipografia em `rem` (`docs/auditoria-ia.md`).
8. **Textos legais** (24/11): Privacidade, Termos e Reembolso em rascunho, com índice lateral e base em LGPD, Marco Civil, CDC e Decreto 7.962/2013.
9. **Entrar** (24/11): Google ou link por e-mail, faixa do plano escolhido, todos os estados (link enviado, reenvio, e-mail já cadastrado, link expirado, erro).
10. **Checkout** (24/11): resumo com próxima cobrança, cartão (Luhn, validade, CVC), Pix com código e contagem, CPF/CNPJ validados, estados de recusa, espera e aprovação.
11. **Instalar** (24/11): quatro passos marcáveis, download com estados, código de conexão, pergunta de teste, “Deu certo?” levando à Ajuda no passo certo.
12. **Portal** (24/11): abas Plugin, Plano e pagamento, Cancelar ou reembolso (prazo de 7 dias à vista), Conta (sair, excluir).
13. **Ajuda** (24/11): seis artigos com link direto (`#instalar`, `#conectar`, `#nao-aparece`, `#cobranca`, `#reembolso`, `#privacidade`).
14. **Artefatos**: design system, briefings, pendências e painel de progresso publicados no claude.ai.

### Falta

**Decisões da empresa** (travam o resto)

- [ ] Provedor de pagamento (cartão, Pix Automático, assinatura) e emissão de nota fiscal.
- [ ] Hospedagem do site e do servidor; domínio.
- [ ] Serviço de e-mail para os links de acesso, recibos e avisos.
- [ ] Razão social, CNPJ, endereço, e-mail de contato, Instagram e encarregado de dados (hoje provisórios em `src/data/site.ts`).
- [ ] Política de dados: se as consultas são guardadas, por quanto tempo e se treinam modelos.
- [ ] Prazos: estorno, guarda de dados, aviso de mudança de preço e de termos.
- [ ] Limite de uso do Max e regra de troca de plano no meio do mês.
- [ ] Formato de entrega do plugin, proteção contra cópia, planos do Claude que aceitam plugins e nomes dos menus.
- [ ] Canal de suporte e prazo de resposta; frequência de atualização da base.

**Jurídico**

- [ ] Revisão por advogado de Privacidade, Termos e Reembolso.
- [ ] Revisão das 8 citações dos exemplos da landing (`src/data/examples.ts`).

**Servidor e integrações** (ligar o que hoje é demonstração)

- [ ] Autenticação: Google OAuth e link por e-mail; sessão. A tela chama `PUBLIC_AUTH_ENDPOINT` (POST com `{modo, nome, email, plano}`; 409 = e-mail já tem conta) e `PUBLIC_AUTH_ENDPOINT/google?next=…`.
- [ ] Pagamento: trocar os campos do cartão pelos campos seguros do provedor (o número nunca passa pelo nosso servidor); webhooks de aprovação, recusa e Pix; ativar com `PUBLIC_PAYMENT_PROVIDER`.
- [ ] Notas fiscais e recibos por e-mail.
- [ ] Portal com dados reais: assinatura, próxima cobrança, notas, reembolso e cancelamento pelo provedor.
- [ ] Download do plugin com link que expira em 15 minutos e código de conexão real.
- [ ] Formulário de contato: definir `PUBLIC_CONTACT_ENDPOINT` (POST JSON); sem ele, abre o e-mail da pessoa.
- [ ] Tirar o modo de demonstração (`src/scripts/demo.ts` e os avisos) quando cada integração existir.

**Publicação**

- [ ] Baixar as fotos do Unsplash para o próprio site, mantendo os créditos.
- [ ] Imagem de compartilhamento (Open Graph), `sitemap.xml` e `robots.txt`.
- [ ] Testar com leitor de tela e com movimento reduzido ativado no sistema.
- [ ] Publicar no domínio escolhido.

**Depois do MVP**

- [ ] Página Para equipes (`/equipes`) com formulário de interesse.

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
