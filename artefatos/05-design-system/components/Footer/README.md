Rodapé no padrão de sites, sempre escuro, revelado ao final por trás da página, com as configurações na barra de baixo.

- Estrutura, de cima para baixo:
  - marca (Logo de 84 px), uma frase sobre o produto, ícones redondos de Instagram e e-mail;
  - quatro colunas de links: Produto, Sua conta, Ajuda e Legal. Títulos em `label` `brand`, links em `small` `mute`, com sublinhado que corre da esquerda no hover;
  - faixa “Privacidade e termos, em resumo” com quatro itens só em texto, cada um com a primeira frase em negrito (reembolso pelo CDC art. 49, direitos pela LGPD art. 18, consultas, uso responsável), e o contato do encarregado de dados;
  - barra final com ©, CNPJ, link “Créditos das fotos” e as configurações;
- Sempre escuro, nos dois temas: o rodapé redefine os tokens localmente (fundo `#0b201e`, superfície `#122e2a`, `ink` `#f0f5e8`, `mute` `#b2c8bc`, `brand` `#83d3a9`, filete `#26443d`). Contraste mínimo 4,5:1 mantido.
- Revelado ao final: o conteúdo fica numa folha `bg` acima (`z-index` 1) que termina com cantos de 36 px e filete `line`; o rodapé fica fixo embaixo (`z-index` 0) e um espaçador com a altura dele permite descobri-lo. Só vale quando a tela tem 768 px ou mais de largura e o rodapé é mais baixo que a janela; senão é um rodapé comum, no fluxo.
- Configurações:
  - Tema: seletor de três opções (Auto, Claro, Escuro) em `fieldset` com rádios, marcador `brand` que desliza em CSS puro (`:has(:checked)`); abaixo de 420 px mostra só os ícones. A escolha fica salva no navegador.
  - Preferências de cookies: abre um diálogo modal honesto. Diz o que o site guarda (só o tema, como essencial) e o que não usa (medição, publicidade), com botão para apagar as preferências. Não exibe chaves para coisas que não existem.
  - Voltar ao topo: botão redondo.
- Diálogos: `<dialog>` modal, centrado, entra com opacidade e escala 0,96 em 220 ms; fecha com Esc, clique fora ou botão; o foco volta ao botão que abriu; a rolagem suave pausa enquanto está aberto.
- Itens ainda sem decisão (CNPJ, Instagram, e-mail do encarregado, política de cookies) levam o rótulo tracejado.
- Quem consome fornece os links, os canais e o resumo legal.
