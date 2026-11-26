# Suporte e administração da Órbita

Itens 51 e 52 da rodada de testes. Documento de desenho, aberto em 26/11/2026: nada disto está construído ainda. Fica por
último no projeto, junto com a fase de segurança (ver [ciberseguranca.md](ciberseguranca.md)), porque estas são as telas que
mais expõem dados de clientes. A regra geral: **cada pessoa da equipe vê só o necessário para a tarefa, e tudo o que ela vê
ou faz fica registrado.**

---

## 1. Quem usa e com que papel

| Papel | Quem é | Pode | Não pode |
|---|---|---|---|
| **Suporte** | Atendimento ao cliente | Buscar cliente, ver a ficha resumida, ver e responder chamados, reenviar e-mail de verificação, ver aparelhos conectados e encerrar sessões a pedido do cliente | Ver CPF/CNPJ inteiro, mudar plano, dar reembolso, apagar conta, ver os temas de alerta |
| **Financeiro** | Cobrança e notas | Tudo do suporte + ver assinatura, faturas e notas, pedir reembolso e trocar a forma de pagamento a pedido do cliente | Mudar papel de alguém, apagar conta |
| **Admin** | Responsável pela Órbita | Tudo + gerenciar a equipe e os papéis, suspender ou apagar conta, ver o registro de auditoria, ver as métricas | Ver a senha de alguém (ela não existe em claro), entrar na conta do cliente sem registro |

Nenhum papel enxerga senhas, códigos de verificação ou tokens: eles só existem como hash.

## 2. Acesso da equipe (o mais importante)

- **Login separado**, em endereço próprio (ex.: `equipe.` do domínio), com cookie próprio (`orbita_equipe`), que não serve
  no site nem no Portal do cliente, e vice-versa.
- **2FA obrigatório e mais forte** que o do cliente: app autenticador (TOTP) ou chave física (WebAuthn/passkey). Código
  por e-mail não basta para a equipe.
- **Sessão curta**: 30 minutos sem uso e no máximo 8 horas; sai de todos os aparelhos ao trocar a senha ou ser removido.
- **Ações sensíveis pedem a senha de novo** (reautenticação): reembolso, suspensão, exclusão, mudança de papel.
- **Lista de IPs permitidos** opcional para o papel Admin.
- **Contas da equipe** só são criadas por um Admin, por convite que vale 24 horas. Não há cadastro aberto.
- **Limite de tentativas** por IP e por conta, guardado no banco, com bloqueio temporário e aviso ao Admin.
- **Rotas próprias** (`/equipe/...`), cada uma conferindo o papel no servidor. A tela só esconde; quem decide é a API.

## 3. Registro de auditoria

Toda tela aberta e toda ação da equipe vira uma linha que ninguém edita nem apaga (nem o Admin):

| Campo | Exemplo |
|---|---|
| Quando | 26/11/2026 15:42:10 |
| Quem | id da pessoa da equipe e o papel |
| O quê | `ver_ficha`, `reenviar_codigo`, `reembolso`, `mudar_papel`… |
| Sobre quem | id do cliente (nunca o e-mail no log) |
| Motivo | obrigatório nas ações sensíveis (ex.: "pedido no chamado 123") |
| De onde | IP e aparelho |

O cliente pode pedir, pela LGPD, quem acessou os dados dele; o registro responde isso.

## 4. Telas do suporte (item 51)

1. **Entrar** — e-mail, senha e o 2FA da equipe. Sem "lembrar de mim".
2. **Início do suporte** — chamados abertos, os que esperam resposta há mais tempo e uma busca.
3. **Busca de cliente** — por e-mail completo ou id. Não lista todos os clientes e não aceita busca parcial (evita varrer
   a base). Cada busca entra no registro.
4. **Ficha do cliente (resumida)**:
   - nome, e-mail, data de cadastro, plano e situação (ativo, pendente, cancelado);
   - status do plugin (ativo ou inativo, item 40) e última vez que foi usado;
   - aparelhos conectados (só navegador, sistema e datas);
   - CPF/CNPJ mascarado (ex.: `***.982.247-**`);
   - histórico de chamados.
   - Não mostra: temas de alerta, perguntas feitas ao plugin, dados da nota completos.
5. **Chamado** — conversa com o cliente, anexos (só imagem e PDF, com limite de tamanho e verificação), mudança de
   situação (aberto, aguardando cliente, resolvido) e notas internas que o cliente não vê.
6. **Ações do suporte** — reenviar e-mail de verificação; encerrar sessões do cliente a pedido dele (com motivo).

O lado do cliente já tem onde isso aparece: "Seus chamados" na página Suporte do Portal (hoje "a definir").

## 5. Telas da administração (item 52)

1. **Painel** — números do negócio sem dados pessoais: assinantes por plano, novos e cancelados no mês, receita do mês,
   reembolsos, plugins ativos.
2. **Clientes** — a mesma busca do suporte, com a ficha completa: CPF/CNPJ inteiro (só ao clicar em "mostrar", com motivo
   e registro), dados da nota, assinatura, faturas, histórico de mudanças de plano.
3. **Assinaturas** — lista com filtros (plano, situação, forma de pagamento); ações: reembolso, suspender, reativar, sempre
   com reautenticação e motivo. As ações passam pelo Asaas pela mesma regra da API do cliente.
4. **Equipe** — quem tem acesso, com que papel, último acesso; convidar, mudar papel e remover.
5. **Auditoria** — o registro da seção 3, com filtro por pessoa, cliente, ação e data; exportação só para Admin.
6. **Segurança** — tentativas de login da equipe, bloqueios, sessões abertas da equipe, avisos da API
   (`problemas_de_producao`), versão das dependências.
7. **Conteúdo** — novidades da base e avisos que aparecem no Portal (hoje em `src/data/novidades.ts`).

## 6. Verificação de vulnerabilidades (mais forte que no resto do site)

- Revisão de segurança (`/security-review`) em toda mudança destas telas, antes do commit.
- Testes automáticos obrigatórios para cada rota de `/equipe`: sem sessão (401), sessão de cliente (401), papel errado
  (403), cliente inexistente (404), sem motivo na ação sensível (422), sem reautenticação (403), e que cada ação gerou a
  linha de auditoria.
- Teste de IDOR: trocar o id do cliente na URL nunca mostra dado que o papel não pode ver.
- Proteção contra CSRF reforçada: além do cookie `SameSite=Strict`, token por formulário e conferência do `Origin`.
- CSP própria, sem script de terceiros nas telas da equipe.
- Varredura com OWASP ZAP no ambiente de teste e teste manual de invasão antes de ligar em produção.
- Alertas para o Admin: muitas buscas em pouco tempo, ação fora do horário, login de IP novo.

## 7. Ordem sugerida de construção (quando chegar a vez)

1. Login da equipe com 2FA forte, papéis e registro de auditoria (sem isso, nenhuma tela entra).
2. Suporte: busca, ficha resumida e chamados (fecha o "Seus chamados" do Portal).
3. Admin: equipe, auditoria e segurança.
4. Admin: clientes, assinaturas e painel.
5. Revisão de segurança dedicada e teste de invasão.

## 8. Para decidir

- Endereço das telas da equipe (subdomínio próprio ou caminho no site).
- Se haverá "entrar como o cliente" para reproduzir problemas (se sim: só Admin, com aviso ao cliente e registro).
- Prazo de guarda do registro de auditoria.
- Ferramenta de chamados: própria (como descrito) ou um serviço pronto integrado.
