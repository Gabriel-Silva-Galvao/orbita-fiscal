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

### 6. Baixar o plugin — Executado e testado (25/11/2026)

**Por que o download real não funciona (documentado).** Ainda não existe o arquivo do plugin: ele depende do
servidor MCP (que já existe e será ligado depois) e do formato aceito pela loja do Claude. Até lá, o site
entrega um pacote de demonstração com o mesmo fluxo do real.

**Feito.**
- API `app/plugin.py`: `POST /plugin/link` (exige sessão e assinatura com acesso; senão 403) gera um link que vale
  15 minutos; `GET /plugin/baixar/{token}` entrega `orbita-plugin-0.0.0-demo.zip` como anexo (410 se expirou, 404
  se o link não existe). Token só como SHA-256; links vencidos são apagados.
- O zip traz `README.md` dizendo que é DEMONSTRAÇÃO, um exemplo de manifesto (`.claude-plugin/plugin.json`) e um
  exemplo de skill. É montado na memória.
- Instalar: "Baixar o plugin" pede o link e baixa sem sair da página; avisa que é demonstração e até que horas o link
  vale; sem assinatura ativa, explica que o download depende dela.
- 3 testes novos (66 no total).

**Quando o plugin real existir.** Trocar `montar_zip()` pelo arquivo publicado; o fluxo continua igual.

### 14. Cards de geração mais vivos — Executado e testado (25/11/2026)

**Feito.** No topo, ao passar o mouse, a resposta sobe 4 px e cresce 2% com sombra e contorno verde, e a pergunta
acompanha (2 px). No comparativo, cada coluna sobe 4 px e cresce 1,5% com sombra; a coluna com a Órbita ganha também
um brilho verde. Transição de 320 ms; com movimento reduzido, nada se mexe. Testado com o mouse nas duas áreas.

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

### 13. Exemplos sorteados no topo e logo no "com a Órbita" — Executado e testado (25/11/2026)

**Fonte.** O painel "Comparação por pergunta" (artefato da pesquisa) tem 11 perguntas, com o texto integral das
respostas: as 5 tributárias do comparativo e 6 do jurídico geral (TJMG em improbidade, sócio retirante,
negativação, alimentos e plano de saúde; TRF6 em tempo especial). Os dados vieram de uma cópia local do painel,
salva numa sessão anterior.

**Feito.**
- `scripts/exemplos/gerar_topo.py` gera `src/data/topo.json`: para cada pergunta, o primeiro parágrafo da resposta
  com a Órbita (sem mudar nada) e até 5 fontes citadas, sem repetir a mesma fonte escrita de jeitos diferentes.
- O topo sorteia uma das **11** a cada visita. A troca é feita por um script curto logo depois do cartão, antes da
  primeira pintura: nada pula. Sem JavaScript, fica a de crime tributário.
- Nas 5 tributárias, "Compare com a resposta sem a Órbita" abre a aba da mesma pergunta no comparativo; nas outras,
  o link diz "Veja a diferença com e sem a Órbita".
- O comparativo continua com as mesmas 5 perguntas.
- Logo animada (`MiniAtomo.astro`): órbitas girando e um elétron correndo ao lado de "Claude Opus 5.5 com a Órbita",
  no cartão do topo e no cabeçalho da coluna com a Órbita. Parada com movimento reduzido.

**Testes.** As 11 aparecem no sorteio; recarregar troca a pergunta; o sorteio não move a página; o link abre a aba
certa; logo presente no topo e nas 5 colunas.
**Pendência.** As 6 perguntas do jurídico geral também precisam da revisão jurídica antes de ir ao ar, como as 5.

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

## Bloco E: mudança dos planos e do público (25/11/2026)

Mudança de teoria pedida pelo Gabriel depois de fechar o bloco C. **Vem antes do bloco C na execução**, porque muda os
planos que o Portal, o checkout, a boas-vindas e o header usam.

### 25. Três planos: Bronze, Prata e Ouro — Executado e testado (25/11/2026)

**Feito.** API (`PLANOS` e validação; 72 testes), `src/data/plans.ts` (planos, `planList`, `aPartirDe`, `upgradeDe`),
novo `PlanCard.astro` (card branco, preço grande, ✓, "a definir" em cinza, selo "Mais escolhido" no Prata), landing
(título "Três planos: escolha pelo quanto você pesquisa", três cards, FAQ, CTA final), checkout (`/assinar/bronze|prata|ouro`,
"Trocar para" com os outros dois), Entrar (troca de plano em ciclo), middleware, Portal (upgrade Bronze → Prata → Ouro,
recursos do Ouro), header (Upgrade para o Prata/Ouro; selo Ouro), Instalar, Ajuda, Termos, /bases e textos
"a partir de R$ 19,90". Banco de desenvolvimento migrado (Pro → Prata, Max → Ouro). `/assinar/pro` agora dá 404.
**Pendências.** As especificações de cada plano (quando vierem, editar `plans.ts` e `PLANOS` na API). A imagem de
compartilhamento ainda não fala de preço. O guia antigo ainda cita Pro/Max em trechos de histórico.

**Pedido.** Sai Pro (R$ 50) e Max (R$ 75,90). Entram três planos de assinatura mensal:

| Plano | Preço | Papel |
|---|---|---|
| Bronze | R$ 19,90/mês | entrada |
| **Prata** | R$ 59,90/mês | **em destaque, "Mais escolhido"** |
| Ouro | R$ 119,90/mês | o mais completo |

**Especificações de cada plano: serão definidas no futuro.** Até lá, cada card mostra o que é comum aos três (a base
inteira, a fonte em cada resposta, funciona no Claude, cancelar quando quiser, garantia de 7 dias) e, no lugar do que
diferencia os planos, a marca "a definir". **O Ouro herda os recursos que hoje são do Max**: alertas por tema, resumo
semanal e acesso antecipado. Quando as especificações chegarem, basta editar `src/data/plans.ts` (site) e a tabela de
planos da API; o resto lê dali.

**Design dos cards** (referências: páginas de planos da Anthropic e do ChatGPT):
- três cards lado a lado (no celular, um embaixo do outro, com o Prata primeiro), **sempre brancos**, também no modo
  escuro, texto quase preto e cantos arredondados;
- uma cor só de destaque, no Prata: borda e selo "Mais escolhido", e o botão principal; nos outros, botão com contorno;
- em cada card: nome, para quem é (uma linha), preço grande com "/mês", botão, e a lista de itens com um ícone de
  check; os itens "a definir" aparecem em cinza;
- abaixo dos três, uma faixa "Planos empresariais" (item 26) e a linha de garantia e formas de pagamento.

**O que muda no código.** Tudo que fala em Pro/Max:
- API: `PLANOS` em `billing.py` (`bronze`, `prata`, `ouro`, com os preços), validação dos planos, testes;
- site: `src/data/plans.ts`, os cards da landing, `/assinar/[plano]` (agora `/assinar/bronze|prata|ouro`), o middleware
  (`pro|max`), `/entrar?plano=`, Portal (marca "Max" vira "Ouro"), Instalar, Ajuda, Termos, Reembolso, FAQ, header
  (item 24: Bronze → "Upgrade para o Prata", Prata → "Upgrade para o Ouro", Ouro → selo "Ouro" e "Criar alerta"),
  textos do bloco C e o guia.
- Contas de teste locais com Pro/Max: migrar para Prata/Ouro no banco de desenvolvimento (não há clientes reais).

### 26. Área de planos empresariais com contato animado — Executado e testado (25/11/2026)

**Feito.** API `app/contato.py` (`POST /contato/empresarial`: validação, isca contra robôs, 5 mensagens por IP por hora,
registro na tabela `contatos`, envio por SMTP para `CONTATO_EMAIL` com resposta para quem escreveu e confirmação para
a pessoa; 4 testes, 76 no total), envio de e-mail genérico em `app/correio.py`; `ContatoEmpresarial.astro` (envelope
sobe, aba abre, carta sai e vira a janela de e-mail já endereçada e preenchida com a conta; ao enviar, a carta volta, a
aba fecha e o envelope voa; Esc, X, Cancelar ou clique fora fazem o caminho inverso; direto, sem envelope, com movimento
reduzido); `EmpresasFaixa.astro` abaixo dos planos; página `/empresas`; rodapé e `/bases` apontando para ela.
**Testes.** Fases da animação na ordem, foco na mensagem, envio registrado no banco, confirmação, fechar por Esc, celular
sem rolagem lateral. Sem SMTP, a tela avisa que é demonstração.

**Pedido.** Área de planos empresariais; "Entrar em contato" com o e-mail da Órbita para negociar; animação de abrir uma
caixa de e-mail ao clicar (explorar a ideia).

**Como vai ser.**
- Na seção de planos, abaixo dos três cards: faixa "Para escritórios, empresas e equipes", com o que costuma entrar
  numa negociação (vários usuários, cobrança única, nota para a empresa, condições sob medida) e o botão
  **"Entrar em contato"**. Também uma página `/empresas` com o mesmo conteúdo mais completo (o link "Para escritórios"
  do rodapé, que hoje leva a uma página que não existe, passa a levar para ela).
- **Animação da caixa de e-mail (ideia explorada):**
  1. ao clicar, um envelope fechado sobe do botão até o centro da tela, com o fundo escurecendo;
  2. a aba do envelope abre (giro 3D de cima para baixo) e uma carta desliza para fora;
  3. a carta cresce e vira uma janela de e-mail: "Para: contato@… (Órbita)", "Assunto: Plano empresarial", e os
     campos nome, empresa, e-mail, número de usuários e mensagem, já com o cursor na mensagem;
  4. ao enviar, a carta dobra, volta para o envelope, o envelope fecha e "voa" para fora com um rastro, e aparece
     "Mensagem enviada. Respondemos em até X dias úteis" (prazo a definir);
  5. fechar (X, Esc ou clique fora) faz o caminho inverso, sem enviar.
  Com movimento reduzido, a janela de e-mail aparece direto, sem envelope. Acessível: foco preso na janela, Esc fecha,
  leitor de tela anuncia "Escrever para a equipe da Órbita".
- **Envio:** formulário na própria janela; a API recebe (`POST /contato/empresarial`, com limite de envios por IP e
  verificação contra robôs) e manda para o e-mail da Órbita pelo SMTP (`app/correio.py`), com cópia de confirmação
  para quem escreveu. Sem SMTP configurado (desenvolvimento), a mensagem fica registrada e a tela mostra que é
  demonstração. O e-mail de destino continua "a confirmar" (`src/data/site.ts`).

### 27. Público: advogados, contadores e empresários em todo o site — Executado e testado (25/11/2026)

**Feito.** Topo com "Para advogados, contadores e empresários" no lugar de "Plugin para Claude"; nova seção "Para
advogados, contadores e empresários" (`#para-quem`, também na barra de seções) com um card por público, nessa ordem,
cada um com o que a Órbita resolve e uma pergunta de exemplo; descrição da página para o Google e do rodapé sem
"suas peças"; Contato com "Escritórios, contabilidades e empresas"; tutoriais e IAs com "TI da empresa ou do
escritório"; Termos e Reembolso falando em peças, pareceres, laudos e documentos, não só em peças; link do rodapé
"Para escritórios e empresas" (vai para o contato até a página `/empresas` do item 26).
**Pendência.** A imagem de compartilhamento (og.png) ainda não cita o público: regerar com `npm run og`.

**Pedido.** Deixar claro que a Órbita é para **advogados, contadores e empresários**, nessa ordem, e nunca limitar o
público a advogados, no site inteiro.

**Como vai ser.**
- Revisar todos os textos (landing, /bases, planos, Ajuda, Termos, FAQ, meta descrições e dados estruturados, imagem de
  compartilhamento) trocando o que fala só de advogado, escritório de advocacia ou "peça" por formulações que valem
  para os três, ou citando os três nessa ordem.
- Topo da landing: uma linha "Para advogados, contadores e empresários" acima ou abaixo do título.
- Exemplos de uso por público na seção de planos ou numa faixa própria: advogado (fundamentar a peça), contador
  (conferir crédito, regime, obrigação acessória), empresário (entender o risco antes de decidir).
- Termos de uso: o texto que hoje fala em "revisão profissional" continua, sem restringir a advogados.
- Levantamento inicial: as palavras "advogado", "escritório", "peça", "Pro" e "Max" aparecem em cerca de 20 arquivos
  do site (o Portal e a landing concentram a maior parte).

**Ordem de execução do bloco E.** 25 (planos, API e site) → 27 (público, no site inteiro) → 26 (empresarial e a
animação do e-mail). Depois, o bloco C, já com os planos novos.

## Bloco F: ideias da rodada de 25/11/2026 (noite)

### 28. Avaliações de usuários na boas-vindas — Lapidado (25/11/2026)

**Pedido.** Avaliações de outros usuários na página de boas-vindas (item 3), para deixar evidente o valor e que a
pessoa não precisa se arrepender da compra.

**Limite que não muda.** Só avaliações **reais e autorizadas**. Avaliação inventada, ou de pessoa que não existe, é
publicidade enganosa (CDC, art. 37) e fere o Código do CONAR; a nota e a foto também são dados pessoais (LGPD). Até
haver clientes, o espaço fica pronto no código e **não aparece** (decisão do item 3).

**Como colher as avaliações (o que torna a ideia possível).**
1. **Pedido no momento certo:** depois de 7 dias de uso, ou da 10ª consulta, o Portal mostra "Como está sendo a
   Órbita?" com nota de 1 a 5 e um texto opcional. Quem der 4 ou 5 vê o convite "Podemos mostrar sua avaliação no
   site?".
2. **Autorização explícita:** caixa marcada pela pessoa, com o que será mostrado (nome, cargo/área, cidade, foto opcional),
   onde e por quanto tempo; pode retirar a qualquer momento no Portal (Conta e segurança). Guardamos data e texto da
   autorização.
3. **Revisão antes de publicar:** a equipe aprova cada avaliação (sem editar o sentido; correção só de digitação, com
   aceite da pessoa).
4. **Foto:** a pessoa envia ou usa as iniciais; nunca foto de banco de imagens.

**Como aparece na boas-vindas.**
- Faixa "O que dizem advogados, contadores e empresários que usam a Órbita", com 3 avaliações (uma de cada público quando
  houver), nota em estrelas, nome, área e cidade, e a data.
- Média geral e quantidade ("4,8 de 5, em 120 avaliações") só quando houver pelo menos 20 avaliações.
- Ao lado: "Não gostou? Reembolso integral em até 7 dias" com o link, que é o que mais tira o medo de se arrepender.
- Com o tempo, a mesma faixa pode ir para a landing e para a página de planos.

**O que precisa ser construído.** Tabela `avaliacoes` (nota, texto, autorizada, aprovada, datas), rotas para enviar,
autorizar, retirar e listar as aprovadas; o pedido no Portal; a faixa (já prevista no item 3); tela simples de
aprovação para a equipe. Texto da autorização revisado por advogado.

### 29. Pagamentos no sandbox do Asaas — Lapidado (25/11/2026)

**Existe teste?** Sim. O Asaas tem um ambiente **Sandbox**, separado da produção: site `sandbox.asaas.com` e API
`https://api-sandbox.asaas.com/v3`, com chave própria (diferente da de produção). Nele dá para testar cliente,
assinatura, cartão de teste, Pix e boleto, estorno e webhooks, sem dinheiro de verdade.

**O que depende do Gabriel.**
1. Criar a conta Sandbox em `sandbox.asaas.com`. A documentação não deixa claro se o Sandbox exige CNPJ; a produção
   aceita pessoa física sem CNPJ. Conferir no cadastro.
2. Gerar a chave da API no Sandbox e colocar **só** no `api/.env` (nunca no chat):
   `ASAAS_BASE_URL=https://api-sandbox.asaas.com/v3`, `ASAAS_API_KEY=...`, `ASAAS_SIM_ENABLED=false` e um
   `ASAAS_WEBHOOK_TOKEN` próprio (32+ caracteres).

**O que muda no código.**
- O cliente do Asaas já fala com o Sandbox sem mudança (só a URL e a chave).
- **Webhook:** o Asaas precisa alcançar a API, e `localhost` não é alcançável da internet. Opções: um túnel
  (Cloudflare Tunnel ou ngrok) com a URL cadastrada no painel do Sandbox; ou, enquanto não houver túnel, a API
  confere o status da cobrança no Asaas quando o Portal abre (consulta de reserva). Proposta: as duas.
- **Trava de segurança (item 17):** hoje a API recusa subir sem a simulação e com o código do 2FA na resposta. No
  Sandbox de desenvolvimento, o código na resposta ainda é útil: a trava passa a olhar `COOKIE_SECURE` (produção) em
  vez de só a simulação.
- **Cartão:** no Sandbox, usar os cartões de teste do Asaas; é a hora de trocar os campos do cartão pela tokenização
  do Asaas (risco S3).
- O botão "Simular pagamento" some fora da simulação; no Sandbox, o Pix e o boleto são confirmados pelo painel do
  Asaas (ou pela rota de confirmação do Sandbox).

**Teste.** Assinatura nas três formas pelo Sandbox, webhook chegando pelo túnel, acesso liberado, cancelamento e
reembolso refletidos no painel do Asaas.

### 30. FAQ: bug no clique do "+" e animação suave — Executado e testado (26/11/2026)

**Feito.** `src/components/Faq.astro` refeito: estado próprio aplicado no clique (`data-estado` e `aria-expanded`),
"+" desenhado com duas barras que vira "−" num círculo cheio junto com o conteúdo; altura animada só em CSS (grade de
0fr a 1fr, 300 ms, mesma curva para abrir e fechar) com o texto entrando com fade e leve deslize; clique no meio da
animação ignorado; compensação da rolagem quando a pergunta que fecha está acima; resposta fechada sem foco de teclado
(`inert`); sem JavaScript, volta a ser `<details>` comum; movimento reduzido sem animação. A resposta "O que a base
cobre?" passou a apontar para `/bases`.
**Testes.** Estado inicial (primeira aberta), abrir outra fecha a anterior, clique rápido ignorado, fechar, altura 0 na
fechada, teclado; no celular, a pergunta clicada não sai do lugar (0 px) e sem rolagem lateral. **Não visto na tela:**
a fluidez da animação (o painel de teste estava oculto).

**O que acontece hoje** (`src/components/Faq.astro`):
- Ao fechar, o "+" só gira de volta **depois** que a animação de fechar termina (o `open` do `<details>` só sai no fim):
  o ícone fica atrasado 220 ms e "pula".
- Clicar de novo durante a animação não é bloqueado: a pergunta pode ficar aberta com o ícone de fechada (ou o
  contrário), e duas podem ficar abertas.
- No fim da animação de fechar, a resposta pode piscar inteira por um quadro antes de sumir.
- Abrir uma pergunta fecha outra acima dela: o conteúdo abaixo sobe de uma vez (salto).

**Como vai ficar.**
- Estado próprio em cada item (`data-estado="aberto|fechado"`), aplicado no clique: o "+" gira na hora, junto com o
  conteúdo.
- Altura animada por CSS (grade com `grid-template-rows: 0fr → 1fr`), com a mesma curva e duração para abrir e fechar
  (~280 ms) e o texto entrando com leve fade e deslize; nada de animação por JavaScript medindo altura.
- Cliques durante a animação são ignorados; uma aberta por vez continua.
- Quando a pergunta que fecha está acima, a página compensa a rolagem para a pergunta clicada não sair do lugar.
- Teclado (Enter/espaço), leitor de tela (`aria-expanded`) e movimento reduzido (abre sem animação).
- Testar nas 6 perguntas da landing e nas da Ajuda, no computador e no celular, clicando rápido várias vezes.

### 31. /bases: fade nos cards e o estado novo zera o filtro — Executado e testado (26/11/2026)

**Feito.** Ao filtrar, buscar ou trocar de página, os cards que saem fazem fade out e descem 6 px (180 ms) e só então
os novos entram com a animação de entrada; uma troca nova cancela a anterior; movimento reduzido troca direto.
Escolher outro estado no mapa zera estado, tipo, busca e página da lista (o painel do estado novo abre normalmente).
**Testes.** 8 cards com o fade durante a troca e nenhum depois; com tipo + busca + estado BA aplicados, clicar em MG
voltou a 108 bases, página 1, sem filtro de estado, sem busca e com "Todas".

**Pedido.** Animação de saída (fade out) nos cards de cada base; ao clicar num estado novo no mapa, zerar o filtro
que estava aplicado na lista lá embaixo.

**Como vai ficar.**
- **Troca de cards:** ao filtrar, buscar ou mudar de página, os cards que saem fazem fade out (e descem 6 px) em
  ~180 ms; depois os novos entram com fade in em cascata (como hoje). Movimento reduzido: troca direta.
- **Estado novo zera o filtro:** ao escolher outro estado no mapa, a lista volta ao início: limpa o filtro de estado
  anterior ("Estado: XX ✕"), o tipo e a busca, e volta à página 1. O painel do estado novo abre normalmente; a lista só
  filtra pelo estado novo se a pessoa clicar em "Ver as bases de XX na lista".
- Desmarcar o estado (segundo clique) também zera, como já faz hoje.

### 32. Rodapé padronizado e enxuto — Executado e testado (26/11/2026)

**Feito.** `Footer.astro`: marca (logo, uma frase com o público, redes) e três colunas: Produto (Como funciona, O que a
Órbita cobre, Planos e preços, Para empresas, Instalar o plugin), Suporte (Central de ajuda, Fale com a equipe,
Perguntas frequentes) e Legal (Termos, Privacidade, Reembolso, Cookies); uma linha de confiança (cartão, Pix, boleto ·
Pagamento processado pelo Asaas · Dados tratados conforme a LGPD); linha final com © e razão social, CNPJ (uma vez só),
Encarregado de dados, Créditos, tema e cookies. Saíram o resumo de privacidade em parágrafos, a coluna "Sua conta" e a
faixa Empresa/Atendimento/Pagamento (repetições). Logado: "Planos e preços" vira "Minha conta" e "Mudar de plano".
**Testes.** No computador, 544 px de altura (antes bem maior); colunas certas; versão logada; celular sem rolagem lateral.

**O que a pesquisa mostra** (guias de UX e galerias de rodapés de SaaS): o rodapé deve ser um sistema organizado, não
uma pilha de links; o essencial é links legais (privacidade, termos, cookies), aviso de copyright e dados da empresa,
contato/suporte e poucos grupos com títulos claros (Produto, Empresa, Suporte, Legal). Bons rodapés mostram coisas
diferentes para quem está logado; selos de confiança e contato ajudam; não esconder suporte atrás de cadastro.

**Problemas do rodapé atual.** 5 grupos de links + resumo de privacidade em 3 parágrafos + faixa de empresa,
atendimento e pagamento + barra com tema e cookies: tudo junto, com repetições (contato aparece 3 vezes, CNPJ 2 vezes,
links legais 2 vezes).

**Proposta (padrão da Órbita).**
1. **Linha principal, 4 colunas curtas:**
   - Marca: logo, uma frase ("Legislação e jurisprudência com a fonte, no Claude"), redes.
   - **Produto:** Como funciona, O que cobre, Planos, Para empresas, Instalar o plugin.
   - **Suporte:** Central de ajuda, Fale com a equipe, Status do serviço (futuro).
   - **Legal:** Termos de uso, Privacidade, Reembolso, Cookies.
2. **Faixa de confiança, uma linha:** formas de pagamento (cartão, Pix, boleto) · "Pagamento processado pelo Asaas" ·
   "Dados tratados conforme a LGPD".
3. **Linha final:** © ano, razão social e CNPJ (uma vez só) · Encarregado de dados (link) · Créditos · tema e
   preferências de cookies.
- Sai: o resumo de privacidade em parágrafos (fica na página de Privacidade), a coluna "Sua conta" (vai para o menu do
  avatar e para o Entrar) e as repetições.
- Logado: a coluna Produto troca "Planos" por "Minha conta" e "Planos" vira "Mudar de plano".
- O rodapé curto das páginas de foco (item 2) continua como está.

### 33. Compra só do que faz sentido, upgrade com melhorias e comparação de planos — Executado e testado (26/11/2026)

**Feito.**
- **API:** `PUT /billing/assinatura/plano` só sobe de plano (assinatura ativa e não cancelada), muda o valor da
  assinatura no Asaas e o plano no banco; igual, menor ou sem pagamento: 409. Teste novo (77 no total).
- **Servidor (middleware):** em `/assinar/{plano}` e `/upgrade/{plano}`, consulta `GET /billing/plano`: pagamento
  pendente → `/conta/plano?aviso=pendente`; mesmo plano → `?aviso=ja-assina`; plano menor → `?aviso=menor`; plano maior
  → `/upgrade/{plano}`; sem plano ativo, `/upgrade` vira compra nova. Vale para link direto e para botão.
- **Tela de upgrade** (`src/pages/upgrade/[plano].astro`): "Do Prata para o Ouro", só o que se ganha (com ✓), "continua
  tudo do Prata", valor de hoje, novo valor e diferença, cobrança proporcional "a definir", "Confirmar upgrade" e
  "Voltar sem mudar"; ao confirmar, volta ao Portal com "Upgrade feito".
- **Portal, Plano e pagamento:** mostra os avisos de quem tentou comprar o que já tem e do upgrade feito.
- **Cards da landing** (logado): "Seu plano" (com selo e borda), "Incluído no seu plano" ou "Fazer upgrade para o X";
  pagamento pendente: "Concluir o pagamento". Os cards (e o rodapé) esperam o aviso `orbita:sessao` do header, para
  funcionar já na primeira página depois de entrar.
- **Compare os planos** (`ComparePlanos.astro`, dados em `comparacao` no `src/data/plans.ts`): grupos Pesquisa,
  Recursos, Suporte e Conta e cobrança; ✓, — ou "a definir"; cabeçalho dos planos fixo ao rolar; Prata em destaque; no
  celular, abas e uma coluna por vez.
**Testes.** Conta Prata: mesmo plano, menor e maior levam para onde devem; cards com os rótulos certos; upgrade para o
Ouro gravado (API e Portal com o aviso); conta com Pix pendente vai para o Portal; tabela no computador e no celular
(abas, sem rolagem lateral). **Pendente:** a regra da cobrança proporcional no meio do mês e o downgrade (hoje, com a
equipe); os botões da tabela de comparação não mudam de rótulo para quem está logado (o servidor redireciona do mesmo
jeito).

**Pedido.** Quem já tem um plano não pode entrar na compra de outro (nem por link, nem por botão); o botão do plano
dele aparece como "Seu plano"; no upgrade, mostrar o que melhora; e uma comparação dos planos com ✓ e ✗, como fazem a
Anthropic e o ChatGPT.

**Regras de compra.**
- **No servidor (middleware), não só no botão:** com assinatura ativa ou pendente, `/assinar/{plano}`:
  - plano igual ao atual → vai para o Portal (Plano e pagamento) com o aviso "Você já assina o Prata";
  - plano abaixo → vai para o Portal com "Para mudar para um plano menor, fale com a equipe" (ou downgrade no fim do
    período, regra a definir);
  - plano acima → abre a **tela de upgrade** (não o checkout de compra nova).
- A API também recusa uma segunda assinatura (já faz: 409 `ja_assinante`).
- **Botões dos cards** (landing, /empresas, Portal), para quem está logado: plano atual → "Seu plano" (desativado, com
  selo); planos abaixo → "Incluído no seu plano"; planos acima → "Fazer upgrade". Pagamento pendente → "Concluir
  pagamento" no plano escolhido.

**Tela de upgrade** (`/assinar/{plano}` quando já existe assinatura menor):
- "Do Prata para o Ouro": o que você ganha (só os itens novos, com ✓ verde), o que continua (resumido), o novo valor
  e como fica a cobrança (proporcional ou na próxima fatura: regra "a definir", marcada na tela).
- Botão "Confirmar upgrade"; na API, troca o valor da assinatura no Asaas (rota nova `PUT /billing/assinatura/plano`).

**Comparação dos planos** (referência: a seção "Compare features across plans" do ChatGPT, com linhas agrupadas e
Sim/Não/Limitado por plano, e a página de planos da Anthropic):
- Abaixo dos cards, "Compare os planos": tabela com os três planos no topo (fixos ao rolar) e linhas agrupadas:
  **Pesquisa** (base inteira, fonte em cada resposta, limite de consultas), **Recursos** (alertas por tema, resumo
  semanal, acesso antecipado), **Suporte** (canal, prazo, implantação), **Conta** (usuários, nota fiscal).
- Em cada célula: ✓, ✗ ou o valor ("100/mês", "Ilimitado"); o que ainda não foi definido aparece "a definir", nunca
  um valor inventado.
- No celular: um plano por vez, com abas Bronze/Prata/Ouro sobre a tabela.
- Uma frase por plano respondendo "por que subir": Prata, "para quem pesquisa toda semana"; Ouro, "para quem quer ser
  avisado do que muda".
- A tabela lê os mesmos dados de `src/data/plans.ts` (uma fonte só para cards, tabela, upgrade e Termos).

**Depende de.** As especificações de cada plano (item 25) para preencher a tabela; até lá, a estrutura fica pronta
com "a definir".

**Ordem sugerida para o bloco F.** 30 (FAQ, pequeno) → 31 (/bases, pequeno) → 32 (rodapé, médio) → 33 (compra e
comparação, alto) → 29 (Sandbox, quando a conta existir) → 28 (avaliações, junto com a boas-vindas).

## Bloco C: plataforma do assinante

### 3. Página de boas-vindas depois da compra — Fechado na teoria (25/11/2026)

**Pedido.** Página receptiva depois da compra, com animações como as da landing, apresentando o produto, o que a
compra liberou e por que confiar.

**Decidido.**
- É **diferente do Início**: aparece uma vez só, depois da compra (itens 5 e 8).
- **Primeira ação: instalar o plugin**, em três passos guiados (baixar/instalar, conectar a conta, primeira pergunta).
- **Pro e Max diferentes:** o Max destaca o que tem a mais (alertas por tema, resumo semanal, acesso antecipado), com
  atalho para configurar; o Pro vê o mesmo sem esses itens e uma linha discreta sobre o Max.
- Os **três pontos de confiança** que saíram da landing (item 22) voltam aqui: fonte para conferir, rascunho não
  sentença, seus dados.

**Proposta de estrutura.**
1. Abertura: "Bem-vindo à Órbita, {nome}" com a animação de "acesso liberado" (lugar da explosão do átomo).
2. O que o plano dá, em cartões (Pro ou Max).
3. Três passos guiados, com progresso salvo, levando ao Plugin e conexões.
4. Uma resposta real animada, como no topo da landing, para mostrar o resultado.
5. Por que confiar: os três pontos, garantia de 7 dias, as bases consultadas (com o número da página /bases) e o
   contato humano.
6. Saída: "Ir para o meu painel" (Início).

**Decidido também.**
- A **explosão do átomo toca na abertura**, uma vez, ao chegar depois do pagamento. Até ela ser feita (última etapa),
  a abertura usa uma animação simples de "acesso liberado".
- **Depoimentos só quando houver reais**, com autorização: a estrutura fica pronta no código e nada aparece até lá.

### 5 e 8. Portal com cara de produto: páginas próprias, cabeçalho e navegação — Executado e testado (25/11/2026)

**Feito.** Layout `src/layouts/Portal.astro` (menu lateral com o plano e as 7 páginas; no celular, barra inferior com
Início, Plugin, Novidades, Plano e a folha "Mais"; cabeçalho de produto com o nome da página, busca na Ajuda, avatar
com menu e "Voltar ao site"; rodapé curto) e estado compartilhado em `src/scripts/portal.ts` (a assinatura é lida uma
vez por página). O antigo `conta.astro` virou 7 páginas em `src/pages/conta/`: Início (`index`), `plugin`, `plano`,
`alertas`, `novidades`, `suporte` e `configuracoes`. Cada página diz com que estados abre (com acesso, pendente,
encerrado, sem plano); nos outros, o layout mostra o estado vazio certo. Novidades, Suporte e Conta abrem sem plano.
Plano e pagamento abre com pagamento pendente e mostra o QR e o copia e cola do Pix (ou a linha do boleto) da
cobrança em aberto, e lista as faturas vindas da API. Endereços antigos (`/conta#plano`, `#cancelar` etc.) vão para
as páginas novas; Nav, Ajuda e Reembolso já apontam para elas. Artigos da Ajuda para a busca em `src/data/ajuda.ts`.
**Testes.** Contas locais Prata (pendente e depois paga), Ouro e sem plano; as 7 páginas no computador e no celular
(375 px, sem rolagem lateral); busca, menu do avatar e folha "Mais" com teclado (Esc devolve o foco); cancelar e
reativar; salvar o nome; sem sessão vai para `/entrar?next=`; build limpo.
**Não testado:** o modo de demonstração sem a API (o servidor de teste estava ligado à API).
**Fica para depois.** "Rever a apresentação" no Início (depende da boas-vindas, item 3); chamados abertos no Suporte
e a troca da forma de pagamento (a definir); aparelhos conectados e senha entram no item 9.

**Visual mais vivo (pedido de 25/11/2026, só no Portal).** Dentro das regras de `docs/auditoria-ia.md` (nada com ação
se mexe sob o cursor, sem ícone decorativo, sem laço sem motivo):
- Início: saudação pelo nome e pela hora do aparelho ("Boa noite, Gabriel") com a data; cartão do plano com a cor da
  marca, o átomo da Órbita girando num círculo e o selo de situação (Ativo, Suspenso, Cancelamento agendado,
  Encerrado), cujo ponto pulsa duas vezes ao abrir e para; "Continue de onde parou" com anel de progresso que enche até
  o número de passos feitos e os 4 passos com ✓ e o próximo tracejado; atalhos ganham cor no hover, sem se mexer.
- Layout: os blocos da página entram em cascata quando os dados chegam; o esqueleto de carregamento respira; o destaque
  da página atual desliza de um item para o outro no menu lateral e na barra do celular (View Transitions), com o menu,
  o cabeçalho e a barra parados.
- Cor da marca (`.cartao.is-marca`) no convite de upgrade, no pagamento pendente e no convite do Ouro.
- Com movimento reduzido, nada se mexe.
**Testes.** Conta Prata no computador e no celular (375 px, sem rolagem lateral); anel com 0 e com 2 de 4 passos;
build limpo. **Não visto na tela:** o deslizar do menu entre páginas (o painel de teste não mostra a transição) e o
movimento reduzido ligado.

## Bloco G: ideias da revisão do Portal (25/11/2026) — Em aberto

Revisão das 7 telas depois dos itens 5 e 8. Nada executado; cada ideia espera a decisão.

1. **Tema claro/escuro no Portal.** O seletor só existe no rodapé do site. Proposta: no menu do avatar.
2. **"Pergunte agora" no Início.** Três perguntas de exemplo, uma por público (advogado, contador, empresário), com
   botão para copiar e abrir o Claude: o Início passa a ajudar a usar o produto, não só a ver o plano.
3. **Plugin e conexões vazio.** Consultas em 0 e versão "a definir" até o servidor MCP. Proposta: uma frase só ("Seus
   números aparecem depois da primeira pergunta") no lugar dos zeros, ou manter como está.
4. **Prévia de alerta para quem não é Ouro.** Um alerta de exemplo, marcado como exemplo, ao lado do upgrade.
5. **Suporte dentro do Portal.** Formulário com o e-mail e o plano já preenchidos, em vez de levar a `/ajuda#contato`.
6. **Novidades por tribunal ou órgão.** Depende de as novidades terem esse dado (`src/data/novidades.ts`).
7. **Selo "Ouro" no menu** some para quem já é Ouro.
8. **Visual do Início nas outras páginas** (Plano, Plugin, Suporte), que ainda estão mais neutras.
9. **Fora do Portal (já no item 33):** o Checkout ainda deixa quem assina o Prata comprar o Prata de novo.


**Pedido.** Interface de quem está logado com cara de produto novo (mesmo design); cada aba vira uma página própria,
mais completa; cabeçalho mais intuitivo; navegação boa no celular.

**Decisões.**
- **Páginas** (cada uma com endereço próprio):

| Página | Endereço | O que tem |
|---|---|---|
| Início (painel) | `/conta` | Visão do dia a dia (ver abaixo). |
| Plugin e conexões | `/conta/plugin` | Baixar o plugin, conexão por IA (Claude, ChatGPT, Copilot, Gemini), tutoriais, uso do mês e limite do plano. |
| Plano, pagamento e faturas | `/conta/plano` | Plano atual, forma de pagamento, faturas e notas, upgrade/troca, cancelar e reembolso. |
| Alertas e resumo (Max) | `/conta/alertas` | Alertas por tema e resumo semanal; no Pro, a página mostra o que o Max dá, com o upgrade. |
| Novidades da base | `/conta/novidades` | O que entrou na base, por data e por tribunal/órgão; marca o que é novo desde a última visita. |
| Suporte | `/conta/suporte` | Falar com a equipe, chamados abertos, artigos da Ajuda mais usados. |
| Conta e segurança | `/conta/configuracoes` | Item 9: dados, senha, aparelhos conectados, preferências, LGPD. |

- **Navegação:** no computador, menu lateral fixo com o logo, o nome do plano e as 7 páginas; no celular, barra
  inferior estilo app com 4 ícones (Início, Plugin, Novidades, Plano) e "Mais" (Alertas, Suporte, Conta).
- **Cabeçalho de produto:** logo, nome da página atual, busca na Ajuda e o avatar com menu (o mesmo do site), mais
  "Voltar ao site". Não repete os links do site.

**Início é diferente da boas-vindas (proposta de Claude, confirmada pelo Gabriel em 25/11/2026).**
- **Boas-vindas** (`/boas-vindas`, item 3) é **uma vez só**, logo depois da compra: comemora, apresenta o que a pessoa
  ganhou, guia os três primeiros passos (instalar, conectar, primeira pergunta) e passa confiança. Tem animação de
  apresentação, como a landing, e é onde a explosão do átomo pode tocar. Depois de concluída, não volta mais
  (fica um link "Rever a apresentação" no Início).
- **Início** (`/conta`) é **o painel de todo dia**: rápido de ler, sem apresentação. Mostra:
  1. faixa de estado: plano, próxima cobrança e, se houver, um aviso (Pix pendente, pagamento atrasado, cancelamento
     agendado);
  2. status do plugin por IA (conectado ou não) e consultas do mês com o limite do plano;
  3. "Continue de onde parou": o que falta da instalação, só enquanto não estiver tudo feito;
  4. novidades da base desde a última visita (3 a 5 itens) e o link para Novidades;
  5. atalhos: baixar o plugin, abrir o Claude, falar com o suporte; no Max, criar alerta.
- **Regra de entrada:** depois da compra, a pessoa cai na boas-vindas; nas próximas vezes, no Início.

**Como vai ser feito.** Um layout novo `Portal.astro` (cabeçalho de produto, menu lateral, barra inferior no
celular, área de conteúdo) usado pelas 7 páginas; as páginas reaproveitam o que já existe no `conta.astro` (abas
de hoje) e ganham conteúdo novo. Os dados de plugin (conexões, uso, versão) continuam em demonstração até o servidor
MCP; ficam marcados "a definir" como hoje.

**Teste.** Cada página no computador e no celular; menu lateral e barra inferior com a página atual marcada; teclado
e leitor de tela; o Portal só abre com sessão; nada de rolagem lateral.

### 9. Conta e segurança completa — Fechado na teoria (25/11/2026) · Executado (26/11/2026)

**Feito.** Troca de senha com código (as outras sessões caem), troca de e-mail confirmada no endereço novo, aparelhos conectados com "Sair deste aparelho" e "Sair de todos", preferências de e-mail (resumo semanal só no Ouro; avisos de cobrança sempre ligados) e dados da nota fiscal editáveis depois da primeira compra (atualizam o cliente no Asaas). Rotas novas: `POST /auth/senha/trocar`, `POST /auth/email/trocar`, `POST /auth/confirmar`, `GET`/`PUT /auth/preferencias`, `GET`/`PUT /billing/nota` (82 testes).

Página `/conta/configuracoes` do Portal (itens 5 e 8).

**Decisões.** Básico + aparelhos conectados + preferências de e-mail + dados da nota fiscal. "Meus dados (LGPD)" fica
de fora desta rodada.

**Conteúdo.**
- **Perfil:** nome, e-mail (troca com código enviado ao e-mail novo), iniciais no avatar.
- **Senha:** trocar a senha (pede a atual e confirma com o código de 6 dígitos); ao trocar, **todas as outras sessões
  caem** (anotado no item 1 e no documento de segurança, S13).
- **Aparelhos conectados:** lista com navegador e sistema, criada em, último uso e "Este aparelho"; "Sair deste
  aparelho" em cada um e "Sair de todos" (a API já existe: `GET/DELETE /auth/sessoes`, `POST /auth/sair-de-todos`).
- **Preferências de e-mail:** novidades da base, avisos de cobrança (obrigatórios, só informativo) e resumo semanal
  (só no Max). Precisa de API nova (`GET/PUT /auth/preferencias`).
- **Dados da nota fiscal:** CPF ou CNPJ, nome ou razão social e endereço; editar atualiza o cliente no Asaas.
  Precisa de API nova (`GET/PUT /billing/nota`).
- **Excluir conta:** continua como hoje (pede cancelar a assinatura antes).

**Fica para depois.** "Baixar meus dados" (direito de acesso da LGPD): enquanto não houver o botão, o pedido é atendido
pelo suporte, e a Política de privacidade precisa dizer isso.

### 11. Checkout com cara de pagamento — Executado e testado (26/11/2026)

**Feito** (`src/pages/assinar/[plano].astro`): tema próprio aplicado à página de foco inteira (cabeçalho, conteúdo e
rodapé curto), sempre claro também com o site no modo escuro: fundo cinza muito claro, cartões brancos com sombra leve,
texto quase preto, tipografia do sistema, azul só nas ações (botão de pagar, passo atual) e verde só no "Pagamento
aprovado"; logo no verde da marca; sem animação. "← Voltar aos planos" e passos numerados (1 Dados da nota · 2 Pagamento
· 3 Confirmação), que acompanham a tela (formulário, espera do Pix/boleto, aprovado); dados da nota antes da forma de
pagamento; selos abaixo do botão (conexão criptografada, processado pelo Asaas, reembolso em 7 dias). A lógica de
pagamento não mudou.
**Testes.** Conta sem plano: Pix com QR, passos 1 → 2 → 3 e aprovação em verde; com o site forçado no modo escuro o
checkout continua branco; celular sem rolagem lateral. **Não testado:** cartão e boleto nesta rodada (a lógica é a mesma
de antes).

**Decisão.** Sempre branco, mesmo com o site no modo escuro (como Amazon e Mercado Livre).

**Como vai ser.** Página `/assinar/[plano]` com tema próprio: fundo branco e cinza bem claro, texto quase preto,
tipografia do sistema (a do celular/computador da pessoa), um azul de ação para o botão de pagar e verde só para
"pagamento aprovado"; sem animação de entrada e sem o átomo. Estrutura:
1. topo enxuto: logo pequeno, "Pagamento seguro" com cadeado e "Voltar";
2. passos numerados (1 Dados da nota · 2 Pagamento · 3 Confirmação);
3. coluna principal: dados da nota, forma de pagamento (cartão, Pix, boleto) em cartões selecionáveis;
4. resumo do pedido fixo ao lado (no celular, no topo, recolhível): plano, valor, próxima cobrança, "cancele quando
   quiser" e a garantia de 7 dias;
5. selos: "Pagamento processado pelo Asaas", conexão segura, formas aceitas;
6. rodapé curto (item 2).
Os campos do cartão passam a ser os do Asaas quando a tokenização entrar (risco S3 do documento de segurança).

---

## Bloco D: só documentar agora

### 7. Vídeo passo a passo da instalação — Só documentar

Vídeo curto (60 a 90 s) com cada passo do download e da conexão do plugin, na página Instalar e na de
boas-vindas. Pode ser feito com Remotion (skill da organização) depois que o plugin real existir, para mostrar
as telas verdadeiras do Claude.

### 12. Depoimentos com foto na boas-vindas — Ver item 28

Só com clientes reais e autorização por escrito (uso de nome, foto e texto). Depoimento inventado é
publicidade enganosa (CDC, art. 37, e Código do CONAR). Plano: deixar o espaço pronto e pedir depoimentos
aos primeiros clientes do período de teste.

### 17. Documentação completa do backend e da segurança — Executado (25/11/2026)

**Feito.** `docs/backend-e-seguranca.md`: arquitetura, arquivos, tabelas, todas as rotas, configuração de desenvolvimento e produção, o que já está seguro, 16 pontos de risco classificados (2 críticos: simulação do Asaas ligada por padrão e token do webhook de exemplo; 3 altos: cartão passando pela API, código do 2FA no log/resposta e limite de tentativas só na memória e só no login), LGPD, lista do dia da publicação e cobertura dos testes. Em seguida, corrigidos os dois críticos: simulação do Asaas desligada por padrão e trava que impede a API de subir com configuração perigosa (simulação em produção, token do webhook ou chave de exemplo, código do 2FA na resposta); webhook compara o token em tempo constante. 6 testes novos (72 no total). Os três riscos altos (S3 a S5) continuam abertos.

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

1. ~~Bloco A~~ feito: 1 e 10, 2, 4, 6, 14, 15, 19, 21 a 24.
2. ~~Documento do item 17~~ feito, com os dois riscos críticos corrigidos.
3. ~~Bloco B~~ feito: 13 e 20.
4. ~~Bloco E~~ feito: 25, 27 e 26.
5. Bloco C, teoria fechada em 25/11/2026 (ajustar Pro/Max para Bronze/Prata/Ouro). Ordem de execução: ~~5 e 8 (layout do Portal e as 7 páginas)~~ feito, 9 (conta e
   segurança), 11 (checkout branco), 3 (boas-vindas).
6. **Bloco F**: 30 → 31 → 32 → 33 → 29 (com a conta Sandbox do Asaas) → 28 (com a boas-vindas).
   **Bloco G** (ideias da revisão do Portal): conforme o que for decidido.
7. Riscos altos de segurança (S3 a S5) antes de publicar.
8. Bloco D (só documentar) e, por último, a animação de explosão, que toca na abertura da boas-vindas.
