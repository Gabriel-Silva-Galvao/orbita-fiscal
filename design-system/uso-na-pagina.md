# Como usar na página

Receita curta para montar as páginas dos briefings com este sistema.

## Estrutura de seção

1. Título (`display-lg`), sem sobretítulo.
2. Uma frase de apoio (`body-lg`, `mute`), no máximo duas linhas.
3. O conteúdo, em coluna de até 1.100 px.

Seções separadas por `space-9` no desktop e `space-8` no celular, com um filete `line` entre elas.

## Mapa de componentes por página

| Página | Componentes |
| --- | --- |
| Landing | Nav, Logo, Button, ExampleCard, Tag, Step, PlanCard, Faq, Field (contato), Footer |
| Entrar | Logo, Field, Button |
| Checkout | Logo, PlanCard (resumo), Field, Button, Tag |
| Instalar | Step, Button, Tag |
| Portal | Nav, Tag, Button, Field |
| Ajuda | Faq, Field, Button |
| Textos legais | Nav, texto em `body` e `display-md`, Footer |

Toda página termina com o Footer: o conteúdo fica numa folha `bg` com classe `page-sheet` e o rodapé vem depois dela.

## O que não fazer

- Não adicione números de acervo, selos de tribunais nem depoimentos sem dado real.
- Não use cor fora dos tokens nem sombra.
- Não mova texto corrido com parallax; só ilustrações e etiquetas seguem a rolagem.
- Não escreva “100% de garantia”.

## Sem traços de IA

Auditoria de 24/11/2026 com as skills audit-ai-design-slop, no-ai-design-slop, better-typography e design-audit. Para cada elemento, pergunte que função ele cumpre; se a página fica mais clara sem ele, remova.

- Sobretítulo em caixa alta só no hero.
- Ícone só com função; nunca em cima de cada título ou item.
- Nada que tenha ação se move sob o cursor (ímã, inclinação).
- Preço e números de decisão aparecem fixos, sem contagem.
- Laços de flutuação só onde há uma cena com motivo (citações do hero).
- Sem marca d'água gigante, sem selo que repete o que a imagem já mostra.
