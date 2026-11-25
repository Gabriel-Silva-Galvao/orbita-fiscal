/**
 * Dados da empresa e canais. Tudo aqui está pendente de confirmação (briefing, Pendências):
 * e-mail, Instagram, razão social, CNPJ e encarregado de dados. Troque os valores quando decidir.
 */
export const contact = {
  email: 'contato@orbitafiscal.com.br',
  privacyEmail: 'privacidade@orbitafiscal.com.br',
  instagram: 'https://www.instagram.com/orbitafiscal',
  instagramHandle: '@orbitafiscal',
};

export const company = {
  name: 'Órbita',
  legalName: '', // razão social: a definir
  cnpj: '', // a definir
  address: '', // endereço da sede: a definir
  city: 'Brasil',
  supportHours: '', // horário de atendimento: a definir
};

/** Formas de pagamento aceitas no Checkout (Asaas). */
export const paymentMethods = ['Cartão de crédito', 'Pix', 'Boleto'];

export const legalLinks = [
  { href: '/privacidade', label: 'Política de privacidade' },
  { href: '/termos', label: 'Termos de uso' },
  { href: '/reembolso', label: 'Política de reembolso' },
  { href: '/privacidade#cookies', label: 'Cookies' },
  { href: '/privacidade#direitos', label: 'Seus direitos na LGPD' },
  { href: '/privacidade#encarregado', label: 'Encarregado de dados' },
];
