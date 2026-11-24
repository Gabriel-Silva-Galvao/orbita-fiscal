# Órbita: site

Site de venda do plugin da Órbita para o Claude. Astro, GSAP + ScrollTrigger, Lenis e a marca Limiar Esmeralda (temas claro e escuro).

O que está feito e o que falta: [PROGRESSO.md](PROGRESSO.md).

## Rodar

Requer Node 22 ou mais novo (exigência do Astro 6 em diante).

```powershell
npm install
npm run dev      # http://localhost:4321
npm run build    # gera dist/client (estático) e dist/server (Node)
npm run preview  # serve o build localmente
node dist/server/entry.mjs  # produção: servidor Node (HOST e PORT pelo ambiente)
```

Copie `.env.example` para `.env` quando houver servidor. Sem as variáveis, Entrar, Checkout, Instalar e Portal rodam em **modo de demonstração** (avisado na tela) e guardam a “assinatura” só no navegador (`src/scripts/demo.ts`). Para testar o Checkout: `4242 4242 4242 4242` aprova, `4000 0000 0000 0002` é recusado.

## Arquitetura (decidida em 24/11/2026)

- **Frontend:** o site inteiro fica em Astro. As páginas públicas continuam estáticas. As abas do assinante vão ser renderizadas no servidor, com ilhas React só nas partes muito interativas. Pesquisa: [artefatos/astro-ou-react.html](artefatos/astro-ou-react.html).
- **Backend:** todo em **Python**, com **FastAPI** como biblioteca principal. Login, assinatura, pagamento, portal e a base jurídica do plugin ficam nessa API. O Astro só chama a API por HTTP, sem regra de negócio própria: o servidor do Astro apenas protege as rotas e repassa as chamadas.
- Os endpoints do `.env.example` (`PUBLIC_AUTH_ENDPOINT`, `PUBLIC_CONTACT_ENDPOINT` e os próximos) apontam para essa API.
- **Acesso:** Google ou e-mail e senha, sempre com verificação em duas etapas por código de 6 dígitos no e-mail, no cadastro e no login. Contrato da API no topo de `src/pages/entrar.astro`.
- **Conta antes da compra:** só quem criou a conta e confirmou o e-mail chega ao Checkout. Escolher um plano sem estar logado leva a `/entrar?plano=<plano>&modo=criar`, e depois do código a pessoa volta ao Checkout desse plano.

### Como o Plano A está montado

- `astro.config.mjs`: integração `@astrojs/react` e adaptador `@astrojs/node` (modo `standalone`). Tudo continua estático por padrão.
- Rotas do assinante (`/conta`, `/instalar`, `/assinar/pro|max` e o futuro `/app`) declaram `export const prerender = false` e rodam no servidor.
- `src/middleware.ts` protege essas rotas. Com `API_URL` definido, chama `GET {API_URL}/auth/sessao` repassando o cookie: 200 abre a página e põe o usuário em `Astro.locals.usuario`; 401/403 manda para `/entrar?next=<rota>`. Sem `API_URL`, tudo abre em demonstração.
- Componentes React (`.tsx` em `src/components/`) entram só onde há muita interação, com `client:load`, `client:visible` ou, para um app inteiro, `client:only="react"`.

## Páginas

| Rota | Arquivo |
| --- | --- |
| `/` | `src/pages/index.astro` |
| `/entrar` | `src/pages/entrar.astro` (`?plano=pro\|max`, `?modo=criar`, `?erro=link-expirado`) |
| `/assinar/pro`, `/assinar/max` | `src/pages/assinar/[plano].astro` |
| `/instalar` | `src/pages/instalar.astro` |
| `/conta` | `src/pages/conta.astro` (`#plugin`, `#plano`, `#cancelar`, `#conta`) |
| `/ajuda` | `src/pages/ajuda.astro` (`#instalar`, `#conectar`, `#nao-aparece`, `#cobranca`, `#reembolso`, `#privacidade`) |
| `/privacidade`, `/termos`, `/reembolso` | `src/pages/*.astro` com `src/layouts/Legal.astro` |

## Regras de design

- Tokens em `src/styles/tokens.css` (gerado do design system em `design-system/`). Sem sombra e sem gradiente.
- Itens sem decisão usam o componente `Pending` (“a definir” / “a confirmar”), nunca viram promessa.
- Sem sobretítulo fora do topo da landing, sem ícone decorativo, nada que tenha ação se mexe sob o cursor, preço sempre fixo (`docs/auditoria-ia.md`).
- Movimento: atributos `data-reveal`, `data-speed`, `data-depth`, `data-split` (`src/scripts/motion.ts`). Com movimento reduzido, a página fica completa e parada.
- Textos em português do Brasil, valores como R$ 75,90, datas como 24/11/2026.

## Fotos

Unsplash, com autoria em `src/data/photos.ts` e no rodapé (“Créditos das fotos”). Hoje vêm do CDN do Unsplash; antes de publicar, vale baixá-las para `public/` mantendo os créditos.
