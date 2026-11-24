# Tutorial de uso da Órbita

Guia para usar o site da Órbita de ponta a ponta, do primeiro acesso ao Portal do assinante, e o inventário de tudo o que pode ser usado hoje.
Atualizado em 24/11/2026, junto com a etapa 5e (aba Suporte).

> **Modo de demonstração.** Enquanto a API não está ligada ao site, tudo roda no navegador: nenhum e-mail é enviado (o código de verificação aparece na tela), nenhum pagamento é cobrado e os dados ficam só neste navegador. Itens marcados no site como "a confirmar" ou "a definir" ainda não têm valor final.

## 1. Como rodar

**Site** (Astro), na pasta do projeto:

```powershell
npm install
```

```powershell
npm run dev
```

Abre em http://localhost:4321.

**API** (Python FastAPI, com a simulação do Asaas), na pasta `api`:

```powershell
python -m venv .venv; .venv\Scripts\pip install -r requirements.txt
```

```powershell
.venv\Scripts\uvicorn app.main:app --reload
```

Abre em http://localhost:8000 (documentação automática em `/docs`). Para rodar os testes: `.venv\Scripts\python -m pytest -q`.

## 2. Passo a passo do assinante

### 2.1 Conhecer a Órbita (página inicial, `/`)
- Leia o que a Órbita faz, veja os exemplos de conversa (abas como "Prescrição intercorrente" e "ICMS no PIS/Cofins") e compare os planos **Pro (R$ 50/mês)** e **Max (R$ 75,90/mês)**.
- Tire dúvidas nas perguntas frequentes ou mande mensagem pelo formulário de contato.
- No rodapé: tema claro, escuro ou automático, preferências de cookies e créditos das fotos.

### 2.2 Criar a conta (`/entrar?modo=criar`)
A conta vem antes da compra. Ao clicar em "Assinar" sem conta, o site leva para cá.
1. Preencha nome, e-mail e senha (ou use "Continuar com Google").
2. Digite o **código de 6 dígitos** enviado ao e-mail. Na demonstração, ele aparece na tela. Vale 10 minutos, com 5 tentativas; dá para reenviar após 60 s.
3. Você segue direto para o checkout do plano escolhido.

Para entrar depois: `/entrar`, e-mail e senha, e de novo o código. "Esqueci a senha" envia um link de troca.

### 2.3 Assinar (`/assinar/pro` ou `/assinar/max`)
Escolha a forma de pagamento:
- **Cartão:** preencha os dados e clique em "Pagar". O acesso é liberado na hora.
- **Pix:** copie o código Pix. Na demonstração, use "Simular Pix confirmado".
- **Boleto:** copie a linha digitável; o vencimento é em 3 dias. Na demonstração, use "Simular boleto pago". Na vida real, o acesso começa quando o banco confirma, em até 3 dias úteis.

Ao confirmar o pagamento aparece "Seu plugin está pronto", com o botão "Ir para a instalação".

### 2.4 Instalar o plugin (`/instalar`)
1. **Baixar o plugin.**
2. Enviar o arquivo no Claude, no menu de plugins.
3. **Gerar código de conexão** e digitá-lo no Claude quando ele pedir para conectar a Órbita.
4. **Copiar pergunta** de teste e conferir as fontes na resposta.

### 2.5 Usar o Portal (`/conta`)
As abas rolam na horizontal no celular; também dá para navegar com as setas do teclado.

| Aba | O que faz | Pro | Max |
|---|---|---|---|
| Status do plugin | Acesso, consultas do mês, última consulta, versão do plugin, conexões com cada IA e a novidade mais recente | Sim | Sim |
| Novidades | Lista datada do que mudou na Órbita e nas IAs, com filtro (Todas, Órbita, Claude e outras IAs), selo "Nova" e contador de não lidas | Sim | Sim |
| Tutoriais | Como instalar no Claude (disponível), ChatGPT, Microsoft Copilot e Gemini (em preparação) | Sim | Sim |
| Alertas por tema | Salvar até 20 temas (mínimo 3 letras, sem repetidos), com sugestões prontas e botão de remover | Convite para o Max | Sim |
| Resumo semanal | Escolher as áreas do resumo que chega toda semana | Convite para o Max | Sim |
| Plano e pagamento | Plano, data de início, próxima cobrança, forma de pagamento e troca de plano | Sim | Sim |
| Cancelar ou reembolso | Reembolso integral em até 7 dias, sem justificar; cancelamento sem multa, com acesso até o fim do período e opção de reativar | Sim | Sim |
| Suporte | E-mail com botão Copiar, prazo de resposta, horário, Ajuda e formulário | Até 2 dias úteis e convite para o Max | Prioritário no mesmo dia útil e conversa de implantação |
| Conta | Salvar nome, ver o e-mail, sair e excluir a conta (digitando EXCLUIR) | Sim | Sim |

Ações com consequência (cancelar, reembolso, excluir conta) sempre pedem uma segunda confirmação.

### 2.6 Outras páginas
- `/ajuda`: perguntas e respostas sobre uso, pagamento e conta.
- `/termos`, `/privacidade`, `/reembolso`: regras da assinatura, dados pessoais e devolução (com tabela por forma de pagamento).
- Qualquer endereço inexistente mostra a página 404.

## 3. API (para a equipe)

| Rota | Para quê |
|---|---|
| `POST /billing/assinaturas` | Cria a assinatura (pro ou max; cartão, Pix ou boleto). Recusa com `ja_assinante` se já houver uma |
| `GET /billing/assinaturas/{id}` | Consulta a assinatura e o status do acesso |
| `PUT /billing/assinaturas/{id}/forma` | Troca para Pix ou boleto |
| `DELETE /billing/assinaturas/{id}` | Cancela |
| `POST /billing/assinaturas/{id}/reembolso` | Reembolso em até 7 dias do primeiro pagamento (`fora_do_prazo` ou `nada_pago` fora disso) |
| `POST /webhooks/asaas` | Recebe os eventos do Asaas, confere o token e ignora repetidos |
| `/asaas-sim/v3/...` | Simulação do Asaas, enquanto não há CNPJ |

Regras de acesso: pagamento confirmado ou recebido libera; atraso ou estorno suspende; reembolso e cancelamento encerram de vez. Detalhes em `api/README.md`.

## 4. Teste completo de 24/11/2026

| O que foi testado | Resultado |
|---|---|
| Testes automáticos da API (`pytest`) | 27 de 27 passaram |
| Build do site (`npm run build`) | Passou |
| As 11 páginas respondem (`/`, `/entrar`, `/entrar?modo=criar`, `/instalar`, `/ajuda`, `/termos`, `/privacidade`, `/reembolso`, `/assinar/pro`, `/assinar/max`, `/conta`) | Todas com 200; endereço inexistente dá 404 |
| Criar conta com código de 6 dígitos e seguir para o checkout | Funcionou |
| Pagar por boleto e simular a confirmação | "Seu plugin está pronto"; assinatura salva com forma Boleto |
| As 9 abas do Portal no Pro | Todas abrem; Alertas e Resumo mostram o convite para o Max; Suporte mostra 2 dias úteis |
| As mesmas abas no Max | Alertas e Resumo liberados; Suporte prioritário com conversa de implantação |
| Validação dos temas | "IC" recusado (curto), "icms-st" recusado (repetido); "ICMS-ST" e "Crédito presumido de ICMS" salvos |
| Resumo semanal | Área marcada ficou salva |
| Cancelar, reativar e pedir reembolso | Os três funcionaram; após o reembolso, acesso "Encerrado" e próxima cobrança "Nenhuma" |
| Gerar código de conexão na instalação | Código gerado e exibido |

### Pontos de atenção
- Tudo ainda é demonstração: o site não chama a API. Ligar os dois é uma etapa futura.
- Valores como limite de consultas, versão do plugin, prazos de suporte e frequência dos resumos seguem "a confirmar" ou "a definir".
- ChatGPT, Copilot e Gemini estão "em preparação" até a Órbita ser publicada nessas IAs.
