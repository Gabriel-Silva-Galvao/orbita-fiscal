/**
 * Porta das rotas do assinante (Plano A, 24/11/2026).
 *
 * Sem API_URL: modo de demonstração, tudo passa (a "assinatura" vive no navegador).
 * Com API_URL: antes de abrir uma rota protegida, pergunta à API em FastAPI se a sessão do
 * cookie é válida, em GET {API_URL}/auth/sessao, repassando o cabeçalho Cookie.
 *   200 com JSON do usuário -> segue, com o usuário em Astro.locals.usuario
 *   401/403                 -> redireciona para /entrar?next=<rota>
 *   API fora do ar          -> 503, sem abrir a página
 * Toda regra de negócio fica na API; aqui só se decide se a porta abre.
 */
import { defineMiddleware } from 'astro:middleware';
import { API_URL } from 'astro:env/server';

const PROTEGIDAS = ['/conta', '/instalar', '/app'];

const protegida = (path: string) => PROTEGIDAS.some((p) => path === p || path.startsWith(`${p}/`));

export const onRequest = defineMiddleware(async (context, next) => {
  const { pathname, search } = context.url;
  // Páginas estáticas são geradas no build, sem requisição real: não há o que proteger.
  if (context.isPrerendered || !protegida(pathname) || !API_URL) return next();

  const entrar = () => context.redirect(`/entrar?next=${encodeURIComponent(pathname + search)}`);
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
});
