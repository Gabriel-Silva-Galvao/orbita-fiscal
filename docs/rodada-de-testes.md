# Rodada de testes (25/11/2026): ajustes pedidos, diagnóstico e plano

Documento de teoria: nada aqui foi executado ainda. Cada item tem o pedido, o que se sabe hoje, a proposta
e as dúvidas em aberto. A execução começa só depois que as dúvidas forem respondidas, um bloco por vez,
com teste e o ok do Gabriel antes do commit.

Legenda de status: **Diagnosticado** (causa achada), **Proposto** (caminho definido, falta o ok),
**Em aberto** (faltam respostas), **Só documentar** (não executar agora).

---

## Bloco A: correções e remoções

### 1 e 10. Login "que não salva" e sessão mais forte — Executado e testado (25/11/2026)

**Feito.** API com "manter conectado", aparelho, criação e último uso por sessão, `GET /auth/sessoes`, `DELETE /auth/sessoes/{id}` e `POST /auth/sair-de-todos` (61 testes). Cabeçalho com avatar e menu em todas as páginas com `Nav`; `/entrar` agora roda no servidor e manda quem já está logado para o `next` seguro, o Checkout do plano ou `/conta`. A lista de aparelhos ainda não aparece no Portal: entra no item 9. Não existe rota de troca de senha ainda; quando existir, deve chamar o encerramento de todas as sessões.

**Pedido.** A pessoa precisa entrar várias vezes; depois da compra, a landing não mostra que ela está logada.
Sessão com token melhorado e salva no navegador.

**Diagnóstico (testado em 25/11).** A sessão já é salva: cookie `orbita_sessao` HttpOnly, 30 dias, token guardado
só como SHA-256 no banco; `GET /auth/sessao` responde 200 e `/conta` abre sem novo login. A causa é visual:
a landing é gerada no build, então o cabeçalho sempre mostra "Entrar", e `/entrar` não redireciona quem já está
logado. A pessoa vê "Entrar", clica e entra de novo.

**Decisões.**
- **Teto da sessão: 30 dias** a partir do login, mesmo usando sempre. Depois disso, entra de novo (com o código).
- **"Manter conectado": marcado por padrão** na tela de entrar. Desmarcado, o cookie é de sessão do navegador
  (some ao fechar) e a sessão no servidor vale 12 horas.
- **Cabeçalho de quem está logado: avatar com as iniciais e menu** (Minha conta, Instalar o plugin, Ajuda, Sair).

**Como vai ser feito.**
1. API (`api/app/auth.py`):
   - `POST /auth/codigo` aceita `manter` (padrão `true`): cookie persistente de 30 dias ou cookie de sessão + 12 h.
   - Tabela `sessoes` ganha `criada`, `ultimo_uso`, `aparelho` (navegador e sistema, do User-Agent) e `manter`
     (migração em `db.py`). `GET /auth/sessao` atualiza `ultimo_uso` no máximo uma vez por minuto.
   - Token novo a cada login (já é assim) e **todas as sessões caem** ao trocar a senha ou excluir a conta.
   - Rotas novas para o item 9/10: `GET /auth/sessoes` (aparelhos conectados, marcando o atual),
     `DELETE /auth/sessoes/{id}` (sair de um aparelho) e `POST /auth/sair-de-todos`.
   - Testes de tudo isso.
2. Site:
   - Componente de cabeçalho ciente da sessão em todas as páginas: um script pequeno consulta `/auth/sessao`
     (com cookie) e troca "Entrar" + "Assinar" pelo avatar com menu. Sem sessão, nada muda. Sem salto de layout
     (o espaço do botão é reservado).
   - Menu do avatar acessível: abre com clique e Enter, fecha com Esc e clique fora; no celular, mesmo menu.
   - `/entrar` com sessão válida vai direto para `/conta` (ou para o `next`), no servidor (middleware), sem piscar.
   - Checkbox "Manter conectado" (marcada) na tela de entrar, enviada no `POST /auth/codigo`.
   - Depois da compra, a volta para a landing já mostra o avatar.
3. Produção (anotado): `COOKIE_SECURE=true` e site e API no mesmo domínio (ex.: `api.` do domínio do site),
   para o cookie continuar first-party.

**Teste.** Entrar com e sem "Manter conectado"; fechar e reabrir o navegador; landing, /bases e Ajuda mostrando o
avatar; menu no computador e no celular; `/entrar` logado indo para `/conta`; Sair; sessão expirada pedindo login;
testes da API.

### 2. Rodapé flutuando e incompleto — Executado e testado (25/11/2026)

**Decisões.** Dados ainda inexistentes entram com o marcador "a definir"; nas páginas de foco, versão curta.
**Feito.** Rodapé completo com a faixa Empresa (razão social, CNPJ, endereço), Atendimento (e-mail, horário, formulário) e Pagamento (cartão, Pix, boleto e "Pagamento processado pelo Asaas"), mais o link "O que a Órbita cobre". Nas páginas de foco (Entrar, Checkout, Portal, Instalar), rodapé curto com ©, razão social, CNPJ, Asaas e links legais, sempre colado embaixo (a página ocupa no mínimo a altura da janela). Os dados ficam em `src/data/site.ts` (`company`), e os marcadores somem quando forem preenchidos.

**Pedido.** Nas páginas simples (pagamento, boas-vindas) o rodapé flutua no meio da tela; faltam informações.

**Proposta.**
- Layout com `min-height: 100dvh` e o conteúdo crescendo (`flex: 1`), para o rodapé colar embaixo.
- Rodapé completo: razão social, CNPJ, endereço, contato e horário de atendimento, links legais
  (Privacidade, Termos, Reembolso, Cookies), Ajuda, redes, formas de pagamento aceitas (cartão, Pix, boleto),
  selo "Pagamento processado pelo Asaas" e ano.
- Nas páginas de foco (pagamento e entrar), uma versão curta com os mesmos dados essenciais.

**Dúvidas.** Razão social, CNPJ, endereço e redes continuam "a definir": entram como marcadores até haver CNPJ?

### 4. QR Code do Pix não aparece — Executado e testado (25/11/2026)

**Feito.** A simulação do Asaas gera o copia e cola no padrão oficial (BR Code/EMV, com CRC16 conferido pelo valor de referência 29B1) e um QR de verdade em PNG (biblioteca `segno` 1.6.6, em `api/requirements.txt`). Teste novo na API (62 testes). No Checkout, o QR aparece e um app de banco consegue ler o código; a chave é de simulação, então o pagamento não é encontrado.

**O que se sabe.** O copia e cola funciona. A simulação do Asaas devolve como QR um PNG de 1×1 pixel
(`api/app/asaas_sim/store.py`, `pix_qrcode`).

**Proposta.** Gerar o QR de verdade a partir do payload Pix na simulação (biblioteca Python `segno` ou
`qrcode`). No Asaas real, a imagem já vem pronta (`encodedImage`), então o site não muda.

### 6. Baixar o plugin — Proposto

**O que se sabe.** O botão simula o download porque ainda não há arquivo do plugin nem formato definido.

**Proposta.** Um `orbita-plugin-demo.zip` simulado (README explicando que é demonstração, manifesto de exemplo
e as instruções), servido pela API com link que expira, como será o real. Registrar no planejamento que o
real depende do servidor MCP e do formato da loja do Claude.

### 14. Cards de geração mais vivos — Proposto

Hover com leve aumento (scale 1.01 a 1.02), sombra e borda acendendo; transição curta e nada para quem pede
movimento reduzido.

### 15. Títulos sem ponto final e cards da segunda seção — Executado e testado (25/11/2026)

**Decisão.** "Segunda seção" = "O que a Órbita consulta", que hoje vem logo depois do topo.
**Feito.**
- Sem ponto final nos títulos: topo, O que a Órbita consulta, comparativo ("A mesma pergunta, com e sem a Órbita"),
  Como funciona, IAs, Planos ("Dois planos: escolha pelo trabalho que você faz"), Antes de assinar, Comece hoje,
  Contato e 404.
- Cards de "O que a Órbita consulta": cada um mostra o total de documentos do grupo em destaque (ex.: 7,1 milhões,
  em 36 bases), o nome do grupo, as fontes em etiquetas e "Ver as bases →". No hover, o card sobe, ganha sombra e
  a faixa verde do topo se completa. O card leva a `/bases?tipo=...#todas`, com a lista já filtrada pelo grupo.
- `/bases` aceita `?tipo=` com um ou mais tipos.
**Pendência.** A imagem de compartilhamento (og.png) ainda tem o título com ponto: regerar com `npm run og`.

### 16. Átomo sempre atrás do texto no celular — Substituído pelo item 19

### 19. Topo sem a logo e com fundo parado — Executado e testado (25/11/2026)

**Decisões.**
- **Fundo:** as órbitas largas continuam desenhadas, mas os dois pontos verdes **param de viajar**.
  Ficam parados num lugar bonito da órbita (sem `animateMotion`).
- **Logo:** sai **só o átomo grande** de lítio atrás do cartão de resposta. A logo do cabeçalho fica.

**O que muda no código.**
- `src/components/Hero.astro`: sai o bloco `.hero-atom` (anéis e `Symbol`) e o CSS dele, incluindo as regras
  de celular; o cartão de resposta volta a ocupar a largura natural (sem o deslocamento que abria espaço
  para o átomo); os pontos do fundo viram círculos estáticos.
- `src/scripts/gerar.ts`: sai a aceleração do átomo (`data-boost`) durante a "consulta à base".
  A geração ao vivo da resposta, o status e as fontes continuam iguais.
- O `orbit.ts` continua (é usado pela logo do cabeçalho e por outras seções).

**Efeito colateral.** O item 16 (átomo atrás do texto no celular) deixa de existir.

**Teste.** Build; topo sem o átomo no computador e no celular; pontos parados; geração ao vivo funcionando;
CLS do topo igual ou menor; nada de rolagem lateral no celular.

### 21. Tirar a linha "Menos tempo caçando lei…" — Executado e testado (25/11/2026)

**O que sai.** A seção inteira `#dia-a-dia` de `src/pages/index.astro` (só tem essa frase), com os estilos
`.linha`, `.linha-texto` e `.linha-destaque`.

**Efeitos que precisam ir junto.**
- Rodapé: o link "O dia a dia" (`/#dia-a-dia`, em `src/components/Footer.astro`) sai, para não virar link quebrado.
- Ordem das seções: o comparativo (fundo normal) passa a encostar em "Como funciona" (fundo alternado).
  A alternância de fundos continua certa, sem duas seções iguais seguidas.
- A frase não é reaproveitada em outro lugar (a ideia de "menos busca, mais revisão" já aparece no comparativo).

**Teste.** Build, página sem a seção, rodapé sem o link, nenhum `#dia-a-dia` restante no código,
CLS e rolagem iguais.

### 22. Tirar a seção "Feito para quem assina o que entrega" — Executado e testado (25/11/2026)

Sai a seção inteira, com a foto do Congresso e os três pontos de confiança.

**O que sai.**
- A seção em `src/pages/index.astro` (título, frase "Direito brasileiro, com as garantias da lei brasileira",
  a foto e os três pontos) e a lista `trust` do topo do arquivo.
- O componente `src/components/SceneBrasilia.astro`, que só é usado ali.
- A foto `congresso` em `src/data/photos.ts` e o crédito dela na janela "Créditos das fotos" do rodapé.

**Os três pontos de confiança não se perdem.** O FAQ "Antes de assinar" já cobre os três:
"E se a IA errar?" (fonte para conferir e rascunho, não sentença) e "O que acontece com meus dados?".
Eles também são candidatos a voltar na página de boas-vindas (item 3), num formato próprio.

**Efeitos que precisam ir junto.**
- Fundos: Planos (normal) passa a encostar em "Antes de assinar" (alternado). A alternância continua certa.
- O parallax (`data-parallax` em `motion.ts`) continua sendo usado no Contato; nada a mudar no motor.
- Conferir que nenhum link aponta para a seção (ela não tem `id` de âncora, então o menu e o rodapé não mudam).

**Teste.** Build, página sem a seção, nenhuma referência a `SceneBrasilia` ou `congresso`, créditos das
fotos atualizados, CLS e rolagem iguais.

**Decidido (25/11/2026).** Os três pontos também voltam na página de boas-vindas (item 3), além do FAQ. O texto deles fica guardado aqui para isso:
- Fonte para conferir: cada resultado vem com a norma, a súmula ou o julgado de onde saiu, para você abrir e conferir.
- Rascunho, não sentença: o plugin pesquisa e prepara. A decisão, a revisão e a assinatura continuam com você.
- Seus dados: dizemos o que guardamos, por quanto tempo e se as consultas treinam algum modelo (a definir).

---

### 23. Header fixo igual em todo o site, header que muda e transição suave — Executado e testado (25/11/2026)

**Pedido.** Ao abrir as bases, o header mudava por completo; a pessoa sem assinatura precisa de um header fixo
para andar pelo site, e de um header que muda (pesquisar exemplos). Transição entre páginas mais suave, com um
carregamento da Órbita.

**Referências.** Padrão de duas camadas (navegação global fixa + barra da página com as seções, que aparece ao
rolar e acende a seção atual), descrito em sistemas de design como o da Universidade de St Andrews e no
artigo da LogRocket sobre navegação fixa. Transição entre páginas com as View Transitions entre documentos
(`@view-transition { navigation: auto }`): Chrome e Edge 126+, Safari 18.2/26.2; no Firefox, parcial; quem
não suporta só troca de página sem animação.

**Decisões.** Links globais: Como funciona, O que cobre, Planos, Ajuda. Header que muda: barra da página ao rolar
e "Assinar" em destaque só depois da primeira tela. Transição: esmaecer com o header parado + átomo se demorar.

**Feito.**
- `Nav.astro`: os mesmos quatro links em todas as páginas públicas, com a página atual marcada; no celular,
  numa linha rolável abaixo do logo (antes sumiam). O `links` de cada página virou a barra da página.
- Barra da página: aparece depois de 60% da primeira tela, flutuando abaixo do header (não empurra o conteúdo),
  e acende a seção visível. Landing: O que consulta, Com e sem a Órbita, Como funciona, Funciona com, Planos,
  Dúvidas. /bases: Por tipo, Mapa, Todas as bases. Ajuda, textos legais e 404: sem barra.
- "Assinar" discreto (contorno) no topo e verde com brilho depois da primeira tela. Ajuda, legais e 404 passaram
  de "Ver planos" para "Assinar".
- Transição: o conteúdo esmaece (160 ms) e o novo entra subindo (340 ms); o header fica parado
  (`view-transition-name`). Com movimento reduzido, sem animação.
- Carregamento: `src/scripts/carregando.ts` mostra o átomo girando no centro se a próxima página demorar mais de
  250 ms; troca rápida não mostra nada; âncora da mesma página não mostra; volta pelo histórico esconde.

**Testes.** Header global e página atual (landing, /bases, Ajuda); barra e "Assinar" mudando ao rolar; seção
acesa; troca de página com o header parado; átomo não aparece em âncora; celular sem rolagem lateral; todas as
páginas respondendo (200, e 404 na inexistente); 62 testes da API; build limpo.
**Não deu para ver no painel de teste:** a animação da troca e o átomo de verdade, porque o painel estava oculto
e o navegador pausa as animações nesse estado. Conferir abrindo o site no navegador.

### 24. Botão do header conforme o plano — Executado e testado (25/11/2026)

**Pedido.** Logado sem plano: "Assinar", para saber que pode ter um plano. Só com o Pro: "Upgrade". Com o Max:
definir uma ideia.

**Feito.** Rota leve `GET /billing/plano` (só o plano e se dá acesso, sem consultar o Asaas; teste novo, 63 no
total). O header de quem está logado mostra, ao lado do avatar:
- sem plano, cancelado ou reembolsado sem acesso: **Assinar** → planos da landing;
- pagamento pendente (Pix ou boleto): **Concluir assinatura** → Portal, aba do plano;
- Pro: **Upgrade para o Max** → Portal, aba do plano (onde fica a troca de plano);
- Max: selo **Max** no avatar e o atalho **Criar alerta** → Portal, aba de alertas por tema, que é só do Max.
  A ideia: quem já tem tudo ganha um atalho para o recurso exclusivo, em vez de um botão de venda.

**Testes.** Quatro contas de teste locais: pendente, Pro, Max e sem plano, cada uma com o botão certo;
celular sem rolagem lateral.
**Pendência.** A troca de Pro para Max no Portal ainda não tem regra de cobrança no meio do mês (marcada "a definir").

## Bloco B: landing

### 13. Exemplos sorteados no topo e logo no "com a Órbita" — Em aberto

**Pedido.** A cada recarga, um exemplo diferente na resposta do topo; o comparativo continua com as 5
perguntas fixas; a coluna com a Órbita ganha a logo animada. Exemplos tirados do artefato da pesquisa.

**O que se sabe.** O painel "Comparação por pergunta" tem 11 perguntas; o comparativo usa as 5 tributárias.

**Proposta.** O topo sorteia entre as perguntas do painel (com trecho e fontes reais), no servidor ou no
navegador sem causar salto de layout. Coluna "com a Órbita" com o símbolo girando ao lado do nome.

**Dúvidas.** Sortear entre as 11 ou só entre as 6 que não estão no comparativo? Há mais perguntas além
dessas 11?

### 20. Página "O que a Órbita cobre" — Executado e testado (25/11/2026)

**Feito.** Levantamento em `scripts/cobertura/` (108 bases, 10.374.017 documentos; tabela em
`docs/cobertura-levantamento.md`, conferida pelo Gabriel); página `/bases` com contadores, grupos por tipo,
mapa real do Brasil por estado (pacote @svg-maps/brazil 2.0.0, CC BY 4.0, autorizado pelo Gabriel em 25/11/2026; crédito no rodapé) com sigla no hover, estado que sobe ao ser escolhido com total e maior acervo, e painel com cada base abrindo seus detalhes; lista paginada (12 por página); faixa de venda, busca (aceita nome do estado), filtros e CTA final;
na landing, a seção ganhou os totais e o botão "Ver tudo o que a Órbita cobre". Testado no computador e no celular.

**Pedido.** A seção "O que a Órbita consulta" fica na landing (mais completa) e ganha um botão de venda para
uma página nova, totalmente detalhada e interativa: quantidade de documentos, bases, tudo.

**Decisões.**
- Números: **contar nos próprios plugins**, e o Gabriel confere antes de publicar.
- Escopo: **tributário e jurídico** (plugins orbita-fiscal e orbita-juridica).
- Interações: **mapa do Brasil, filtros por tipo, busca e contadores animados**.
- Período coberto e atualização: **por base**.

**De onde saem os números (testado em 25/11/2026).** Cada base dos plugins tem um script `buscar.py`
com `--resumo`, que devolve os números do dia direto do servidor. Exemplo real, CARF:
475.797 acórdãos, de 30/05/1973 a 09/10/2026, 466.525 com inteiro teor, última carga 03/11/2026,
atualização toda noite, mais a divisão por órgão, instância, resultado e votação.
O plugin orbita-fiscal tem 95 bases; o orbita-juridica, mais 16.

**Como o levantamento vai ser feito (na execução).**
1. Um script roda o `--resumo` de todas as bases **em paralelo** (vários processos ao mesmo tempo) e grava
   um arquivo `src/data/cobertura.json` com, por base: nome, plugin, tipo, UF, órgão, quantidade de documentos,
   quantos com inteiro teor, primeira e última data, data da última carga e frequência de atualização.
2. O Gabriel confere a tabela antes de ir ao ar. Base que não responder fica marcada "a confirmar", sem número.
3. O script fica no projeto (`scripts/cobertura/`) para atualizar os números quando quiser; o site não consulta
   o servidor ao vivo (página estática e rápida).

**Tipos (para os filtros).** Legislação; tribunais superiores (STF, STJ); Justiça Federal (TRF1 a TRF6 e turmas
recursais); Justiça estadual (TJs); contencioso administrativo federal (CARF); contencioso administrativo
estadual (TIT-SP, CCMG, TATEs, CONSEF, conselhos); consultas e pareceres (RFB, PGFN, SEFAZ); controle externo
(TCU, TCE-MG); jurídico geral (TJMG por área, TRF6 previdenciário).

**Estrutura da página `/bases`.**
1. Topo de venda: total de documentos e de bases em contadores animados, frase de valor e botão "Assinar".
2. Mapa do Brasil clicável: cada estado acende conforme a cobertura; ao clicar, um painel lista o TJ,
   o conselho administrativo, as consultas da SEFAZ e a legislação do estado, com números.
3. Filtros por tipo e busca ("tem o CARF?", "Bahia", "PGFN"), filtrando a mesma lista ao vivo.
4. Lista de bases em cartões: nome, quantidade, período, atualização e o que dá para fazer com ela.
5. Faixas de venda no meio da página (comparativo com e sem a Órbita, garantia de 7 dias) e CTA final.
6. Nota de transparência: data do levantamento e o que cada número significa.

**Na landing.** A seção "O que a Órbita consulta" continua, ganha os totais e o botão
"Ver tudo o que a Órbita cobre" para `/bases`.

**Ainda em aberto.**
- Mostrar as bases que estão no plugin mas fora do escopo de venda (se houver alguma)?
- O mapa só cobre estados com base própria; os outros aparecem apagados com "cobertura pelos tribunais
  superiores e federais". Confirmar o texto.

---

## Bloco C: plataforma do assinante

### 3. Página de boas-vindas depois da compra — Em aberto

**Pedido.** Página receptiva, com animações como as da landing, apresentando o produto, o que a compra
liberou e por que confiar.

**Proposta inicial.** Saudação com o nome, o átomo e uma animação de "acesso liberado"; o que o plano dá
(Pro ou Max); três passos para começar (instalar, conectar, primeira pergunta) com progresso; uma pergunta
guiada com resposta animada; sinais de confiança (garantia de 7 dias, bases consultadas, LGPD, contato humano) e os três pontos
que saíram da landing no item 22 (fonte para conferir, rascunho não sentença, seus dados).
É também onde a animação de explosão do átomo, já planejada, pode tocar.

**Dúvidas.**
1. Qual a primeira ação: instalar, fazer uma pergunta de teste ou conhecer o plano?
2. Pro e Max com conteúdo diferente?
3. Primeira pergunta guiada com resposta pronta animada?
4. Quais sinais de confiança?

### 5. Cabeçalho e interface de quem está logado — Em aberto

**Pedido.** Elementos de login no cabeçalho (inclusive na landing) e um Portal com cara de produto novo,
no mesmo design.

**Proposta.** Ver item 1 para o cabeçalho. No Portal: barra lateral com o símbolo e o nome do plano, painel
inicial com status do plugin e atalhos, e o mesmo sistema visual da landing (cores, tipografia, átomo).

### 8. Uma página com design próprio para cada aba — Em aberto

**Pedido.** Cada aba vira página própria, mais complexa; cabeçalho mais intuitivo; responsividade com
interação no celular.

**Proposta inicial de páginas.** Início (painel), Plano e pagamento, Faturas, Uso e status do plugin,
Instalar e conexões, Novidades da base, Ajuda e suporte, Conta e segurança.

**Dúvidas.** Quais páginas entram? No celular: menu inferior (estilo app) ou lateral que abre?

### 9. Aba de conta completa — Proposto

**Básico.** Nome, e-mail, senha, foto ou iniciais.
**Avançado.** Aparelhos conectados e sair de todos (item 10), preferências de e-mail (novidades, resumo
semanal no Max), tema, dados da nota fiscal (CPF ou CNPJ, razão social), baixar meus dados (LGPD),
excluir conta.

### 11. Checkout com cara de pagamento — Em aberto

**Pedido.** Visual sóbrio, branco e com as cores usuais de pagamento (como Amazon e Mercado Livre), sem seguir
o design do site.

**Proposta.** Fundo branco, tipografia de sistema, cinzas neutros e um azul ou verde de ação; resumo do pedido
fixo ao lado; selos de segurança e do Asaas; passos numerados; nada de animação.

**Dúvidas.** Fica branco também quando o site está no modo escuro?

---

## Bloco D: só documentar agora

### 7. Vídeo passo a passo da instalação — Só documentar

Vídeo curto (60 a 90 s) com cada passo do download e da conexão do plugin, na página Instalar e na de
boas-vindas. Pode ser feito com Remotion (skill da organização) depois que o plugin real existir, para mostrar
as telas verdadeiras do Claude.

### 12. Depoimentos com foto na boas-vindas — Só documentar

Só com clientes reais e autorização por escrito (uso de nome, foto e texto). Depoimento inventado é
publicidade enganosa (CDC, art. 37, e Código do CONAR). Plano: deixar o espaço pronto e pedir depoimentos
aos primeiros clientes do período de teste.

### 17. Documentação completa do backend e da segurança — Proposto (executar no bloco A ou B)

Documento com: arquitetura, cada rota e contrato, banco e tabelas, fluxo de login e 2FA, sessão, cobrança
e webhooks do Asaas, configuração (`.env`), testes, e uma análise de segurança por ponto crítico:
senhas (scrypt), códigos e tokens (hash), cookies, CORS, força bruta e limites, CSRF, webhook do Asaas
(token), dados pessoais e LGPD, segredos, registros, publicação (HTTPS, cabeçalhos), e o que falta.

### 18. Estante de livros de direito interativa — Só documentar

Os livros da antiga cena da biblioteca viram uma estante animada; a pessoa puxa um livro e ele se abre
mostrando um resumo pronto feito pelo Claude Opus 5.5 com a Órbita sobre aquele tema.

**Dúvidas.** Cada livro é uma área do direito (tributário, civil, trabalhista) ou uma obra real? Os resumos
saem do painel da pesquisa?

### Animação de explosão do átomo — Continua a última etapa

---

## Ordem proposta de execução

1. Bloco A, um item por vez: 1 e 10, 4, 2, 19, 21, 22, 15, 14, 6.
2. Documento do item 17.
3. Bloco B: 13 e 20 (depois das respostas).
4. Bloco C: 5 e 8 juntos, depois 9, 11 e 3.
5. Bloco D e a animação de explosão.
