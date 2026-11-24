Botão em pílula com texto `button`: um principal cheio e um secundário só com contorno.

- Principal: fundo `brand`, texto `on-brand`. Um por bloco, no máximo dois por página.
- Secundário: fundo transparente, texto `ink`, borda `line-strong`.
- Altura mínima 44 px, raio `radius-pill`, padding horizontal 20 px.
- Foco: contorno sólido de 3 px em `brand` com recuo de 3 px.
- Texto de botão diz a ação e, no pagamento, o valor: “Pagar e receber o plugin”.
- Movimento: no hover o principal se enche de `ink` de baixo para cima (texto vira `bg`) e o secundário se enche de `soft` da esquerda, em 420 ms. Ao pressionar, `scale: 0.97` em 160 ms. O botão nunca se desloca sob o cursor. Com movimento reduzido, só a troca de cor.
- Quem consome fornece o texto e o destino.