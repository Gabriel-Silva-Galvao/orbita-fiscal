/**
 * Estado de demonstração, só neste navegador, enquanto não há servidor de contas.
 * Instalar e Portal leem a assinatura que o Checkout de demonstração gravou.
 */
export interface DemoSub {
  plano: 'pro' | 'max';
  email: string;
  desde: string;
  metodo: 'cartao' | 'pix' | 'boleto';
  final?: string;
  reembolso?: string;
  cancelada?: string;
  nome?: string;
}

const KEY = 'of-demo-assinatura';

export function getSub(): DemoSub | null {
  try {
    const v = JSON.parse(localStorage.getItem(KEY) ?? 'null');
    return v && (v.plano === 'pro' || v.plano === 'max') ? v : null;
  } catch {
    return null;
  }
}

export function saveSub(s: DemoSub | null) {
  try {
    if (s) localStorage.setItem(KEY, JSON.stringify(s));
    else localStorage.removeItem(KEY);
  } catch {}
}

/** Dias inteiros desde a compra. */
export const daysSince = (iso: string) => Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);

export const fmtDate = (d: Date) => d.toLocaleDateString('pt-BR');

/** Mesma data no mês seguinte ao da compra, avançando até ficar no futuro. */
export function nextCharge(iso: string) {
  const d = new Date(iso);
  const now = new Date();
  do d.setMonth(d.getMonth() + 1);
  while (d <= now);
  return d;
}
