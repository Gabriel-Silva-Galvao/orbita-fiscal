# Briefings das páginas da Órbita Fiscal

Nov 23, 2026 · @Gabriel Luis

Sete páginas no MVP e uma depois dele. Cada briefing diz o que a página precisa ter, o que a pessoa deve sentir ao chegar e para onde ela segue, para levar ao Claude Design e depois ao código.

## Como usar este documento

Leia a persona e o mapa, depois um briefing por vez. Todos os briefings têm os mesmos campos, na mesma ordem, para você colar um deles no Claude Design sem reescrever nada.

- **Objetivo**: o que a página precisa conseguir, em uma frase.
- **A pessoa chega com**: o estado de espírito e o que ela já sabe.
- **Impacto desejado**: o que ela deve sentir e pensar ao sair.
- **Conteúdo**: o que entra, em ordem, e o que fica de fora.
- **Conexões**: de onde ela vem e para onde segue.
- **Estados**: o que muda quando algo falha ou está vazio.
- **Pendências**: o que depende de decisão sua.

Para o Claude Design, cole a persona, o mapa, um briefing e o link do design system. Para o código, siga a mesma ordem e use o protótipo da etapa 1 como referência de tom e de layout. Texto marcado como “a definir” depende da seção de pendências, no fim.

## Persona

Renata é uma advogada de escritório pequeno que já usa o Claude no trabalho e quer parar de pesquisar o mesmo tema à mão. É uma persona de trabalho construída a partir do briefing. Vale validar com poucas conversas com advogados antes de fechar o texto.

- **Quem é**: advogada, atua em contencioso, escritório de poucas pessoas. Usa, decide e paga.
- **Como chega**: depois de uma apresentação, uma indicação ou um link em outro site. Já tem contexto e quer reconhecer o produto.
- **O que quer**: encurtar a pesquisa e ter profundidade na análise dentro de uma ferramenta que já conhece.
- **O que a faz comprar**: entender em uma leitura o que o plugin faz, ver uma tarefa dela resolvida e sentir segurança para pagar.

As dores abaixo têm código para o mapa de páginas usar.

| Código | Dor | Como aparece |
| --- | --- | --- |
| D1 | Tempo perdido em pesquisa manual e repetitiva | Abre várias bases e refaz a mesma busca por caso |
| D2 | Tokens gastos em consultas sucessivas | Pergunta várias vezes e ainda precisa conferir se reuniu o material |
| D3 | Medo de citar o que não existe | Tribunais já multaram advogado e parte por precedente inventado |
| D4 | Ferramenta que parece complicada | Quer entender e incorporar ao próprio ritmo, sem treinamento |
| D5 | Insegurança antes de pagar e instalar | Não sabe se vai funcionar, como instala e como pede o dinheiro de volta |
| D6 | Perder o fio depois da compra | Quer voltar, baixar atualizações e ver o que mudou na base |

## Mapa de páginas

O MVP tem sete páginas, todas ligadas a pelo menos uma dor da persona. A oitava, para equipes, fica para depois. O quadro em branco da etapa 2 mostra o mesmo mapa desenhado.

| Página | Rota | Dores que resolve | Chega de | Segue para | MVP |
| --- | --- | --- | --- | --- | --- |
| 1. Landing | / | D1, D3, D4 | Anúncio, apresentação, indicação, link | Planos na própria página, Entrar, Ajuda | Sim |
| 2. Entrar e criar conta | /entrar | D5 | Landing, e-mail de compra, Portal | Checkout se veio de um plano, senão Portal | Sim |
| 3. Checkout | /assinar/pro, /assinar/max | D5 | Landing, Entrar | Instalar | Sim |
| 4. Instalar o plugin | /instalar | D2, D5 | Checkout, Portal | Portal, Ajuda | Sim |
| 5. Portal do cliente | /conta | D6, D5 | Entrar, e-mail de atualização | Instalar, Checkout para trocar de plano, Ajuda | Sim |
| 6. Ajuda | /ajuda | D4, D5 | Qualquer página | Volta à página de origem | Sim |
| 7. Textos legais | /privacidade, /termos, /reembolso | D3, D5 | Rodapé, Checkout | Volta à página de origem | Sim |
| 8. Para equipes | /equipes | Expansão | Rodapé | Formulário de interesse | Depois |

## Página 1. Landing

A landing faz a pessoa entender, em uma leitura, o que o plugin faz, que ele roda no Claude e onde estão os planos. O protótipo da etapa 1 é a referência visual.

- **Objetivo**: levar o visitante qualificado até a escolha de um plano.
- **A pessoa chega com**: contexto parcial, vinda de uma apresentação, indicação ou link. Desconfia de promessas grandes sobre IA no direito.
- **Impacto desejado**: “entendi o que é, vejo uma tarefa minha ali e sei onde pagar”. Leveza, nada de excesso. Seriedade sem frieza.

**Conteúdo, nesta ordem**

1. **Cabeçalho**: logo, três links (Exemplo, Como funciona, Planos) e o botão Ver planos.
2. **Hero**: título “Pesquise o direito brasileiro e prepare suas peças na IA que você já usa”, uma frase de apoio, botão Ver planos, link Ver um exemplo, e a linha “A partir de R$ 50 por mês. Reembolso em até 7 dias”. O símbolo atrás tem um elétron em órbita lenta.
3. **Exemplo**: três abas (Pesquisar, Conferir o processo, Preparar a peça), cada uma com uma pergunta, as fontes consultadas e a resposta. Sempre marcado como ilustrativo.
4. **Como funciona**: três passos, assinar, instalar no Claude, conectar e perguntar.
5. **Planos**: Pro R$ 50 e Max R$ 75,90 por mês, lado a lado, com o Max em destaque. Cada botão leva ao Checkout daquele plano.
6. **Confiança**: fonte para conferir, rascunho e não sentença, e seus dados.
7. **Dúvidas**: quatro perguntas.
8. **Rodapé**: aviso de que respostas de IA exigem revisão, e links para Privacidade e Termos.

**Fica de fora**: números de acervo, depoimentos, vídeo, Academy e Business, até haver dado ou cliente real.

**Movimento**: entrada de blocos em 280 ms com 8 px de deslocamento, elétron em órbita lenta. Tudo visível sem rolar para disparar. Sem movimento quando a pessoa pede movimento reduzido.

**Conexões**: vem de anúncios, indicações e links. Vai para Checkout (botão do plano), Entrar (menu), Ajuda e textos legais (rodapé).

**Estados**: tela estreita reorganiza para uma coluna e o símbolo vem antes do título. Itens a definir aparecem com a marca tracejada “a definir” e não como promessa.

**Pendências**: diferença entre Pro e Max, cobertura da base, política de dados, revisão jurídica do exemplo.

## Página 2. Entrar e criar conta

Esta página dá à pessoa uma conta com o menor atrito possível, sem fazer ela esquecer o plano que escolheu.

- **Objetivo**: identificar a pessoa e devolvê-la ao ponto onde estava, o Checkout ou o Portal.
- **A pessoa chega com**: a decisão quase tomada. Qualquer campo a mais é motivo para desistir.
- **Impacto desejado**: calma e continuidade. “Já estou dentro e falta pouco.”

**Conteúdo**

1. Duas abas simples, Entrar e Criar conta, com o mesmo layout.
2. Se veio de um plano, uma faixa no topo: “Você escolheu o Max, R$ 75,90 por mês”, com link para trocar.
3. Criar conta: nome, e-mail e senha. Entrar: e-mail e senha, com “Esqueci a senha”.
4. Uma linha sobre dados e termos, com links para Privacidade e Termos.
5. Nenhum menu de navegação extra. Só o logo, que volta à Landing.

**Conexões**: vem da Landing, do e-mail de compra e do Portal. Segue para o Checkout do plano escolhido ou, sem plano, para o Portal.

**Estados**: e-mail já cadastrado (oferece Entrar), senha fraca (diz o que falta), e-mail de confirmação enviado, conta criada mas e-mail não confirmado.

**Pendências**: método de acesso, se e-mail e senha ou link por e-mail, e se haverá login com Google.

## Página 3. Checkout

O checkout remove a insegurança de pagar. A pessoa precisa saber o que paga, quando e como desistir.

- **Objetivo**: concluir o pagamento do plano escolhido.
- **A pessoa chega com**: o dedo no botão. Qualquer surpresa de preço ou prazo a faz sair.
- **Impacto desejado**: segurança e controle. “Sei exatamente o que estou contratando.”

**Conteúdo**

1. Resumo do plano à esquerda: nome, R$ 50 ou R$ 75,90 por mês, o que inclui e um link para trocar de plano.
2. Frase de cobrança sem letra miúda: “Cobrança mensal. Reembolso integral em até 7 dias.”
3. Pagamento à direita: cartão e Pix Automático (a confirmar).
4. Dados para nota fiscal: nome ou razão social e CPF ou CNPJ.
5. Botão “Pagar e receber o plugin”, com o valor no próprio botão.
6. Links para Termos e Reembolso. Nenhuma outra saída da página além do logo.

**Conexões**: vem da Landing, pelo botão do plano, ou de Entrar. Segue para Instalar quando o pagamento é aprovado.

**Estados**: processando (botão travado, sem clique duplo), cartão recusado (mensagem clara e outra forma de pagar), Pix aguardando confirmação com código copiável e contagem, pagamento aprovado.

**Pendências**: provedor de pagamento, emissão de nota fiscal, e se a assinatura renova sozinha no Pix.

## Página 4. Instalar o plugin

Esta é a página que transforma o pagamento em uso. O plugin do Claude precisa ser instalado e a conta, conectada. Se a pessoa travar aqui, pede reembolso.

- **Objetivo**: levar a pessoa à primeira pergunta respondida pela base, em poucos minutos.
- **A pessoa chega com**: alívio de ter pago e pressa de testar. Ainda não sabe como instala um plugin.
- **Impacto desejado**: competência e pequena vitória. “Funcionou de primeira.”

**Conteúdo**

1. Título “Seu plugin está pronto” e o plano contratado.
2. Passo 1, baixar o arquivo do plugin, com botão e versão atual.
3. Passo 2, no Claude, abrir o menu de plugins e enviar o arquivo. Uma imagem curta do caminho.
4. Passo 3, conectar a conta Órbita Fiscal, porque instalar o plugin não conecta o serviço sozinho.
5. Passo 4, testar com uma pergunta pronta e copiável, por exemplo a do exemplo da Landing.
6. Pergunta de fechamento, “Deu certo?”, com Sim (leva ao Portal) e Não (leva à Ajuda já no passo certo).

**Conexões**: vem do Checkout ou do Portal. Segue para Portal e Ajuda.

**Estados**: arquivo ainda sendo preparado, download expirado (gera novo link), pessoa sem plugins disponíveis no plano do Claude dela (explica o que fazer).

**Pendências**: formato de entrega e proteção contra cópia, e quais planos do Claude permitem instalar plugins. Confirmar os nomes dos menus em português antes de escrever o texto final.

## Página 5. Portal do cliente

O Portal mantém a pessoa por perto depois da compra. Precisa parecer familiar a quem já é cliente e deixar claro que há novidade quando a base muda.

- **Objetivo**: dar controle sobre o plano e entregar atualizações do plugin.
- **A pessoa chega com**: uma dúvida pontual (baixar de novo, ver a fatura, cancelar) ou curiosidade sobre o que mudou.
- **Impacto desejado**: controle e continuidade. “Está tudo aqui, e está atualizado.”

**Conteúdo, em quatro abas**

1. **Plugin**: versão atual, botão de baixar, e as novidades em lista curta com data (“o que mudou na base”). Aviso discreto quando há versão nova.
2. **Plano e pagamento**: plano atual, próxima cobrança, forma de pagamento, trocar entre Pro e Max, notas fiscais.
3. **Cancelar ou pedir reembolso**: duas ações separadas, em linguagem direta, com o prazo de 7 dias à vista. Sem labirinto.
4. **Conta**: nome, e-mail, senha, excluir conta.

**Conexões**: vem de Entrar e dos e-mails de atualização. Segue para Instalar (reinstalar), Checkout (trocar de plano) e Ajuda.

**Estados**: pagamento atrasado (faixa no topo com ação), reembolso solicitado (acompanhamento), versão nova disponível, sem plano ativo.

**Pendências**: frequência de atualização da base, canal dos e-mails de novidade, regra de troca de plano no meio do ciclo.

## Página 6. Ajuda

A Ajuda existe para a pessoa nunca ficar sozinha no passo 3 ou 4. Tem que ser curta e achar rápido.

- **Objetivo**: resolver as dúvidas de instalação, conexão e cobrança sem abrir chamado.
- **A pessoa chega com**: um problema concreto, com pouca paciência.
- **Impacto desejado**: “alguém pensou nisso”. Resposta em uma tela, sem rolar.

**Conteúdo**

1. Seis artigos curtos: instalar o plugin, conectar a conta, o plugin não aparece no Claude, como funciona a cobrança, pedir reembolso, privacidade dos dados.
2. Campo de busca só se passar de dez artigos. No MVP, uma lista basta.
3. Um canal de contato, com prazo de resposta dito com honestidade.

**Conexões**: aberta de qualquer página, com o link de volta à página de origem. Segue para Instalar e Portal.

**Estados**: sem resultado na busca (oferece contato), formulário enviado.

**Pendências**: canal de suporte (e-mail, formulário ou chat) e prazo de resposta.

## Página 7. Textos legais

Três textos que o advogado vai ler com atenção profissional. A clareza deles faz parte da confiança.

- **Objetivo**: informar sem assustar, com linguagem direta.
- **A pessoa chega com**: olhar de quem lê contratos. Vai notar o que está vago.
- **Impacto desejado**: seriedade e transparência.

**Conteúdo**

1. **Privacidade**: que dados a Órbita Fiscal guarda sobre a conta e sobre as consultas, por quanto tempo e para quê, com referência à LGPD. Responder cedo se as consultas treinam modelos.
2. **Termos de uso**: o que a assinatura dá, renovação, uso pessoal da licença e limites.
3. **Reembolso**: sete dias a partir da compra, como pedir e em quanto tempo o valor volta. O prazo é o mínimo do art. 49 do CDC.
4. Layout de leitura: coluna única, índice lateral no desktop, data de vigência no topo, sem animação.

**Conexões**: vem do rodapé, do Checkout e do Entrar. Volta à página de origem.

**Pendências**: os textos precisam ser redigidos ou revisados por advogado, com razão social e dados de contato da empresa.

## Página 8. Para equipes (depois do MVP)

Prepara a expansão para escritórios e entidades como a OAB, sem competir com a compra individual.

- **Objetivo**: coletar interesse de organizações que queiram o plugin para vários profissionais.
- **A pessoa chega com**: responsabilidade por uma equipe e perguntas sobre acesso, cobrança e privacidade.
- **Impacto desejado**: seriedade institucional. “Eles entendem como uma equipe trabalha.”

**Conteúdo**: uma frase sobre o uso em equipe, três pontos (acesso por pessoa, cobrança única, privacidade), formulário curto com nome, organização, número de profissionais e e-mail.

**Conexões**: link discreto no rodapé. Segue para uma confirmação de envio.

**Pendências**: só entra depois que o fluxo individual estiver operacional.

## Estados e erros que valem para todas as páginas

- **Carregando**: esqueleto leve na forma do conteúdo, sem girar nada na tela.
- **Erro de rede ou serviço**: diz o que aconteceu, o que a pessoa pode fazer e oferece tentar de novo. Nunca culpa a pessoa.
- **Sessão expirada**: pede entrar de novo e devolve à página onde estava.
- **Base em manutenção**: faixa discreta no Portal e na Instalar. A Landing não muda.
- **Movimento reduzido**: sem entrada animada nem órbita. A página fica completa em repouso.
- **Acessibilidade**: contraste mínimo AA nos dois temas, foco visível, uso só com teclado, texto alternativo no símbolo.
- **Celular primeiro**: toda página funciona em coluna única a partir de 360 px de largura.
- **Formatos**: valores como R$ 75,90, datas como 23/11/2026, textos em português do Brasil.

## Pendências em aberto

O que trava texto ou fluxo, em ordem de impacto. As dez primeiras vêm da etapa 1. O que já foi decidido em 23/11/2026 está no doc Pendências e decisões.

- [x] Diferença entre Pro e Max: por tarefa ou por volume?

    Decidido: por tarefa. Pro pesquisa; Max soma conferir o processo e preparar a peça.
- [ ] Como tratar o “100% de garantia”: sugestão de não prometer e oferecer fonte para conferir e reembolso de 7 dias.
- [ ] Cada resultado traz link ou inteiro teor da fonte?
- [ ] Cobertura da base e frequência de atualização, com data e critério.
- [ ] Somente Claude ou outras IAs também?
- [ ] Haverá plano anual e teste grátis?
- [ ] Entrega do plugin após a compra e proteção contra cópia.
- [ ] Razão social, política de dados e textos legais.
- [ ] Método de acesso: e-mail e senha, link por e-mail ou Google.
- [ ] Provedor de pagamento, Pix Automático e emissão de nota fiscal.
- [ ] Canal de suporte e prazo de resposta.
- [ ] Quais planos do Claude permitem instalar plugins.
- [ ] Revisão jurídica dos exemplos de uso da Landing.
