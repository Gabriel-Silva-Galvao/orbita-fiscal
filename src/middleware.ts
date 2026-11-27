/**
 * Porta das rotas do assinante (Plano A, 24/11/2026).
 *
 * Sem API_URL: modo de demonstração, tudo passa (a "assinatura" vive no navegador).
 * Com API_URL: antes de abrir uma rota protegida, pergunta à API em FastAPI se a sessão do
 * cookie é válida, em GET {API_URL}/auth/sessao, repassando o cabeçalho Cookie.
 *   200 com JSON do usuário -> segue, com o usuário em Astro.locals.usuario
 *   401/403                 -> redireciona para /entrar?next=<rota>
 *                              (no Checkout, /entrar?plano=<plano>&modo=criar: conta antes da compra)
 *   API fora do ar          -> 503, sem abrir a página
 * Toda regra de negócio fica na API; aqui só se decide se a porta abre.
 */
import type { APIContext, MiddlewareNext } from 'astro';
import { defineMiddleware } from 'astro:middleware';
import { API_URL } from 'astro:env/server';
import { caminhoSeguro } from './scripts/caminho-seguro';
import { cabecalhosDeSeguranca } from './scripts/cabecalhos';

const PROTEGIDAS = ['/conta', '/instalar', '/app', '/assinar', '/upgrade', '/boas-vindas'];

const protegida = (path: string) => PROTEGIDAS.some((p) => path === p || path.startsWith(`${p}/`));

// SEO (etapa 8a): conta, compra e login ficam fora do Google. O robots.txt não bloqueia essas rotas
// (senão o Google nem leria o noindex); o aviso vai no cabeçalho de toda resposta delas, redirecionamentos inclusive.
const foraDoGoogle = (path: string) => protegida(path) || path === '/entrar' || daEquipe(path);

// Telas da equipe (itens 51 e 52): por ora são só uma estrutura para discussão, com dados de exemplo. Fora do
// `astro dev` não existem (404), para nada da área interna aparecer no site publicado (F-12 no registro de segurança).
const daEquipe = (path: string) => path === '/equipe' || path.startsWith('/equipe/');

export const onRequest = defineMiddleware(async (context, next) => {
  const res = await porta(context, next);
  try {
    if (foraDoGoogle(context.url.pathname)) res.headers.set('X-Robots-Tag', 'noindex, nofollow');
    // ARES-QA-004: anti-clickjacking, nosniff, Referrer-Policy e HSTS (com HTTPS) nas respostas do servidor.
    if (!context.isPrerendered) {
      for (const [nome, valor] of Object.entries(cabecalhosDeSeguranca(context.url.protocol === 'https:'))) res.headers.set(nome, valor);
    }
  } catch {
    // Respostas com cabeçalhos imutáveis (raras): o meta robots do layout continua valendo.
  }
  return res;
});

/** Item 1: quem já tem sessão e abre /entrar vai direto para onde ia (next, Checkout do plano ou a conta). */
async function jaLogado(context: APIContext): Promise<Response | null> {
  const cookie = context.request.headers.get('cookie');
  if (!API_URL || !cookie?.includes('orbita_sessao=')) return null;
  try {
    const res = await fetch(new URL('/auth/sessao', API_URL), {
      headers: { cookie, accept: 'application/json' },
      signal: AbortSignal.timeout(3000),
    });
    if (!res.ok) return null;
  } catch {
    return null; // API fora do ar: mostra a tela de entrar normalmente
  }
  const q = context.url.searchParams;
  const next = q.get('next') ?? '';
  const plano = q.get('plano');
  return context.redirect(plano && ['bronze', 'prata', 'ouro'].includes(plano) ? `/assinar/${plano}` : caminhoSeguro(next));
}

async function porta(context: APIContext, next: MiddlewareNext): Promise<Response> {
  const { pathname, search } = context.url;
  if (daEquipe(pathname) && !import.meta.env.DEV) return new Response('Not found', { status: 404 });
  if (pathname === '/entrar' && !context.isPrerendered) {
    const destino = await jaLogado(context);
    if (destino) return destino;
    return next();
  }
  // Páginas estáticas são geradas no build, sem requisição real: não há o que proteger.
  if (context.isPrerendered || !protegida(pathname) || !API_URL) return next();

  // Decisão de 24/11/2026: primeiro a conta, depois a compra. Quem chega ao Checkout sem
  // sessão vai criar a conta com o plano já escolhido; o Entrar leva de volta ao Checkout.
  const plano = pathname.match(/^\/assinar\/(bronze|prata|ouro)$/)?.[1];
  const entrar = () =>
    context.redirect(plano ? `/entrar?plano=${plano}&modo=criar` : `/entrar?next=${encodeURIComponent(pathname + search)}`);
  const cookie = context.request.headers.get('cookie');
  if (!cookie) return entrar();

  let res: Response;
  try {
    res = await fetch(new URL('/auth/sessao', API_URL), {
      headers: { cookie, accept: 'application/json' },
      signal: AbortSignal.timeout(5000),
    });
  } catch {
    return new Response('Serviço temporariamente indisponível. Tente de novo em instantes.', { status: 503 });
  }

  if (res.status === 401 || res.status === 403) return entrar();
  if (!res.ok) return new Response('Serviço temporariamente indisponível. Tente de novo em instantes.', { status: 503 });

  context.locals.usuario = (await res.json()) as App.Locals['usuario'];

  // Item 33: quem já tem plano não compra de novo. A regra vale no servidor, para link direto e para botão.
  const pedido = pathname.match(/^\/(assinar|upgrade)\/(bronze|prata|ouro)$/);
  if (pedido) {
    const [, rota, alvo] = pedido;
    let atual: App.Locals['planoAtual'];
    try {
      const r = await fetch(new URL('/billing/plano', API_URL), {
        headers: { cookie, accept: 'application/json' },
        signal: AbortSignal.timeout(5000),
      });
      atual = r.ok ? ((await r.json()) as App.Locals['planoAtual']) : undefined;
    } catch {
      return new Response('Serviço temporariamente indisponível. Tente de novo em instantes.', { status: 503 });
    }
    context.locals.planoAtual = atual;
    const ORDEM = ['bronze', 'prata', 'ouro'];
    const temPlano = atual?.plano && atual.tem_acesso;
    if (atual?.status_acesso === 'pendente') return context.redirect('/conta/plano?aviso=pendente');
    if (temPlano) {
      const de = ORDEM.indexOf(atual!.plano!);
      const para = ORDEM.indexOf(alvo);
      if (para === de) return context.redirect('/conta/plano?aviso=ja-assina');
      if (para < de) return context.redirect('/conta/plano?aviso=menor');
      if (rota === 'assinar') return context.redirect(`/upgrade/${alvo}`); // plano maior: tela de upgrade
    } else if (rota === 'upgrade') {
      return context.redirect(`/assinar/${alvo}`); // sem plano ativo: é uma compra nova
    }
  }
  return next();
}
