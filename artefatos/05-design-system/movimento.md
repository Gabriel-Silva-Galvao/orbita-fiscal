# Movimento sofisticado

A página precisa parecer viva sem ficar barulhenta. Desde 23/11/2026 a direção mudou: a Órbita Fiscal usa movimento em toda a página, com parallax e ilustrações em camadas. O movimento continua ligado ao que o produto faz, que é encontrar a fonte e trazê-la até você. A implementação de referência está no site em Astro (`src/scripts/motion.ts` e `src/scripts/orbit.ts`).

## Princípios

- Tudo tem vida, mas nada compete com a leitura. O texto nunca se mexe depois de entrar, e só as camadas de ilustração seguem a rolagem.
- Cada movimento mostra uma de três coisas: origem (de onde vem a fonte), ordem (o que vem primeiro) ou resultado (o que mudou).
- Curvas suaves: `power3.out` e `expo.out` para entradas, `back.out` e `elastic.out` só para pequenos quiques (selo, átomo, citações). Nada linear além do parallax.
- Com `prefers-reduced-motion`, nenhuma animação roda e a página fica completa e parada. Se o motor de movimento falhar, a página aparece inteira em até 2,5 s.
- Mantenha o JavaScript de movimento abaixo de 60 KB compactado (hoje ~46 KB com GSAP e ScrollTrigger) e teste a 60 fps em celular de entrada.

## Durações

| Uso | Duração | Curva |
| --- | --- | --- |
| Toque em botão (`scale: 0.97`) | 160 ms | `--ease-out` `cubic-bezier(0.23, 1, 0.32, 1)` |
| Diálogo (opacidade e escala 0,96) | 220 ms | `--ease-out` |
| Hover de link, cor, borda | 280 ms | `ease-out` |
| Preenchimento de botão, sublinhado, pílula da aba | 420 a 520 ms | `cubic-bezier(.2,.8,.2,1)` |
| Entrada de bloco | 800 ms, 28 px, cascata de 90 ms | `power3.out` |
| Palavras do título do hero | 900 ms, cascata de 45 ms | `expo.out` |
| Abrir e fechar dúvida | 380 a 460 ms | `cubic-bezier(.2,.8,.2,1)` |
| Traço que se desenha | 1,4 s | `cubic-bezier(.65,0,.35,1)` |
| Flutuação de citações e folhas | 5 a 9 s, em laço | `ease-in-out` |

## As cenas

| Cena | Onde | O que acontece |
| --- | --- | --- |
| Entrada do hero | Landing, topo | Sobretítulo, depois o título palavra por palavra saindo de uma máscara, depois a frase e os botões. O átomo cresce com quique, dois anéis tracejados aparecem e giram (60 s e 90 s), e quatro citações chegam em órbita. |
| Profundidade no hero | Landing, topo | Com mouse, cada camada (`data-depth`) segue o cursor em uma profundidade diferente. Ao rolar, o texto sobe e esmaece e o átomo afunda e gira 6°. |
| Órbitas do fundo | Landing, topo | Elipses grandes atravessam o hero, com dois pontos `brand` viajando por elas (26 s e 40 s). |
| A base | Entre hero e exemplo | Foto real de lombadas em duotone da marca. Uma lente com o anel da órbita revela a foto em cores: com mouse, segue o cursor; sem mouse, percorre uma elipse a −28°. Citações à frente, em parallax. |
| Pergunta e fontes | Exemplo | A pergunta é digitada, aparece “Consultando a base” com o átomo acelerado e três pontos, e as fontes chegam uma a uma pela esquerda, cada uma com um fio `brand` que cresce. |
| Três passos | Como funciona | Uma linha corre com a rolagem e acende cada passo: o número ganha fundo `brand` e cresce. |
| Planos | Planos | O selo COMPLETO entra com quique. Preço fixo, cartões parados. |
| Brasília | Confiança | Foto do Congresso Nacional que se abre como uma órbita: um círculo de 18% cresce com a rolagem até a moldura inteira, com anéis da marca girando e etiquetas de garantias (CDC art. 49, LGPD) em parallax. |
| O dia a dia | Depois do exemplo | Texto dos quatro momentos rola à esquerda; à direita, uma moldura fixa (sticky) troca de foto com esmaecer e leve desfoque quando o momento chega ao meio da tela, com contador “02 de 04”. Uma linha com pontos se preenche com a rolagem. No celular, cada momento tem a própria foto, que abre de baixo para cima. |
| Rodapé revelado | Fim da página | A folha do conteúdo termina com cantos de 36 px e sobe, descobrindo o rodapé escuro fixo atrás dela. |
| Logo | Cabeçalho, hero, rodapé | Os elétrons giram sozinhos e o núcleo respira; com o mouse, aceleram e os anéis se inclinam. |

## Rolagem

Lenis é o único motor de rolagem suave, ligado ao ScrollTrigger e desligado com movimento reduzido. Diálogos abertos pausam a rolagem suave.

## Atributos do motor

| Atributo | Efeito |
| --- | --- |
| `data-split` | Título sobe palavra por palavra; o texto inteiro fica para leitores de tela |
| `data-reveal` | Entra ao ficar visível, em cascata com os vizinhos, uma vez |
| `data-speed="0.4"` | Parallax de rolagem; negativo anda contra a rolagem. O pai com `data-parallax` define o trecho |
| `data-depth="1.2"` | Segue o cursor dentro do hero |
| `data-steps` | Linha de progresso dos passos (`--p` de 0 a 1) |
| `data-orbit` | Elétrons do símbolo em órbita (ver componente Logo) |

## Imagens

Fotos reais licenciadas (Unsplash), com `srcset`, carregamento preguiçoso abaixo da dobra, texto alternativo em português e crédito ao autor no rodapé. Camadas de foto em parallax ficam sobredimensionadas em 12% a 24% para não revelar borda. Tratamentos permitidos: duotone com a cor `brand` (cinza + `mix-blend-mode: color`), recorte por `clip-path` (círculo, inset). Prints do produto continuam bem-vindos quando existirem.

## O que não fazer

- Não mover alvo de clique sob o cursor (botão “magnético”, cartão que inclina com botão dentro).
- Não animar preço ou número de decisão a partir de zero.

- Não mover texto corrido com parallax.
- Não esconder conteúdo esperando rolagem quando a pessoa pediu movimento reduzido.
- Não usar sombra, gradiente ou brilho para dar vida. A vida vem do movimento e do traço.
- Não girar o símbolo inteiro sem parar; só os elétrons andam em repouso.
