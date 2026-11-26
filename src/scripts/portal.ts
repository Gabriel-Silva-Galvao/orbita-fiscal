/**
 * Estado compartilhado do Portal (itens 5 e 8 da rodada de testes): as 7 páginas de /conta usam o mesmo
 * carregamento da assinatura, feito uma vez por página. O layout (Portal.astro) e o script de cada página
 * importam este módulo; o Vite junta os dois, então `pronto` é uma promessa só.
 *
 * Com PUBLIC_BILLING_ENDPOINT: lê GET {billing}/assinatura (com cookie). Sem ele: demonstração, com a
 * assinatura que o Checkout gravou neste navegador (src/scripts/demo.ts).
 */
import { getSub, saveSub, nextCharge, type DemoSub } from './demo';

export type Estado =
  /** Assinatura com acesso (inclui suspensa, cancelada com acesso até o fim do período e reembolsada). */
  | 'ativo'
  /** Pix ou boleto ainda não pagos. */
  | 'pendente'
  /** Cancelada e sem acesso. */
  | 'encerrado'
  /** Nunca assinou. */
  | 'sem'
  /** A API não respondeu. */
  | 'erro';

export interface PortalCtx {
  estado: Estado;
  /** Status da API: ativo, pendente, suspenso, cancelado, reembolsado ('' na demonstração). */
  status: string;
  /** Plano mesmo sem acesso (ex.: pendente). */
  plano: DemoSub['plano'] | '';
  sub: DemoSub | null;
  /** Próxima cobrança (ou fim do acesso, se cancelada). */
  proxima: Date | null;
  ouro: boolean;
  /** Cobranças da assinatura (só com a API; na demonstração, lista vazia). */
  cobrancas: Cobranca[];
}

export interface Cobranca {
  id: string;
  /** PENDING, OVERDUE, CONFIRMED, RECEIVED, REFUNDED... (status do Asaas). */
  status: string;
  valor: number;
  vencimento: string;
  pago_em: string | null;
  forma: string;
  fatura_url: string | null;
  pix?: { copia_e_cola: string; imagem_base64: string; expira_em: string };
  boleto?: { linha_digitavel: string; codigo_barras: string; pdf_url: string | null };
}

const root = document.querySelector<HTMLElement>('[data-portal]');
const d = root?.dataset ?? {};
export const billing = d.billing ?? '';
export const authEndpoint = d.authEndpoint ?? '';
export const apiBase = billing.replace(/\/billing\/?$/, '');
export const plans = JSON.parse(d.plans ?? '{}') as Record<string, { name: string; price: string }>;
export const usuario = { email: d.userEmail ?? '', nome: d.userName ?? '' };

export const call = (base: string, path: string, method = 'GET', body?: unknown) =>
  fetch(`${base}${path}`, {
    method,
    credentials: 'include',
    headers: body ? { 'Content-Type': 'application/json' } : { accept: 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });

type Resumo = {
  plano: DemoSub['plano'];
  forma: DemoSub['metodo'];
  final_cartao: string | null;
  status_acesso: string;
  criada_em: string | null;
  primeira_paga_em: string | null;
  cancelada_em: string | null;
  reembolso_em: string | null;
  proxima_cobranca: string | null;
  acesso_ate: string | null;
  cobrancas: Cobranca[];
};

function montar(
  sub: DemoSub | null,
  status: string,
  plano: PortalCtx['plano'],
  estado: Estado,
  extra: { proxima?: string | null; cobrancas?: Cobranca[] } = {},
): PortalCtx {
  return {
    estado,
    status,
    plano,
    sub,
    proxima: extra.proxima ? new Date(`${extra.proxima}T12:00:00`) : sub ? nextCharge(sub.desde) : null,
    ouro: estado === 'ativo' && plano === 'ouro' && !sub?.reembolso,
    cobrancas: extra.cobrancas ?? [],
  };
}

async function carregar(): Promise<PortalCtx> {
  if (!billing) {
    const sub = getSub();
    return montar(sub, '', sub?.plano ?? '', sub ? 'ativo' : 'sem');
  }
  let r: Response;
  try {
    r = await call(billing, '/assinatura');
  } catch {
    return montar(null, '', '', 'erro');
  }
  if (r.status === 401) {
    location.replace(`/entrar?next=${encodeURIComponent(location.pathname)}`);
    return new Promise(() => {}); // a página está saindo
  }
  if (r.status === 404) return montar(null, '', '', 'sem');
  if (!r.ok) return montar(null, '', '', 'erro');
  const a = (await r.json()) as Resumo;
  const dia = (iso: string | null) => (iso ? `${iso}T12:00:00` : undefined);
  const sub: DemoSub = {
    plano: a.plano,
    email: usuario.email,
    nome: usuario.nome || undefined,
    desde: dia(a.primeira_paga_em ?? a.criada_em ?? new Date().toISOString().slice(0, 10))!,
    metodo: a.forma,
    final: a.final_cartao ?? undefined,
    cancelada: dia(a.cancelada_em),
    reembolso: dia(a.reembolso_em),
  };
  const s = a.status_acesso;
  const estado: Estado = s === 'pendente' ? 'pendente' : s === 'cancelado' ? 'encerrado' : 'ativo';
  return montar(estado === 'ativo' ? sub : null, s, a.plano, estado, {
    proxima: a.proxima_cobranca ?? a.acesso_ate,
    cobrancas: a.cobrancas ?? [],
  });
}

let atual = carregar();
/** Estado da assinatura desta visita. Depois de uma ação, `recarregar()` troca a promessa. */
export const pronto = () => atual;

type Ouvinte = (ctx: PortalCtx) => void;
const ouvintes: Ouvinte[] = [];
/** Chama `fn` agora (quando carregar) e de novo a cada recarga. */
export function aoCarregar(fn: Ouvinte) {
  ouvintes.push(fn);
  atual.then(fn);
}
export async function recarregar() {
  atual = carregar();
  const ctx = await atual;
  ouvintes.forEach((fn) => fn(ctx));
  return ctx;
}

/** Faixa de aviso do layout (erros de API e avisos de estado). */
export function avisar(texto: string, tipo: 'erro' | 'info' = 'erro') {
  const b = document.querySelector<HTMLElement>('[data-portal-aviso]');
  if (!b) return;
  b.className = tipo === 'erro' ? 'notice is-error' : 'notice';
  b.textContent = texto;
  b.hidden = false;
  b.scrollIntoView({ block: 'nearest' });
}

/**
 * Ações sobre a assinatura. Na demonstração, mudam o que está guardado no navegador;
 * com a API, cada uma vira a rota correspondente. Devolve true se deu certo.
 */
export async function agir(acao: 'cancelar' | 'reativar' | 'reembolso'): Promise<boolean> {
  if (!billing) {
    const sub = getSub();
    if (!sub) return false;
    const agora = new Date().toISOString();
    if (acao === 'cancelar') sub.cancelada = agora;
    if (acao === 'reativar') delete sub.cancelada;
    if (acao === 'reembolso') sub.reembolso = agora;
    saveSub(sub);
    await recarregar();
    return true;
  }
  const rotas = {
    cancelar: ['/assinatura', 'DELETE'],
    reativar: ['/assinatura/reativar', 'POST'],
    reembolso: ['/assinatura/reembolso', 'POST'],
  } as const;
  try {
    const [path, method] = rotas[acao];
    const r = await call(billing, path, method);
    if (!r.ok) {
      const e = await r.json().catch(() => ({}));
      avisar(e.detail?.mensagem ?? e.descricao ?? 'Não conseguimos concluir agora. Tente de novo em instantes.');
      return false;
    }
  } catch {
    avisar('Não conseguimos falar com o servidor. Confira sua conexão e tente de novo.');
    return false;
  }
  await recarregar();
  return true;
}

/**
 * Itens 43 e 48: troca da forma de pagamento da assinatura (Pix ou boleto, PUT /billing/assinatura/forma).
 * O cartão não passa por aqui: ele será trocado pela tokenização do Asaas no navegador (o número nunca chega
 * à API da Órbita; a API guarda só o token e os 4 últimos dígitos).
 */
export async function trocarForma(nova: 'pix' | 'boleto'): Promise<boolean> {
  if (!billing) {
    const sub = getSub();
    if (!sub) return false;
    sub.metodo = nova;
    saveSub(sub);
    await recarregar();
    return true;
  }
  try {
    const r = await call(billing, '/assinatura/forma', 'PUT', { forma: nova });
    if (!r.ok) {
      const e = await r.json().catch(() => ({}));
      avisar(e.detail?.mensagem ?? 'Não conseguimos trocar a forma de pagamento agora. Tente de novo em instantes.');
      return false;
    }
  } catch {
    avisar('Não conseguimos falar com o servidor. Confira sua conexão e tente de novo.');
    return false;
  }
  await recarregar();
  return true;
}

/** Passos da instalação marcados na página Instalar (1 a 4). */
export function passosInstalacao(): string[] {
  try {
    return JSON.parse(localStorage.getItem('of-demo-instalacao') ?? '[]');
  } catch {
    return [];
  }
}

/** Novidades: ids já vistos (a página Novidades marca todas como vistas ao abrir). */
export const VISTAS = 'of-demo-novidades-vistas';
export function novidadesVistas(): string[] {
  try {
    return JSON.parse(localStorage.getItem(VISTAS) ?? '[]');
  } catch {
    return [];
  }
}

export async function sair(destino = '/entrar') {
  if (authEndpoint) {
    try {
      await fetch(`${authEndpoint}/sair`, { method: 'POST', credentials: 'include' });
    } catch {}
  }
  try {
    sessionStorage.removeItem('of-demo-email');
    sessionStorage.removeItem('orbita:sessao');
  } catch {}
  location.href = destino;
}

export const fmt = (d: Date) => d.toLocaleDateString('pt-BR');
export const dataIso = (iso: string) => iso.slice(0, 10).split('-').reverse().join('/');
export const reais = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

export const forma = (s: DemoSub) =>
  s.metodo === 'pix' ? 'Pix' : s.metodo === 'boleto' ? 'Boleto' : `Cartão final ${s.final || '••••'}`;

export const $ = <T extends HTMLElement = HTMLElement>(s: string, el: ParentNode = document) => el.querySelector<T>(s)!;

export function botao(texto: string, cls: string, onClick: () => void) {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = cls;
  b.textContent = texto;
  b.addEventListener('click', onClick);
  return b;
}
