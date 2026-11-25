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
