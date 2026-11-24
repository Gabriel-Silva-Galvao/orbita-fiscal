# Auditoria de traços de IA no design

24/11/2026. Feita com as skills instaladas no projeto em `.claude/skills/`, todas do registro skills.sh e só com instruções em texto, sem scripts:

- `audit-ai-design-slop` (mengto/skills): auditoria;
- `no-ai-design-slop` (mengto/skills): critério e “teste de remoção”;
- `better-typography` (jakubkrehel/skills): tipografia medida;
- `design-audit` (bencium/bencium-marketplace): hierarquia e consistência.

Escopo: o código da landing (`src/`) e a página renderizada no desktop (1280 px) e no celular (360 e 375 px), nos dois temas.

## Veredito

O site tem direção própria (verde da marca, átomo, fotos com papel na narrativa), mas acumulou reflexos de template. Os principais são:

- o sobretítulo em caixa alta espaçada sobre quase todo título;
- ícones em pastilhas e no topo de cada item;
- elementos que flutuam em laço sem informar nada;
- botões e cartões que se mexem sob o cursor.

Na tipografia, as alturas de linha estavam fixas em px, o espaçamento das letras exagerado nos rótulos e havia um peso que a fonte não carrega. A maior melhora vem de remover os sobretítulos e os ícones decorativos.

## Achados

| Prioridade | Classe | Padrão | Evidência | Dano | Remover ou corrigir |
| --- | --- | --- | --- | --- | --- |
| P1 | Padrão de IA | Alvo que foge do cursor | Botões “magnéticos” (`motion.ts`, `magnetic()`) e cartões de plano que inclinam com o botão “Assinar” dentro (`data-tilt-card` em `PlanCard`) | O alvo do clique se move sob o mouse | Remover o ímã dos botões e a inclinação dos cartões que têm ação |
| P2 | Padrão de IA | Sobretítulo sobre quase todo título | 9 `.overline` (A base, Exemplo, O dia a dia, Como funciona, Planos, Confiança, Dúvidas, Contato, hero), em caixa alta com `0.1em` e um traço animado | Repete o título, dilui a hierarquia e é o clichê nº 1 de landing gerada | Manter só no hero (“Plugin para Claude” informa algo); remover os outros e o traço |
| P2 | Padrão de IA | Ícone no topo de cada item | Ícone de 44 px em cada passo (já numerado) e em cada item de Confiança; ícones em pastilha em cada canal de contato; ícone em cada item do resumo legal; ícone decorativo no título do formulário | Ícones genéricos fazem o papel de enfeite e competem com o texto | Remover; manter só ícones com função (Instagram, e-mail, tema, fechar, enviar, seta do select) |
| P2 | Padrão de IA | Laços de flutuação | Citações do hero, cartões da cena “A base” e etiquetas de Brasília flutuam em laço infinito, todas ao mesmo tempo, mais o parallax | Movimento mecânico, sem estado nem causa | Manter a flutuação só nas citações do hero; nas cenas, só o parallax |
| P2 | Padrão de IA | Pílula que repete a imagem | Selo “Fonte conferida” preso à lente | Rotula o que a lente já mostra | Remover |
| P2 | Padrão de IA | Marca d’água gigante no rodapé | “Órbita” em 190 px na base do rodapé | Repete a logo logo acima; tendência de template | Remover |
| P2 | Defeito | Altura de linha fixa | Tokens `--text-*` com altura em px (`56px/60px`, `16px/26px`…) e tamanhos em px | A altura não acompanha o tamanho; o texto não respeita o tamanho de fonte do navegador | Alturas sem unidade por papel e tamanhos em `rem` |
| P2 | Defeito | Espaçamento exagerado | Rótulos em caixa alta de 11 px com `0.1em` a `0.14em`; “FISCAL” com `0.34em`, que vai a `0.5em` no hover | Palavras se desfazem; o texto se mexe no hover | Caixa alta pequena em `0.06em`; “FISCAL” em `0.22em`, sem animar o espaçamento |
| P3 | Defeito | Peso sintetizado | `font-weight: 700` no “!” do erro do formulário; a família carrega 400, 500 e 600 | O navegador engorda a fonte artificialmente | Usar 600 |
| P3 | Defeito | Quebra de parágrafo | Parágrafos sem `text-wrap: pretty`; títulos de seção sem `balance` em alguns blocos | Palavra sozinha na última linha | `pretty` em parágrafos, `balance` em títulos |

## O que fica

- A combinação Newsreader (títulos) e Hanken Grotesk (texto) é um par serifado + sem serifa com contraste, e não é uma fonte padrão de IA. Ficou como está, como manda a skill.
- As fotos têm papel narrativo e crédito. O átomo, a lente e a moldura de “O dia a dia” comunicam o produto.
- Rótulos “a definir” e “a confirmar” são estado real, não enfeite.

## Não verificado

- Leitura com leitor de tela real.
- Movimento reduzido na tela; a lógica foi revisada no código.

## Achado durante a verificação

| Prioridade | Classe | Padrão | Evidência | Dano | Remover ou corrigir |
| --- | --- | --- | --- | --- | --- |
| P1 | Padrão de IA | Contador animado no preço | Os planos mostravam “R$ 0” e “R$ 0,00” até a contagem disparar, quando o cartão já estava na tela | Preço errado à vista, mesmo por instantes, mina a confiança no momento da decisão | Contagem removida; o preço aparece fixo |
