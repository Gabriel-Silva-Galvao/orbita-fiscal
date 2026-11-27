# Suporte da Órbita: plano

Documento de planejamento do suporte (item 51), aberto em 27/11/2026. Detalha a parte de suporte de
[suporte-e-admin.md](suporte-e-admin.md); a estrutura das telas para discussão está em `/equipe` (só no `astro dev`).
Nada disto está construído além dessa estrutura.

---

## 1. Decisões tomadas (27/11/2026)

| Tema | Decisão |
|---|---|
| Por onde o cliente abre chamado | **Formulário no Portal** (página Suporte, "Seus chamados") e **e-mail** para o endereço do suporte. Chat no site fica como ideia documentada (seção 9). |
| Onde ficam os chamados | **Sistema próprio**, na API da Órbita: ligado à ficha do cliente, ao status do plugin e à auditoria. Nenhum serviço de terceiros recebe dados do cliente. |
| O que o Suporte vê do plugin | **Resumo:** ativo ou inativo, se baixou, última conexão e em quais IAs. O número de perguntas e os dias de uso (a foto completa) ficam para depois (seção 9). |
| Endereço da área do suporte | **`suporte.<domínio>`**, subdomínio próprio, com login e cookie separados do site e do `admin.` ([admin.md](admin.md), seção 2). |
| Quem atende | **Uma pessoa, em dias úteis**, no horário comercial. O texto do Portal não promete prazo de resposta (item 45). |

## 2. O que o suporte resolve

- Instalação e conexão do plugin em cada IA (Claude, ChatGPT, Copilot, Gemini).
- Dúvidas de conta: verificação de e-mail, troca de senha e de e-mail, aparelhos conectados.
- Cobrança e nota fiscal: forma de pagamento, fatura, dados da nota, cancelamento.
- Qualidade das respostas: pergunta sem fonte, julgado que não apareceu, base que falta.
- Reembolso: o pedido é do cliente, no Portal; o suporte só explica (a análise é do Financeiro, seção 8 de
  suporte-e-admin.md).

## 3. Canais

**Formulário no Portal** (canal principal)
- Fica em Conta › Suporte, no lugar do "Seus chamados (a definir)".
- Campos: assunto (lista fechada: plugin, conta, cobrança e nota, respostas e bases, outro), título (até 120
  caracteres), mensagem (até 5.000), IA usada (opcional, lista fechada) e anexos (seção 7).
- Ao abrir, o chamado já leva, sem o cliente digitar: conta, plano e situação, status do plugin e o navegador.
- O cliente vê a lista dos seus chamados, a conversa e a situação, e pode responder e fechar.

**E-mail**
- Mensagem para o endereço do suporte vira chamado. Se o remetente tem conta, o chamado é ligado a ela; se não, entra
  como "sem conta" e o suporte responde pedindo o e-mail do cadastro.
- A resposta da equipe vai por e-mail com o número do chamado no assunto (`[Órbita #1042]`); a resposta do cliente a
  esse e-mail entra no mesmo chamado.
- O e-mail não prova quem mandou (remetente pode ser falsificado). Por isso, pelo e-mail o suporte **não** muda nada na
  conta: pedidos de troca de e-mail, encerrar sessões, dados da nota ou cobrança são feitos pelo próprio cliente no
  Portal, ou depois de confirmar a identidade (ficha F-13 no registro de segurança).
- Como receber: caixa do provedor de e-mail lida pela API (IMAP) ou encaminhamento do provedor para uma rota da API
  (webhook de e-mail recebido). **A decidir** junto com o provedor de SMTP de produção.

## 4. Ciclo de um chamado

| Situação | Quando | Quem muda |
|---|---|---|
| Aberto | Cliente abriu ou respondeu | Sistema |
| Em atendimento | O suporte pegou o chamado | Suporte |
| Aguardando cliente | O suporte respondeu e espera retorno | Suporte |
| Resolvido | O problema foi resolvido | Suporte ou cliente |
| Fechado | 7 dias depois de resolvido sem resposta, ou o cliente fechou | Sistema ou cliente |

- "Aguardando cliente" sem resposta em 7 dias vira "Resolvido" com uma mensagem automática.
- Resposta do cliente num chamado resolvido ou fechado há menos de 30 dias reabre o chamado; depois disso, abre um novo
  que cita o antigo.
- **Notas internas:** só a equipe vê; nunca vão para o cliente nem para o e-mail.
- **Respostas prontas:** textos curtos para os casos comuns (instalar no Claude do computador, onde ver a fatura…),
  editáveis antes de enviar.

## 5. Dados (tabelas na API)

| Tabela | Campos principais |
|---|---|
| `chamados` | id (número sequencial), usuario_id (ou nulo, se veio de e-mail sem conta), email_origem, assunto, titulo, situacao, ia, canal (portal ou email), plano_na_abertura, criado_em, atualizado_em, responsavel_id |
| `chamado_mensagens` | id, chamado_id, autor (cliente, equipe, sistema), autor_id, texto, interna (sim ou não), criado_em, message_id do e-mail (para ligar respostas) |
| `chamado_anexos` | id, mensagem_id, nome_original, tipo, tamanho, caminho do arquivo guardado, sha256 |
| `respostas_prontas` | id, titulo, texto, ativa |

O texto das mensagens é dado pessoal: entra na política de privacidade e tem prazo de guarda (seção 10).

## 6. Rotas da API

**Cliente** (sessão do cliente; dono sempre pela sessão)
- `GET /suporte/chamados` · `POST /suporte/chamados` · `GET /suporte/chamados/{id}` ·
  `POST /suporte/chamados/{id}/mensagens` · `POST /suporte/chamados/{id}/fechar`
- Chamado de outra conta responde 404 (não revela que existe).

**Equipe** (sessão da equipe, papel conferido em cada rota; tudo vai para a auditoria)
- `GET /equipe/chamados` (fila com filtros) · `GET /equipe/chamados/{id}` · `POST /equipe/chamados/{id}/mensagens`
  (resposta ou nota interna) · `PUT /equipe/chamados/{id}/situacao` · `GET /equipe/clientes/{id}/resumo`

**E-mail recebido**
- `POST /suporte/email-recebido` com segredo do provedor (mesmo padrão do webhook do Asaas e do `X-Orbita-Servidor`),
  ou a leitura por IMAP sem rota pública.

## 7. Anexos

- Só PNG, JPG e PDF, até 5 MB cada e 3 por mensagem.
- Tipo conferido pelo conteúdo (assinatura do arquivo), não pela extensão; nome trocado por um id; guardados fora da
  pasta pública.
- Download só para o dono do chamado e para a equipe, com `Content-Disposition: attachment` e `nosniff`.
- PDF não é aberto dentro da página da equipe (evita script embutido).
- Ficha F-04 no registro de segurança.

## 8. Avisos

- **Cliente:** e-mail a cada resposta da equipe (com link para o Portal, sem o texto de notas internas) e na mudança
  para "Resolvido".
- **Suporte (você):** e-mail a cada chamado novo e a cada resposta de cliente; resumo diário às 9h com a fila.
- Sem SMS e sem WhatsApp por enquanto.

## 9. Ideias para depois

**Chat no site** (pedido em 27/11/2026: documentar a ideia)
- Botão "Falar com a equipe" no Portal (e talvez no site), que abre uma conversa em tempo real.
- Só aparece "online" quando há alguém da equipe disponível; fora do horário vira o formulário de chamado.
- Cada conversa vira um chamado com canal `chat`, com a mesma ficha, notas internas e auditoria.
- Precisa de conexão em tempo real (WebSocket ou SSE) na API, limite de mensagens por minuto e o mesmo cuidado com
  texto do cliente na tela da equipe (`textContent`). Ficha F-14 no registro de segurança.
- Faz sentido quando houver mais de uma pessoa atendendo; com uma pessoa só, o formulário e o e-mail bastam.

**Foto completa de uso do plugin para o Suporte** (pedido em 27/11/2026: documentar para próximas ideias)
- Mostrar também o número de perguntas por IA e os dias de uso (`plugin.resumo_de_uso`, que já existe).
- Ajudaria a ver "instalou mas nunca perguntou" ou "usa só no ChatGPT".
- Antes de liberar: decidir o prazo de guarda e citar na política de privacidade (ficha F-09); hoje só o Financeiro
  vê isso, no pedido de reembolso.

**Outras**
- Base de respostas prontas sugerida pelo assunto do chamado.
- Pesquisa de satisfação de uma pergunta ao resolver.
- Artigo da Ajuda sugerido enquanto o cliente escreve o chamado.

## 10. Segurança e privacidade (checklist da seção 0.1 de ciberseguranca.md)

- **Entrada:** assunto, IA e situação em listas fechadas; título até 120 e mensagem até 5.000 caracteres; anexos
  conferidos (seção 7).
- **Autorização:** o cliente só vê os próprios chamados (dono pela sessão, 404 para os outros); a equipe passa pelo
  login com segundo fator (F-01) e pelo papel em cada rota.
- **Navegador:** mensagem do cliente aparece na tela da equipe por `textContent` (sem HTML); links no texto não viram
  clicáveis automaticamente.
- **E-mail:** não aceitar mudanças na conta por e-mail (F-13); limite de chamados novos por remetente por hora;
  remetente sem conta não recebe dados da conta de ninguém.
- **Repetição:** o mesmo e-mail recebido duas vezes não cria dois chamados (`message_id` único).
- **Dados:** mensagens e anexos guardados por 2 anos depois de fechados (a confirmar com o jurídico) e apagados com a
  conta; a auditoria guarda quem leu cada chamado.
- **Testes mínimos:** sem sessão (401), chamado de outra conta (404), campo gigante (422), anexo com extensão trocada
  (422), e-mail repetido (um chamado só), nota interna nunca aparece na rota do cliente.

## 11. Ordem de construção

1. Login da equipe com segundo fator e auditoria (pré-requisito de tudo, suporte-e-admin.md seção 7).
2. Tabelas e rotas do cliente; "Seus chamados" no Portal.
3. Fila e conversa na área da equipe, com notas internas e respostas prontas.
4. Avisos por e-mail (cliente e suporte).
5. E-mail recebido virando chamado.
6. Anexos.
7. Depois: chat, foto completa de uso, pesquisa de satisfação.

## 12. Ainda em aberto

- Como o e-mail recebido chega à API (IMAP ou encaminhamento do provedor).
- Prazo de guarda das mensagens e anexos (jurídico).
- Horário de atendimento que aparece no Portal ("dias úteis, das 9h às 18h"?).
- Se o cliente sem plano ativo também abre chamado pelo Portal (hoje a página Suporte abre em qualquer situação).
