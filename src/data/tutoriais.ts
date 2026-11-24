/**
 * Tutoriais de instalação por IA (aba Tutoriais do Portal).
 * Base: pesquisa de 24/11/2026 em docs/planejamento.md (seção "Pesquisa: loja do Claude e outras IAs").
 * O servidor MCP da Órbita ainda não está no ar: o Claude tem o passo a passo da página Instalar;
 * as outras IAs mostram o caminho de cada uma e ficam "em preparação" até a Órbita ser publicada lá.
 */
export type Tutorial = {
  id: 'claude' | 'chatgpt' | 'copilot' | 'gemini';
  nome: string;
  disponivel: boolean;
  quem: string;
  requisitos: string;
  passos: string[];
  observacao: string;
};

export const tutoriais: Tutorial[] = [
  {
    id: 'claude',
    nome: 'Claude',
    disponivel: true,
    quem: 'Você mesmo instala.',
    requisitos: 'Conta no Claude. Funciona na web, no app para computador, no celular e no Claude Code.',
    passos: [
      'Baixe o plugin da Órbita na página Instalar.',
      'No Claude, abra o menu de plugins e envie o arquivo.',
      'Quando o Claude pedir, entre com a sua conta Órbita e confirme o código enviado ao seu e-mail.',
      'Faça a pergunta de teste e confira as fontes na resposta.',
    ],
    observacao: 'Quando a Órbita estiver no diretório oficial do Claude, a instalação passa a ser direto por lá, sem baixar arquivo.',
  },
  {
    id: 'chatgpt',
    nome: 'ChatGPT',
    disponivel: false,
    quem: 'Você mesmo adiciona, no ChatGPT pela web. Nos planos Business, Enterprise e Edu, quem adiciona para a equipe é o administrador.',
    requisitos: 'Leitura e escrita completas nos planos Business, Enterprise e Edu; no Pro, só leitura. Não funciona no app do celular.',
    passos: [
      'No ChatGPT pela web, abra Plugins e toque em "+".',
      'Escolha adicionar um servidor MCP e cole o endereço da Órbita.',
      'Entre com a sua conta Órbita e confirme o código do e-mail.',
      'Faça a pergunta de teste.',
    ],
    observacao: 'O endereço da Órbita para o ChatGPT aparece aqui quando a integração for publicada.',
  },
  {
    id: 'copilot',
    nome: 'Microsoft Copilot',
    disponivel: false,
    quem: 'Normalmente o TI do escritório configura uma vez para todos.',
    requisitos: 'Licença do Microsoft 365 Copilot, ou Copilot Chat com cobrança por uso no Copilot Studio.',
    passos: [
      'O TI cria um agente no Copilot Studio e adiciona a Órbita como ferramenta MCP.',
      'O TI publica o agente para a equipe no Microsoft 365.',
      'Na primeira pergunta, cada pessoa entra com a própria conta Órbita.',
    ],
    observacao: 'Quando a integração for publicada, este tutorial ganha um guia para o TI, com os dados de conexão.',
  },
  {
    id: 'gemini',
    nome: 'Gemini',
    disponivel: false,
    quem: 'No Gemini Enterprise, o administrador do Google Cloud configura para a empresa.',
    requisitos: 'Gemini Enterprise. No app Gemini de uso pessoal, depende de aprovação da Órbita no programa de apps conectados do Google.',
    passos: [
      'O administrador adiciona a Órbita como "Custom MCP Server" no Gemini Enterprise.',
      'O administrador ativa as ações da Órbita para a equipe.',
      'Cada pessoa entra com a própria conta Órbita.',
    ],
    observacao: 'Quando a integração for publicada, este tutorial ganha um guia para o administrador, com os dados de conexão.',
  },
];
