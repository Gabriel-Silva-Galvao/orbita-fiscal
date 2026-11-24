/** Planos da Órbita. Diferença por tarefa (decisão de 23/11/2026). */
export interface Plan {
  slug: 'pro' | 'max';
  name: string;
  cents: number;
  items: { text: string; pending?: 'definir' | 'confirmar' }[];
}

export const plans: Record<Plan['slug'], Plan> = {
  pro: {
    slug: 'pro',
    name: 'Pro',
    cents: 5000,
    items: [
      { text: 'Pesquisa de legislação e jurisprudência na base atualizada' },
      { text: 'Fonte para conferir em cada resultado', pending: 'confirmar' },
      { text: 'Funciona dentro do Claude' },
    ],
  },
  max: {
    slug: 'max',
    name: 'Max',
    cents: 7590,
    items: [
      { text: 'Tudo do Pro' },
      { text: 'Conferência de processos: o que ainda falta reunir' },
      { text: 'Preparação de peças com citações marcadas para conferência' },
      { text: 'Limite de uso', pending: 'definir' },
    ],
  },
};

/** R$ 50 ou R$ 75,90, com espaço que não quebra entre o símbolo e o valor. */
export const brl = (cents: number) => {
  const v = cents / 100;
  const s = v.toLocaleString('pt-BR', { minimumFractionDigits: Number.isInteger(v) ? 0 : 2, maximumFractionDigits: 2 });
  return `R$ ${s}`;
};
