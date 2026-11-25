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

### 26. Área de planos empresariais com contato animado — Fechado na teoria (25/11/2026)

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

### 5 e 8. Portal com cara de produto: páginas próprias, cabeçalho e navegação — Fechado na teoria (25/11/2026)

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

### 9. Conta e segurança completa — Fechado na teoria (25/11/2026)

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

### 11. Checkout com cara de pagamento — Fechado na teoria (25/11/2026)

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

### 12. Depoimentos com foto na boas-vindas — Só documentar

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
4. **Bloco E** (mudança dos planos e do público): 25 → 27 → 26.
5. Bloco C, teoria fechada em 25/11/2026 (ajustar Pro/Max para Bronze/Prata/Ouro). Ordem de execução: 5 e 8 (layout do Portal e as 7 páginas), 9 (conta e
   segurança), 11 (checkout branco), 3 (boas-vindas).
6. Riscos altos de segurança (S3 a S5) antes de publicar.
7. Bloco D (só documentar) e, por último, a animação de explosão, que toca na abertura da boas-vindas.
