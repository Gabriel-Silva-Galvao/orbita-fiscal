# Análise do site da Órbita Fiscal

24/11/2026. Revisão da landing com as skills **build-awwwards-quality-sites** (direção, fotos licenciadas, rolagem suave, texto acessível) e **emil-design-eng** (curvas, durações, toque, interrupção). Cada linha abaixo já foi aplicada no código.

## Movimento e interação

| Antes | Depois | Por quê |
| --- | --- | --- |
| Rolagem nativa, parallax “aos trancos” na roda do mouse | Lenis como único motor de rolagem, ligado ao ScrollTrigger; desligado com movimento reduzido | Parallax e trilho preso ficam contínuos; um só motor evita conflito |
| Cenas desenhadas em SVG (estante, colunata) | Fotos reais licenciadas (Unsplash) com tratamento da marca | A skill pede imagem real para ilustração; fotos dão contexto e confiança |
| Nenhum botão respondia ao toque | `scale: 0.97` em `:active` (botões, abas, Instagram, copiar, enviar) | Feedback imediato de que o clique foi ouvido; `scale` não briga com o ímã do GSAP |
| Hovers de deslocamento valiam também no toque | Hovers de movimento só em `(hover: hover) and (pointer: fine)` | No celular, toque dispara hover falso |
| Trocar de aba redigitava a pergunta toda (cerca de 2,5 s), inclusive pelo teclado | Digitação só na primeira vez de cada aba; teclado e revisitas mostram as fontes direto | Não animar ação repetida nem de teclado |
| Dúvidas abriam em 460 ms e fechavam em 380 ms | 300 ms ao abrir, 220 ms ao fechar, curva `cubic-bezier(0.23, 1, 0.32, 1)` | Interface abaixo de 300 ms; saída mais rápida que entrada |
| Citações do hero nasciam de `scale(0.6)` | Nascem de `scale(0.9)` com opacidade | Nada surge do nada |
| Curvas genéricas (`ease-out`, `.2,.8,.2,1`) | Tokens `--ease-out` e `--ease-in-out` com curvas fortes | Entradas com mais intenção |
| Títulos de seção apareciam em bloco | Títulos sobem palavra por palavra (`data-split`), com o texto inteiro em `.sr-only` | Ritmo de leitura; leitor de tela ouve a frase inteira |
| Título do hero dividido em palavras lidas uma a uma | Nome acessível inteiro em `.sr-only`, palavras com `aria-hidden` | Acessibilidade da animação de texto |
| Ícones de passos e confiança desenhados à mão | Ícones Solar (Iconify) em linha, que se desenham ao aparecer | Família de ícones consistente, sem pedido de rede |

## Animações próprias com imagens

| Cena | O que faz |
| --- | --- |
| A base | Foto de lombadas em verde da marca (duotone). Uma lente com o anel da órbita revela a foto em cores e um pouco ampliada: com mouse, segue o cursor; sem mouse, percorre uma elipse inclinada a −28°, como o símbolo. Metáfora de conferir a fonte. |
| O dia a dia | Texto dos quatro momentos rola à esquerda; à direita, uma única moldura fica parada (sticky) e troca de foto com esmaecer e leve desfoque quando o momento chega ao meio da tela, com contador “02 de 04”. Uma linha com pontos liga os momentos e se preenche com a rolagem. No celular, cada momento mostra a própria foto, que abre de baixo para cima. Substituiu o trilho horizontal preso (24/11/2026), que ficou exagerado. |
| Confiança | Foto do Congresso Nacional que se abre como uma órbita: um círculo de 18% cresce com a rolagem até a moldura inteira, com anéis da marca girando e etiquetas de garantias (CDC, LGPD). |
| Contato | Foto de mesa de trabalho em parallax ao lado do formulário. |

## Rodapé e contato

- Rodapé com convite final, marca, Instagram, quatro colunas (Produto, Sua conta, Ajuda, Legal), resumo de privacidade e termos (CDC art. 49, LGPD art. 18, consultas, uso responsável), encarregado de dados, créditos das fotos, razão social e CNPJ, voltar ao topo e tema.
- Seção “Fale com a equipe da Órbita”: canais (e-mail com botão de copiar, Instagram, prazo, escritórios) e formulário com validação que diz o que falta, sem culpar, erro que não depende só de cor, consentimento LGPD, estado de envio e de falha.

## Decisões

- **Three.js:** não usado. Lente, trilho e órbita resolvem com CSS `clip-path`, GSAP e uma imagem; um shader somaria peso sem contar nada a mais.
- **Rolagem suave:** Lenis (mais leve que Locomotive Scroll, integração direta com ScrollTrigger).
- **Fotos:** servidas pelo CDN do Unsplash com `srcset`, `loading="lazy"` abaixo da dobra e texto alternativo em português. Origem e autoria em `src/data/photos.ts` e no rodapé.

## O que ainda falta

- Páginas `/privacidade`, `/termos`, `/reembolso`, `/entrar`, `/ajuda`, `/conta`, `/instalar` e `/equipes` ainda não existem (os links levam a 404).
- E-mail, Instagram, encarregado de dados, razão social e CNPJ são provisórios em `src/data/site.ts`, marcados “a confirmar” ou “a definir”.
- O formulário envia para `PUBLIC_CONTACT_ENDPOINT` quando ele for definido; até lá, abre o e-mail da pessoa com a mensagem pronta.
- Não foi possível ver o modo de movimento reduzido na tela; a lógica foi revisada no código.
- Para produção, vale baixar as fotos e servi-las do próprio domínio, mantendo os créditos.

## Rodapé revelado e logo detalhada (24/11/2026)

| Antes | Depois | Por quê |
| --- | --- | --- |
| Rodapé longo e claro, com convite, quadro legal e créditos abertos | Rodapé escuro no padrão de sites: marca e redes, 4 colunas, resumo legal em faixa, barra com © e configurações, marca d'água | Leitura rápida, lugar esperado para cada coisa |
| Rodapé rolava junto com a página | Revelado ao final: fica fixo atrás da página, que termina com cantos arredondados e sobe para descobri-lo; só quando cabe na janela (≥ 768 px), senão vira rodapé comum | Fechamento com sensação de profundidade, sem cortar conteúdo em telas baixas |
| Botão de tema que alternava em ciclo | Seletor de três opções (Auto, Claro, Escuro) com marcador que desliza, em CSS puro | Estado visível de uma vez; funciona sem medir a tela |
| Sem preferências de cookies | Diálogo honesto: só armazenamento essencial (tema), medição e publicidade “não usamos”, botão para apagar preferências | LGPD e transparência, sem fingir controles que não existem |
| Créditos das fotos abertos no rodapé | Créditos em diálogo, a partir de um link na barra final | Rodapé mais limpo |
| Símbolo simples em todos os tamanhos | Duas camadas: simples até 32 px; detalhada a partir de 48 px, com selo de 36 marcações que gira, anéis em linha dupla, elétrons com miolo e rastro, brilho no núcleo e campo pontilhado girando ao contrário | Regra de logo responsivo da skill de marca: detalhe só onde é legível; sem gradiente, sombra nem transparência |
| Logo do cabeçalho com 52 px | 64 px (50 px no celular); rodapé 84 px | Pedido de mais presença da marca |
