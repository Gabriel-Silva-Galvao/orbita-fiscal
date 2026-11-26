/**
 * Planos da Órbita (item 25 da rodada de testes, 25/11/2026): Bronze, Prata e Ouro.
 * As especificações que diferenciam os planos serão definidas no futuro: até lá, esses itens aparecem
 * como "a definir". O Ouro herda o que antes era exclusivo do Max (alertas por tema, resumo semanal,
 * acesso antecipado). Os preços também estão na API (api/app/billing.py, PLANOS): mude nos dois lugares.
 */
export type PlanSlug = 'bronze' | 'prata' | 'ouro';

export interface PlanItem {
  text: string;
  pending?: 'definir' | 'confirmar';
}

export interface Plan {
  slug: PlanSlug;
  name: string;
  cents: number;
  /** Uma linha: para quem é. */
  tagline: string;
  items: PlanItem[];
  featured?: boolean;
}

/** O que vale para os três planos. */
export const comum: PlanItem[] = [
  { text: 'A base inteira: legislação, jurisprudência e consultas' },
  { text: 'A fonte em cada resposta, para conferir' },
  { text: 'Funciona dentro do Claude' },
];

export const plans: Record<PlanSlug, Plan> = {
  bronze: {
    slug: 'bronze',
    name: 'Bronze',
    cents: 1990,
    tagline: 'Para começar a pesquisar com a fonte',
    items: [...comum, { text: 'Limite de consultas por mês', pending: 'definir' }],
  },
  prata: {
    slug: 'prata',
    name: 'Prata',
    cents: 5990,
    tagline: 'Para quem pesquisa toda semana',
    featured: true,
    items: [
      { text: 'Tudo do Bronze' },
      { text: 'Mais consultas por mês', pending: 'definir' },
      { text: 'Recursos do Prata', pending: 'definir' },
    ],
  },
  ouro: {
    slug: 'ouro',
    name: 'Ouro',
    cents: 11990,
    tagline: 'Para quem vive de pesquisa jurídica e fiscal',
    items: [
      { text: 'Tudo do Prata' },
      { text: 'Alertas por tema' },
      { text: 'Resumo semanal por área' },
      { text: 'Acesso antecipado às novidades' },
      { text: 'Limite de consultas', pending: 'definir' },
    ],
  },
};

/** Na ordem de exibição: do mais barato ao mais completo. */
export const planList: Plan[] = [plans.bronze, plans.prata, plans.ouro];

/** Plano de destaque e o plano de upgrade de cada um (header, Portal). */
export const upgradeDe: Partial<Record<PlanSlug, PlanSlug>> = { bronze: 'prata', prata: 'ouro' };

/** R$ 19,90, com espaço que não quebra entre o símbolo e o valor. */
export const brl = (cents: number) => {
  const v = cents / 100;
  const s = v.toLocaleString('pt-BR', { minimumFractionDigits: Number.isInteger(v) ? 0 : 2, maximumFractionDigits: 2 });
  return `R$ ${s}`;
};

/** Menor preço, para os botões "Assinar a partir de ...". */
export const aPartirDe = brl(Math.min(...planList.map((p) => p.cents)));

/**
 * Comparação dos planos (item 33): linhas agrupadas, com o valor de cada plano.
 * true = tem, false = não tem, 'definir' = ainda não definido (nunca inventar um valor), texto = o valor.
 * Quando as especificações chegarem, é aqui (e nos `items` acima) que se atualiza.
 */
export type Celula = boolean | 'definir' | string;
export interface LinhaComparacao {
  nome: string;
  valores: Record<PlanSlug, Celula>;
}
export const comparacao: { grupo: string; linhas: LinhaComparacao[] }[] = [
  {
    grupo: 'Pesquisa',
    linhas: [
      { nome: 'A base inteira (108 bases)', valores: { bronze: true, prata: true, ouro: true } },
      { nome: 'A fonte em cada resposta', valores: { bronze: true, prata: true, ouro: true } },
      { nome: 'Funciona dentro do Claude', valores: { bronze: true, prata: true, ouro: true } },
      { nome: 'Consultas por mês', valores: { bronze: 'definir', prata: 'definir', ouro: 'definir' } },
    ],
  },
  {
    grupo: 'Recursos',
    linhas: [
      { nome: 'Recursos do Prata', valores: { bronze: false, prata: 'definir', ouro: 'definir' } },
      { nome: 'Alertas por tema', valores: { bronze: false, prata: false, ouro: true } },
      { nome: 'Resumo semanal por área', valores: { bronze: false, prata: false, ouro: true } },
      { nome: 'Acesso antecipado às novidades', valores: { bronze: false, prata: false, ouro: true } },
    ],
  },
  {
    grupo: 'Suporte',
    linhas: [
      { nome: 'Atendimento pela equipe', valores: { bronze: true, prata: true, ouro: true } },
      { nome: 'Suporte prioritário', valores: { bronze: false, prata: false, ouro: true } },
      { nome: 'Conversa de implantação', valores: { bronze: false, prata: false, ouro: true } },
      { nome: 'Prazo de resposta', valores: { bronze: 'definir', prata: 'definir', ouro: 'definir' } },
    ],
  },
  {
    grupo: 'Conta e cobrança',
    linhas: [
      { nome: 'Usuários', valores: { bronze: '1', prata: '1', ouro: '1' } },
      { nome: 'Cartão, Pix ou boleto', valores: { bronze: true, prata: true, ouro: true } },
      { nome: 'Reembolso integral em até 7 dias', valores: { bronze: true, prata: true, ouro: true } },
    ],
  },
];
