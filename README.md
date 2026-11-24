# Órbita Fiscal: site

Site de venda do plugin da Órbita Fiscal para o Claude. Astro, GSAP + ScrollTrigger, Lenis e a marca Limiar Esmeralda (temas claro e escuro).

O que está feito e o que falta: [PROGRESSO.md](PROGRESSO.md).

## Rodar

Requer Node 22 ou mais novo (exigência do Astro 6 em diante).

```powershell
npm install
npm run dev      # http://localhost:4321
npm run build    # gera dist/
npm run preview  # serve o dist/
```

Copie `.env.example` para `.env` quando houver servidor. Sem as variáveis, Entrar, Checkout, Instalar e Portal rodam em **modo de demonstração** (avisado na tela) e guardam a “assinatura” só no navegador (`src/scripts/demo.ts`). Para testar o Checkout: `4242 4242 4242 4242` aprova, `4000 0000 0000 0002` é recusado.

## Arquitetura (decidida em 24/11/2026)

- **Frontend:** o site inteiro fica em Astro. As páginas públicas continuam estáticas. As abas do assinante vão ser renderizadas no servidor, com ilhas React só nas partes muito interativas. Pesquisa: [artefatos/astro-ou-react.html](artefatos/astro-ou-react.html).
- **Backend:** todo em **Python**, com **FastAPI** como biblioteca principal. Login, assinatura, pagamento, portal e a base jurídica do plugin ficam nessa API. O Astro só chama a API por HTTP, sem regra de negócio própria: o servidor do Astro apenas protege as rotas e repassa as chamadas.
- Os endpoints do `.env.example` (`PUBLIC_AUTH_ENDPOINT`, `PUBLIC_CONTACT_ENDPOINT` e os próximos) apontam para essa API.

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
