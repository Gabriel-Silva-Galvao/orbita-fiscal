/**
 * Artigos da Ajuda (src/pages/ajuda.astro), para a busca no cabeçalho do Portal e para a página Suporte.
 * O id é a âncora do <details> na Ajuda. Se mudar uma pergunta lá, mude aqui também.
 */
export const artigos = [
  { id: 'instalar', titulo: 'Como instalo o plugin no Claude?', termos: 'instalar baixar arquivo plugin claude' },
  { id: 'conectar', titulo: 'Como conecto minha conta Órbita?', termos: 'conectar código conta login entrar' },
  { id: 'nao-aparece', titulo: 'O plugin não aparece no Claude', termos: 'erro não aparece sumiu problema' },
  { id: 'cobranca', titulo: 'Como funciona a cobrança?', termos: 'cobrança pagamento fatura nota pix boleto cartão' },
  { id: 'reembolso', titulo: 'Como peço reembolso?', termos: 'reembolso devolver dinheiro cancelar 7 dias' },
  { id: 'privacidade', titulo: 'O que acontece com meus dados e minhas consultas?', termos: 'dados privacidade lgpd consultas' },
];
