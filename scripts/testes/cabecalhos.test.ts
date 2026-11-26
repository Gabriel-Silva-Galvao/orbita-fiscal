// Regressão ARES-QA-004 (cabeçalhos de segurança do site). Rodar: npm run test:site
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cabecalhosDeSeguranca } from '../../src/scripts/cabecalhos.ts';

test('anti-clickjacking, nosniff e Referrer-Policy sempre', () => {
  const h = cabecalhosDeSeguranca(false);
  assert.equal(h['X-Content-Type-Options'], 'nosniff');
  assert.equal(h['X-Frame-Options'], 'DENY');
  assert.match(h['Content-Security-Policy'], /frame-ancestors 'none'/);
  assert.equal(h['Referrer-Policy'], 'strict-origin-when-cross-origin');
});

test('HSTS só com HTTPS', () => {
  assert.equal(cabecalhosDeSeguranca(false)['Strict-Transport-Security'], undefined);
  assert.match(cabecalhosDeSeguranca(true)['Strict-Transport-Security'], /max-age=31536000/);
});

test('a CSP não bloqueia scripts nem estilos do próprio site', () => {
  const csp = cabecalhosDeSeguranca(true)['Content-Security-Policy'];
  assert.doesNotMatch(csp, /script-src|style-src|default-src/);
});
