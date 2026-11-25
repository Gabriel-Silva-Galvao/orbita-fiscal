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

const PROTEGIDAS = ['/conta', '/instalar', '/app', '/assinar'];

const protegida = (path: string) => PROTEGIDAS.some((p) => path === p || path.startsWith(`${p}/`));

// SEO (etapa 8a): conta, compra e login ficam fora do Google. O robots.txt não bloqueia essas rotas
// (senão o Google nem leria o noindex); o aviso vai no cabeçalho de toda resposta delas, redirecionamentos inclusive.
const foraDoGoogle = (path: string) => protegida(path) || path === '/entrar';

export const onRequest = defineMiddleware(async (context, next) => {
  const res = await porta(context, next);
  if (foraDoGoogle(context.url.pathname)) {
    try {
      res.headers.set('X-Robots-Tag', 'noindex, nofollow');
    } catch {
      // Respostas com cabeçalhos imutáveis (raras): o meta robots do layout continua valendo.
    }
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
  const seguro = next.startsWith('/') && !next.startsWith('//') && !next.startsWith('/\\');
  return context.redirect(plano === 'pro' || plano === 'max' ? `/assinar/${plano}` : seguro ? next : '/conta');
}

async function porta(context: APIContext, next: MiddlewareNext): Promise<Response> {
  const { pathname, search } = context.url;
  if (pathname === '/entrar' && !context.isPrerendered) {
    const destino = await jaLogado(context);
    if (destino) return destino;
    return next();
  }
  // Páginas estáticas são geradas no build, sem requisição real: não há o que proteger.
  if (context.isPrerendered || !protegida(pathname) || !API_URL) return next();

  // Decisão de 24/11/2026: primeiro a conta, depois a compra. Quem chega ao Checkout sem
  // sessão vai criar a conta com o plano já escolhido; o Entrar leva de volta ao Checkout.
  const plano = pathname.match(/^\/assinar\/(pro|max)$/)?.[1];
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
  return next();
}
