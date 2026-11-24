A Órbita vende um plugin para o Claude que liga a base brasileira de jurisprudência e legislação à IA que o advogado já usa. A marca é a Limiar Esmeralda: verde profundo, tinta quase preta esverdeada, um verde-folha suave e muito ar. Este sistema serve a uma landing page curta e às páginas de compra e uso.

## Fundamentos de conteúdo

- Fale em português do Brasil, em frase curta e direta, com tratamento “você”. Sem gíria, sem exclamação, sem emoji.
- Prometa só o que dá para conferir: “fonte para conferir” e “reembolso em até 7 dias”. Não use “100% garantido”, “sem erros” nem número de acervo sem data e critério.
- Escreva valores como R$ 75,90 e datas como 23/11/2026.
- Itens sem decisão levam o rótulo tracejado “a confirmar” ou “a definir” (componente Tag).
- Texto de exemplo vem sempre marcado como ilustrativo.

## Fundamentos visuais

- Cor: fundo `bg`, texto `ink`, apoio `mute`, ação `brand`, relevo `soft`. Verde só onde há ação ou destaque. Existem os temas claro e escuro, lado a lado desde o primeiro dia.
- Tipografia: títulos em Newsreader (`display-xl` a `title`), texto em Hanken Grotesk (`body-lg` a `label`). Um título `display-xl` por página. Tamanhos em `rem` e alturas de linha sem unidade (títulos 1,07 a 1,3; texto 1,5 a 1,6). Caixa alta pequena com `0.06em`. Títulos com `text-wrap: balance`, parágrafos com `pretty`. Só os pesos carregados: 400, 500 e 600.
- Espaço: seções separadas por `space-9` no desktop e `space-8` no celular; cartões com padding `space-5`.
- Rodapé: a única área sempre escura, nos dois temas (veja o componente Footer).
- Bordas, não sombras: filete `line` de 1 px e raios `radius-lg` e `radius-xl`; botões e abas em `radius-pill`. Nenhuma sombra e nenhum gradiente.
- Foco: contorno sólido de 3 px em `brand`, com recuo de 3 px, em todo elemento interativo.
- Movimento: a página tem vida do topo ao rodapé (entradas em cascata, parallax em camadas, órbita do símbolo, microinterações), sempre suave e sem mover texto corrido. Com movimento reduzido a página fica completa e parada. Detalhes em Movimento sofisticado.
- Imagens: o símbolo atômico em disco `soft` é a imagem do hero. Fora isso, fotos reais licenciadas (Unsplash), com crédito ao autor: lombadas de livros em duotone da marca, mesa de trabalho, documentos, Congresso Nacional. Cada foto tem papel na narrativa; nada de foto decorativa.
- Texto: contraste mínimo 4,5:1 nos dois temas. Não use `mute` sobre `soft` no tema claro.

## Iconografia

Ícones só quando fazem algo (enviar, fechar, tema, seta de seleção, redes). Nada de ícone enfeitando título, item de lista ou cartão. Quando houver, família Solar (Iconify), versão `linear`, em linha e sem pedido de rede, na cor `ink` ou `brand`. Marcas reais só em contexto verdadeiro (Instagram, via MDI). Use o símbolo atômico como marca, marcadores redondos em `brand` nas listas e o sinal “+” do FAQ. Nada de emoji.

## Como ler este sistema

- Cores, tipos, espaços e raios estão em `tokens.json`; as prévias usam o tema do quadro (claro por padrão, escuro no alternador).
- Cada componente tem README e prévia. Páginas inteiras não fazem parte do sistema: elas estão nos briefings.
- Seções adicionais: Referências, Movimento sofisticado e Como usar na página.
- Prints do protótipo estão em `assets/Prints`.
