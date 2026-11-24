# Órbita Fiscal: progresso do site

24/11/2026 · Gabriel Luis

> Doc antigo, substituído pelo painel interativo de progresso e pelo PROGRESSO.md. Mostra o estado de 24/11/2026, quando só a landing estava pronta.

A landing está pronta e roda localmente; é 1 das 7 páginas do MVP. Ainda não está publicada na internet, e as outras 6 páginas dependem de decisões em aberto.

## Páginas do MVP

1 de 7 páginas pronta. As rotas das outras já têm links na landing e dão erro 404 até existirem.

| Página | Rota | Status | O que falta |
| --- | --- | --- | --- |
| 1. Landing | / | Pronta | Revisão jurídica dos exemplos, contatos definitivos, publicar na internet |
| 2. Entrar e criar conta | /entrar | A fazer | Decidir o método de acesso (e-mail e senha, link por e-mail ou Google) |
| 3. Checkout | /assinar/pro, /assinar/max | A fazer | Provedor de pagamento, Pix Automático e nota fiscal |
| 4. Instalar o plugin | /instalar | A fazer | Formato de entrega do plugin e planos do Claude que aceitam plugins |
| 5. Portal do cliente | /conta | A fazer | Regra de troca de plano e frequência de atualização da base |
| 6. Ajuda | /ajuda | A fazer | Canal de suporte e prazo de resposta |
| 7. Textos legais | /privacidade, /termos, /reembolso | A fazer | Razão social, CNPJ e textos redigidos ou revisados por advogado |
| 8. Para equipes | /equipes | Depois do MVP | Entra depois que o fluxo individual estiver no ar |

## Landing: o que já tem

Feita em Astro, com GSAP e Lenis para o movimento, nos temas claro e escuro, e testada no desktop e no celular (360 e 375 px).

| Seção | O que tem |
| --- | --- |
| Cabeçalho | Logo de 64 px com órbita; só o símbolo em telas de até 400 px; some ao descer e volta ao subir |
| Topo | Título palavra por palavra, átomo em órbita e quatro citações reais ao redor |
| A base | Foto de lombadas em verde; uma lente revela a cor |
| Exemplo | Três abas; a pergunta se digita e as fontes chegam uma a uma (ilustrativo) |
| O dia a dia | Texto à esquerda e moldura fixa que troca de foto |
| Como funciona | Três passos ligados por uma linha que acende com a rolagem |
| Planos | Pro R$ 50 e Max R$ 75,90, preços fixos, diferença por tarefa |
| Confiança | Foto do Congresso que se abre em órbita, com garantias do CDC e da LGPD |
| Dúvidas | Quatro perguntas, uma aberta por vez |
| Contato | Canais da equipe e formulário com validação e consentimento LGPD |
| Rodapé | Escuro, revelado ao final, com resumo legal, tema e preferências de cookies |

## Histórico

| Data | Rodada | O que mudou |
| --- | --- | --- |
| 24/11/2026 | Traços de IA | Quatro skills de auditoria instaladas; saíram sobretítulos, ícones decorativos, botões que fogem do cursor e contagem de preço; tipografia em rem |
| 24/11/2026 | Logo simples | Volta ao símbolo original; só o símbolo em telas de até 400 px |
| 24/11/2026 | Rodapé e logo | Rodapé escuro revelado ao final, com tema e cookies; logo maior no cabeçalho |
| 24/11/2026 | O dia a dia | Carrossel horizontal trocado por moldura fixa que troca de foto |
| 24/11/2026 | Fotos e contato | Fotos reais do Unsplash, lente na foto, foto de Brasília em órbita, seção de contato, rodapé completo |
| 23/11/2026 | Movimento | Animações na página toda, parallax, logo com órbita sozinha e no hover |
| 23/11/2026 | Primeira versão | Landing em Astro a partir dos briefings, do protótipo e do design system |

## O que trava o lançamento

São decisões suas, não código. A lista completa está em Órbita Fiscal: pendências e decisões.

- [ ] Revisão jurídica das 8 citações dos exemplos
- [ ] E-mail, Instagram, encarregado de dados, razão social e CNPJ reais (hoje provisórios, marcados “a confirmar”)
- [ ] Provedor de pagamento e emissão de nota fiscal
- [ ] Método de acesso à conta
- [ ] Textos legais redigidos ou revisados por advogado
- [ ] Onde hospedar o site e para onde o formulário de contato envia as mensagens

## Próximos passos

1. Páginas de Privacidade, Termos e Reembolso, com estrutura pronta e texto marcado para revisão.
2. Entrar e Checkout, assim que o método de acesso e o provedor de pagamento forem escolhidos.
3. Instalar o plugin e Portal do cliente.
4. Ajuda.
5. Baixar as fotos para o próprio site e publicar.
