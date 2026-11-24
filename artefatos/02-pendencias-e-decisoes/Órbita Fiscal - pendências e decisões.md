# Órbita Fiscal: pendências e decisões

23/11/2026 · Gabriel Luis

Quatro decisões foram tomadas e a landing já foi construída com elas. Onze pendências continuam abertas e aparecem na página com o rótulo tracejado “a definir” ou “a confirmar”.

> Cópia exportada do doc no claude.ai em 24/11/2026. Decisões posteriores (acesso por Google + link por e-mail; Entrar e Checkout só como interface) estão em PROGRESSO.md e no painel de progresso.

## Decidido

| Questão | Escolha | Efeito na landing |
| --- | --- | --- |
| Tecnologia do site | Astro | Componentes reaproveitáveis para as sete páginas; tokens do design system em CSS |
| Pro x Max | Por tarefa | Pro: pesquisar. Max: tudo do Pro, conferir o processo e preparar a peça. Limite de uso segue “a definir” |
| Exemplos das abas 2 e 3 | Escritos pelo Claude, marcados | Abas Conferir o processo e Preparar a peça preenchidas como ilustrativas, pendentes de revisão jurídica |
| “100% de garantia” | Não prometer | A página fala em fonte para conferir e reembolso em até 7 dias, como pede o design system |

O último item seguiu a regra já escrita no design system. Se quiser outra linha, é só dizer.

## Em aberto

Em ordem de impacto. A coluna da direita diz como a landing trata o ponto enquanto ele não é decidido.

| Pendência | Páginas que trava | Como aparece hoje na landing |
| --- | --- | --- |
| Cada resultado traz link ou inteiro teor da fonte? | Landing, Instalar | “Fonte para conferir” com rótulo “a confirmar” no Pro e em Confiança |
| Cobertura da base e frequência de atualização, com data e critério | Landing, Portal | Dúvida “O que a base cobre?” com “a definir” |
| Somente Claude ou outras IAs também? | Landing, Ajuda | Dúvida “Funciona com qual IA?”: Claude, outras IAs “a definir” |
| Limite de uso do Max | Landing, Checkout, Portal | Item “Limite de uso” com “a definir” |
| Haverá plano anual e teste grátis? | Landing, Checkout | Não aparece; só “Cobrança mensal” |
| Entrega do plugin após a compra e proteção contra cópia | Instalar, Portal | Passo 1 diz “Você recebe o plugin logo depois” |
| Razão social, política de dados e textos legais | Textos legais, Landing | Confiança “Seus dados” e dúvida de dados com “a definir”; links do rodapé ainda sem página |
| Método de acesso: e-mail e senha, link por e-mail ou Google | Entrar | Link “Entrar” leva a /entrar, ainda sem página |
| Provedor de pagamento, Pix Automático e nota fiscal | Checkout | “Cartão ou Pix” com “a confirmar”; botões levam a /assinar/pro e /assinar/max, ainda sem página |
| Canal de suporte e prazo de resposta | Ajuda | Link “Ajuda” no rodapé, ainda sem página |
| Quais planos do Claude permitem instalar plugins | Instalar, Landing | Primeira dúvida com “a confirmar” |

## Citações da landing para revisão jurídica

Todas aparecem como exemplo ilustrativo, mas precisam do aval de um advogado antes de ir ao ar. O texto fica em `src/data/examples.ts`.

| Aba | Citação | Como a landing resume |
| --- | --- | --- |
| Pesquisar | Lei 6.830/1980, art. 40 | Suspende a execução sem devedor ou bens; após um ano, arquivo |
| Pesquisar | Súmula 314 do STJ | Um ano de suspensão, depois corre a prescrição de cinco anos |
| Pesquisar | CTN, art. 174 | Cinco anos para cobrar o crédito, da constituição definitiva |
| Conferir o processo | REsp 1.340.553/RS, Tema 566 do STJ | O ano de suspensão começa com a intimação da Fazenda, sem depender de despacho |
| Conferir o processo | Lei 6.830/1980, art. 40, § 4º | Prescrição intercorrente de ofício, ouvida a Fazenda |
| Preparar a peça | Súmula 393 do STJ | Exceção de pré-executividade para matéria de ofício sem dilação probatória |
| Preparar a peça | REsp 1.340.553/RS, Tema 566 do STJ | Marco inicial da suspensão e o que interrompe a contagem |
| Preparar a peça | Lei 6.830/1980, art. 40, § 4º | Base para reconhecer a prescrição intercorrente |

- [ ] Revisão jurídica das oito citações e dos resumos
