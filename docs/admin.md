# Administração da Órbita: plano

Documento de planejamento da área de administração (item 52), aberto em 27/11/2026. Detalha a parte de admin de
[suporte-e-admin.md](suporte-e-admin.md); o suporte está em [suporte.md](suporte.md). A estrutura das telas para
discussão está em `/equipe` (só no `astro dev`). Nada disto está construído além dessa estrutura.

---

## 1. Decisões tomadas (27/11/2026)

| Tema | Decisão |
|---|---|
| Endereço | **Subdomínios próprios**, um para cada área, quando o domínio for comprado: `admin.<domínio>` para a administração e `suporte.<domínio>` para o suporte. Nenhuma das duas abre pelo site (`<domínio>/equipe` não existe em produção). |
| Segundo fator | **App autenticador** (código de 6 dígitos, TOTP), obrigatório para toda a equipe. O código por e-mail do cliente não serve para a equipe. |
| "Entrar como o cliente" | **Não haverá.** A ficha do cliente mostra o necessário; o acesso mais perigoso fica fora do sistema. |
| Guarda da auditoria | **5 anos.** Depois disso, as linhas são apagadas por rotina mensal. |

## 2. Endereços e isolamento

| Área | Endereço | Quem entra | Cookie |
|---|---|---|---|
| Site e Portal do cliente | `<domínio>` | Clientes | `orbita_sessao` (só do domínio principal, sem `Domain=`) |
| Suporte | `suporte.<domínio>` | Suporte, Financeiro e Admin | `__Host-orbita_suporte` |
| Administração | `admin.<domínio>` | Só Admin | `__Host-orbita_admin` |

- **Cookie `__Host-`:** só vale no próprio subdomínio, sempre `Secure`, sem `Domain` e com `Path=/`. A sessão do admin
  não vai para o suporte nem para o site, e vice-versa. `SameSite=Strict` nas duas áreas.
- **Login próprio em cada área.** Quem é Admin e quer usar o suporte entra lá também (mesma conta, sessão separada).
- **API:** as rotas da equipe ficam num serviço separado do da API do cliente (`api-equipe` ou rotas `/equipe` só
  aceitas pelo host dos subdomínios). O CORS de cada área aceita só a própria origem.
- **Fora do Google e dos buscadores:** `robots.txt` com `Disallow: /`, `X-Robots-Tag: noindex` e nenhum link a partir do
  site.
- **Cabeçalhos:** CSP restrita (só scripts da própria origem, sem terceiros, sem fontes externas), `frame-ancestors
  'none'`, HSTS com `includeSubDomains` no domínio todo.
- **Opcional, a decidir no deploy:** lista de IPs permitidos ou VPN na frente do `admin.` (com uma pessoa só, o IP de
  casa e do escritório bastam).
- No desenvolvimento, as telas continuam em `/equipe` no `astro dev` (404 fora dele, ficha F-12) até os subdomínios
  existirem.

## 3. Acesso da equipe

**Contas**
- Só um Admin cria contas, por convite com link de uso único que vale 24 horas. Não há cadastro aberto.
- A primeira conta de Admin é criada por um comando no servidor (não por tela), com a senha definida pela própria
  pessoa no primeiro acesso.
- Remover alguém derruba todas as sessões dela na hora.

**Entrar**
1. E-mail e senha (mínimo de 12 caracteres, conferida contra listas de senhas vazadas).
2. Código do app autenticador. No cadastro do app, o Admin recebe **10 códigos de recuperação** de uso único, guardados
   só como hash.
3. Sem "lembrar de mim" e sem "lembrar este aparelho".

**Sessão**
- 30 minutos sem uso; no máximo 8 horas; sai de todos os aparelhos ao trocar a senha ou ser removido.
- **Reautenticação** (senha + código do app de novo) antes de: reembolso, suspensão, exclusão de conta, mudar papel,
  convidar, mostrar CPF/CNPJ inteiro e exportar a auditoria. Vale por 5 minutos.

**Tentativas**
- 5 erros de senha ou de código por conta em 15 minutos: bloqueio de 15 minutos e e-mail ao Admin.
- Limite por IP guardado no banco (não na memória), para valer mesmo com a API reiniciada.

**Perdeu o celular do app**
- Entra com um código de recuperação e cadastra o app de novo. Sem códigos, outro Admin reseta o segundo fator; com uma
  pessoa só, o reset é pelo comando no servidor (seção 3, contas).

## 4. Telas da administração

| Tela | O que mostra | Ações (todas com motivo e auditoria) |
|---|---|---|
| **Painel** | Assinantes por plano, novos e cancelados no mês, receita do mês, reembolsos, plugins ativos, online agora e gráfico de 24 h | Nenhuma |
| **Clientes** | A mesma busca do suporte (e-mail completo ou id) e a ficha completa: assinatura, faturas, histórico de planos, foto de uso do plugin, CPF/CNPJ mascarado | Mostrar CPF/CNPJ inteiro, suspender, reativar, apagar conta |
| **Assinaturas** | Lista com filtros (plano, situação, forma de pagamento) | Suspender, reativar, trocar plano a pedido |
| **Reembolsos** | Pedidos em análise (suporte-e-admin.md, seção 8) | Aprovar, recusar com motivo da lista, oferta |
| **Equipe e papéis** | Quem tem acesso, papel, segundo fator, último acesso | Convidar, mudar papel, remover, resetar segundo fator |
| **Auditoria** | Toda ação e toda tela aberta pela equipe, com filtro por pessoa, cliente, ação e data | Exportar CSV (gera linha na própria auditoria) |
| **Segurança** | Tentativas de login da equipe, bloqueios, sessões abertas, avisos de configuração da API, versões das dependências e link para o registro de vulnerabilidades | Encerrar sessões da equipe |
| **Conteúdo** | Novidades da base e avisos que aparecem no Portal (hoje em `src/data/novidades.ts`) | Publicar e despublicar aviso |

O Admin também abre o `suporte.` (fila e chamados) com a mesma conta, entrando lá.

## 5. Auditoria

- Uma linha por tela aberta e por ação: quando, quem (id e papel), o quê (`ver_ficha`, `mostrar_documento`,
  `aprovar_reembolso`, `mudar_papel`…), sobre quem (id do cliente, nunca o e-mail), motivo (obrigatório nas ações
  sensíveis), de onde (IP e aparelho).
- **Só inserção:** a API não tem rota de edição nem de exclusão; o usuário do banco que a API usa não tem permissão de
  `UPDATE` nem de `DELETE` nessa tabela (quando for PostgreSQL). Cada linha guarda o hash da anterior, para mostrar se
  alguma sumiu.
- **5 anos de guarda**; a rotina mensal apaga só o que passou disso.
- Atende o pedido do cliente pela LGPD de saber quem acessou os dados dele.

## 6. Alertas para o Admin

Por e-mail, na hora:
- login da equipe de IP ou aparelho novo;
- bloqueio por tentativas erradas;
- mais de 30 buscas de cliente em 10 minutos pela mesma pessoa;
- ação sensível fora do horário comercial;
- exportação da auditoria;
- configuração perigosa detectada na API (`problemas_de_producao`).

## 7. Dados (tabelas na API)

| Tabela | Campos principais |
|---|---|
| `equipe` | id, nome, email, papel, senha_hash, totp_segredo (cifrado com chave do `.env`), criado_em, removido_em |
| `equipe_recuperacao` | equipe_id, codigo_hash, usado_em |
| `equipe_sessoes` | token_hash, equipe_id, area (suporte ou admin), criada_em, ultimo_uso, ip, aparelho, reauth_ate |
| `equipe_convites` | token_hash, email, papel, expira, usado_em, criado_por |
| `auditoria` | id, quando, equipe_id, papel, acao, alvo_tipo, alvo_id, motivo, ip, aparelho, hash_anterior |
| `avisos_portal` | id, titulo, texto, publicado_em, despublicado_em, criado_por |

## 8. Segurança (checklist da seção 0.1 de ciberseguranca.md)

- **Entrada:** motivo das ações sensíveis com até 300 caracteres; listas fechadas para papel, ação e filtros.
- **Autorização:** papel conferido em cada rota da API, nunca só na tela; cliente pelo id na URL sempre passa pela
  checagem de papel (teste de IDOR, F-02).
- **Testes de cada rota da equipe:** sem sessão (401), sessão de cliente (401), sessão do `suporte.` no `admin.` (401),
  papel errado (403), sem reautenticação (403), sem motivo (422), cliente inexistente (404), e a linha de auditoria criada.
- **Segredos:** segredo do TOTP cifrado no banco; chave no `api/.env`; comparação em tempo constante.
- **Navegador:** CSRF com `SameSite=Strict`, conferência do `Origin` e token por formulário; texto de cliente por
  `textContent`.
- **Revisão:** `/security-review` em toda mudança destas telas; OWASP ZAP e teste manual de invasão antes de ligar em
  produção.

## 9. Ordem de construção

1. Tabelas da equipe, comando de criação do primeiro Admin, login com app autenticador e códigos de recuperação.
2. Sessões por área, reautenticação e auditoria (sem isso nenhuma tela entra).
3. Equipe e papéis (convite, remover, resetar segundo fator) e Segurança.
4. Clientes e Assinaturas (com Asaas pela mesma regra da API do cliente).
5. Reembolsos com aprovação (muda o fluxo do cliente, seção 8 de suporte-e-admin.md).
6. Painel e usuários online.
7. Conteúdo (avisos do Portal).
8. Subdomínios no deploy, revisão de segurança dedicada e teste de invasão.

## 10. Ainda em aberto

- O domínio definitivo (os nomes `admin.` e `suporte.` dependem dele).
- Lista de IPs ou VPN na frente do `admin.`.
- Se a API da equipe roda num processo separado ou na mesma API com rotas presas ao host.
- Quais números do Painel o Suporte também vê (sem nomes).
