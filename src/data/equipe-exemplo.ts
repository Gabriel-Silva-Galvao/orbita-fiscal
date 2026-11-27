/**
 * Dados de EXEMPLO das telas da equipe (estrutura para discussão, 27/11/2026). Nenhum dado real.
 * Quando as telas forem construídas, tudo isto vem da API (rotas /equipe, com papel conferido no servidor).
 */

export const chamados = [
  { id: 1042, cliente: 'Carla Mendes', plano: 'Prata', assunto: 'O plugin não aparece no Claude', situacao: 'Aberto', espera: '3 h', ia: 'Claude' },
  { id: 1041, cliente: 'Escritório Lima', plano: 'Ouro', assunto: 'Nota fiscal com CNPJ errado', situacao: 'Aguardando cliente', espera: '1 dia', ia: '—' },
  { id: 1039, cliente: 'Paulo Reis', plano: 'Bronze', assunto: 'Resposta sem a fonte do julgado', situacao: 'Aberto', espera: '5 h', ia: 'ChatGPT' },
  { id: 1036, cliente: 'Júlia Prado', plano: 'Prata', assunto: 'Trocar de Pix para boleto', situacao: 'Resolvido', espera: '—', ia: '—' },
];

export const conversa = [
  { quem: 'cliente', nome: 'Carla Mendes', quando: '27/11 09:12', texto: 'Instalei pelo passo a passo, mas o Claude não mostra a Órbita nas ferramentas.' },
  { quem: 'interna', nome: 'Ana (Suporte)', quando: '27/11 09:40', texto: 'Status do plugin: inativo. Nenhuma conexão registrada. Provável instalação no app web em vez do desktop.' },
  { quem: 'equipe', nome: 'Ana (Suporte)', quando: '27/11 09:42', texto: 'Oi, Carla! Você instalou no Claude do navegador ou no aplicativo do computador?' },
];

export const cliente = {
  id: 'u_8f3a…c21',
  nome: 'Carla Mendes',
  email: 'carla@exemplo.com.br',
  desde: '12/11/2026',
  plano: 'Prata',
  situacao: 'Ativo',
  forma: 'Pix',
  docMascarado: '***.982.247-**',
  docInteiro: '529.982.247-25',
  plugin: { status: 'Inativo', baixou: 'Sim (2 vezes)', ultima: 'Nunca conectou', perguntas: 0, ias: [] as { ia: string; perguntas: number }[] },
  aparelhos: [
    { nome: 'Chrome no Windows', ultimo: 'hoje, 09:10' },
    { nome: 'Safari no iPhone', ultimo: '25/11' },
  ],
  faturas: [
    { data: '12/11/2026', valor: 'R$ 59,90', situacao: 'Paga', forma: 'Pix' },
  ],
};

export const reembolsos = [
  {
    id: 'R-118', cliente: 'Paulo Reis', plano: 'Bronze', valor: 'R$ 29,90', pago: '22/11/2026', pedido: '27/11/2026', prazo: 'até 29/11',
    motivo: 'As respostas não me ajudaram', melhorar: 'Queria mais decisões do TJMG.',
    uso: { baixou: 'Sim', primeira: '22/11', ultima: '26/11', dias: 4, perguntas: 37, ias: 'ChatGPT 30, Claude 7' },
  },
  {
    id: 'R-117', cliente: 'Marina Costa', plano: 'Prata', valor: 'R$ 59,90', pago: '25/11/2026', pedido: '26/11/2026', prazo: 'até 28/11',
    motivo: 'Não consegui instalar ou usar', melhorar: '',
    uso: { baixou: 'Não', primeira: '—', ultima: '—', dias: 0, perguntas: 0, ias: '—' },
  },
];

export const numeros = {
  assinantes: { bronze: 84, prata: 131, ouro: 42 },
  novosMes: 38,
  canceladosMes: 6,
  receitaMes: 'R$ 14.620,30',
  reembolsosMes: 3,
  pluginsAtivos: 189,
  online: { agora: 23, site: 9, plugin: 16 },
};

export const onlineHoras = [3, 2, 1, 1, 0, 1, 4, 11, 19, 24, 27, 22, 15, 21, 26, 25, 23, 18, 12, 9, 7, 6, 4, 23];

export const time = [
  { nome: 'Gabriel', email: 'admin@orbita…', papel: 'Admin', fator: 'Chave física', ultimo: 'hoje, 10:02' },
  { nome: 'Ana Souza', email: 'ana@orbita…', papel: 'Suporte', fator: 'App autenticador', ultimo: 'hoje, 09:42' },
  { nome: 'Rafael Dias', email: 'rafael@orbita…', papel: 'Financeiro', fator: 'App autenticador', ultimo: '26/11, 17:30' },
];

export const auditoria = [
  { quando: '27/11 09:41', quem: 'Ana Souza (Suporte)', acao: 'ver_ficha', sobre: 'u_8f3a…c21', motivo: 'Chamado 1042' },
  { quando: '27/11 09:39', quem: 'Ana Souza (Suporte)', acao: 'buscar_cliente', sobre: 'u_8f3a…c21', motivo: '—' },
  { quando: '26/11 17:28', quem: 'Rafael Dias (Financeiro)', acao: 'aprovar_reembolso', sobre: 'u_51b0…9de', motivo: 'Dentro dos 7 dias' },
  { quando: '26/11 16:02', quem: 'Gabriel (Admin)', acao: 'mostrar_documento', sobre: 'u_51b0…9de', motivo: 'Conferir nota fiscal' },
  { quando: '26/11 15:10', quem: 'Gabriel (Admin)', acao: 'mudar_papel', sobre: 'Rafael Dias', motivo: 'Entrou no financeiro' },
];

export const eventosSeguranca = [
  { quando: '27/11 08:55', tipo: 'Login da equipe', detalhe: 'Ana Souza, IP conhecido', nivel: 'ok' },
  { quando: '27/11 03:12', tipo: 'Tentativas de login', detalhe: '6 senhas erradas para admin@…, IP novo; bloqueado por 15 min', nivel: 'alerta' },
  { quando: '26/11 22:40', tipo: 'Busca em volume', detalhe: '0 alertas (limite: 30 buscas em 10 min)', nivel: 'ok' },
];
