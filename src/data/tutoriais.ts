/**
 * Tutoriais de instalação por IA (aba Tutoriais do Portal e página Instalar).
 * Item 41: instalação pela loja de cada IA. Os nomes das lojas e dos menus ainda são "a confirmar" até a Órbita ser
 * publicada em cada uma; a página Instalar mostra isso na tela.
 * Base: pesquisa de 24/11/2026 em docs/planejamento.md (seção "Pesquisa: loja do Claude e outras IAs").
 * O servidor MCP da Órbita ainda não está no ar: o Claude tem o passo a passo da página Instalar;
 * as outras IAs mostram o caminho de cada uma e ficam "em preparação" até a Órbita ser publicada lá.
 */
/** Item 41 (26/11/2026): a instalação passa a ser pela loja de cada IA, com passo a passo e vídeo por IA. */
export type PassoLoja = { titulo: string; texto: string };
export type Loja = {
  /** Nome da loja ou diretório da IA. */
  nome: string;
  /** Caminho dentro da IA até a loja (cada item vira uma "etiqueta"). */
  caminho: string[];
  /** Página da Órbita na loja. Fica vazia até a publicação; a tela mostra "a confirmar". */
  url: string;
  /** Quem instala: a própria pessoa ou o administrador da empresa. */
  quemInstala: 'voce' | 'admin';
};
export type Tutorial = {
  id: 'claude' | 'chatgpt' | 'copilot' | 'gemini';
  nome: string;
  disponivel: boolean;
  quem: string;
  requisitos: string;
  passos: string[];
  observacao: string;
  loja: Loja;
  /** Passos da página Instalar para esta IA (o último é sempre a pergunta de teste, comum a todas). */
  instalacao: PassoLoja[];
  /** Endereço do vídeo tutorial (mp4 ou embed). Vazio = vídeo em produção. */
  video: string;
};

export const tutoriais: Tutorial[] = [
  {
    id: 'claude',
    nome: 'Claude',
    disponivel: true,
    quem: 'Você mesmo instala.',
    requisitos: 'Conta no Claude. Funciona na web, no app para computador, no celular e no Claude Code.',
    passos: [
      'No Claude, abra o diretório de conectores e plugins e procure por "Órbita".',
      'Adicione a Órbita, sem baixar arquivo.',
      'Quando o Claude pedir, entre com a sua conta Órbita e confirme o código enviado ao seu e-mail.',
      'Faça a pergunta de teste e confira as fontes na resposta.',
    ],
    observacao: 'A instalação é pelo diretório oficial do Claude. O link direto aparece na página Instalar quando a publicação for aprovada.',
    loja: {
      nome: 'Diretório do Claude',
      caminho: ['Claude', 'Configurações', 'Conectores', 'Explorar o diretório'],
      url: '',
      quemInstala: 'voce',
    },
    instalacao: [
      { titulo: 'Abra o diretório do Claude', texto: 'No Claude (web, app para computador ou celular), vá até o diretório de conectores e plugins e procure por "Órbita".' },
      { titulo: 'Adicione a Órbita', texto: 'Na página da Órbita no diretório, toque em adicionar ou conectar. Não é preciso baixar nenhum arquivo.' },
      { titulo: 'Entre com a sua conta Órbita', texto: 'O Claude abre o login da Órbita. Use o mesmo e-mail da assinatura e confirme o código que chega no seu e-mail.' },
    ],
    video: '',
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
    loja: {
      nome: 'Diretório de apps do ChatGPT',
      caminho: ['ChatGPT', 'Configurações', 'Apps', 'Explorar apps'],
      url: '',
      quemInstala: 'voce',
    },
    instalacao: [
      { titulo: 'Abra o diretório de apps do ChatGPT', texto: 'No ChatGPT pela web, abra o diretório de apps e procure por "Órbita". Nos planos Business, Enterprise e Edu, o administrador pode precisar liberar o app antes.' },
      { titulo: 'Conecte a Órbita', texto: 'Na página da Órbita, toque em conectar.' },
      { titulo: 'Entre com a sua conta Órbita', texto: 'O ChatGPT abre o login da Órbita. Use o e-mail da assinatura e confirme o código do e-mail.' },
    ],
    video: '',
  },
  {
    id: 'copilot',
    nome: 'Microsoft Copilot',
    disponivel: false,
    quem: 'Normalmente o TI da empresa ou do escritório configura uma vez para todos.',
    requisitos: 'Licença do Microsoft 365 Copilot, ou Copilot Chat com cobrança por uso no Copilot Studio.',
    passos: [
      'O TI cria um agente no Copilot Studio e adiciona a Órbita como ferramenta MCP.',
      'O TI publica o agente para a equipe no Microsoft 365.',
      'Na primeira pergunta, cada pessoa entra com a própria conta Órbita.',
    ],
    observacao: 'Quando a integração for publicada, este tutorial ganha um guia para o TI, com os dados de conexão.',
    loja: {
      nome: 'Loja de agentes do Microsoft 365',
      caminho: ['Microsoft 365 Copilot', 'Agentes', 'Obter agentes'],
      url: '',
      quemInstala: 'admin',
    },
    instalacao: [
      { titulo: 'O TI libera a Órbita para a empresa', texto: 'O administrador do Microsoft 365 adiciona a Órbita pela loja de agentes, uma vez, para quem vai usar.' },
      { titulo: 'Abra a Órbita no Copilot', texto: 'No Microsoft 365 Copilot, abra a lista de agentes e escolha a Órbita.' },
      { titulo: 'Entre com a sua conta Órbita', texto: 'Na primeira pergunta, o Copilot pede o login da Órbita. Cada pessoa usa a própria conta e confirma o código do e-mail.' },
    ],
    video: '',
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
    loja: {
      nome: 'Galeria de agentes do Gemini Enterprise',
      caminho: ['Gemini Enterprise', 'Agentes', 'Galeria'],
      url: '',
      quemInstala: 'admin',
    },
    instalacao: [
      { titulo: 'O administrador libera a Órbita', texto: 'No Gemini Enterprise, o administrador do Google Cloud adiciona a Órbita para a equipe.' },
      { titulo: 'Abra a Órbita no Gemini', texto: 'No Gemini Enterprise, escolha a Órbita na lista de agentes.' },
      { titulo: 'Entre com a sua conta Órbita', texto: 'Na primeira pergunta, o Gemini pede o login da Órbita. Use o e-mail da assinatura e confirme o código.' },
    ],
    video: '',
  },
];
