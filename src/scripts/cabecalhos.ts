/**
 * Cabeçalhos de segurança das respostas do site (ARES-QA-004, risco S7).
 *
 * A CSP aqui não restringe scripts nem estilos (isso pede revisão das fontes, fotos e scripts da página antes):
 * só impede que o site seja aberto dentro de outro (clickjacking), troque a base dos links, carregue plugins ou envie
 * formulários para fora. HSTS só quando a página chegou por HTTPS.
 *
 * Atenção: o middleware só roda nas páginas renderizadas no servidor (conta, Entrar, Checkout...). As páginas estáticas
 * saem direto do servidor Node, sem passar por ele; em produção, o proxy (Nginx, Caddy, Cloudflare) deve mandar os
 * mesmos cabeçalhos em tudo.
 */
export const CSP_BASE = "frame-ancestors 'none'; base-uri 'self'; object-src 'none'; form-action 'self'";

export function cabecalhosDeSeguranca(https: boolean): Record<string, string> {
  const h: Record<string, string> = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Content-Security-Policy': CSP_BASE,
  };
  if (https) h['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains';
  return h;
}
