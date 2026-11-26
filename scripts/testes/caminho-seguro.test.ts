// Regressão ARES-SEC-004 (open redirect no ?next= do Entrar). Rodar: npm run test:site
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { caminhoSeguro } from '../../src/scripts/caminho-seguro.ts';

test('aceita caminhos deste site', () => {
  assert.equal(caminhoSeguro('/conta/plano'), '/conta/plano');
  assert.equal(caminhoSeguro('/assinar/ouro?forma=pix#topo'), '/assinar/ouro?forma=pix#topo');
});

test('recusa outro domínio, inclusive com TAB e quebra de linha (a falha da revisão)', () => {
  // searchParams.get já decodifica: "/%09/site" chega como "/\t/site".
  const ruins = [
    '/\t/evil.example',
    '/\n/evil.example',
    '/\r\n/evil.example',
    '//evil.example',
    '/\\evil.example',
    '/\\/evil.example',
    'https://evil.example',
    'javascript:alert(1)',
    '',
    null,
    undefined,
  ];
  for (const ruim of ruins) {
    assert.equal(caminhoSeguro(ruim), '/conta', JSON.stringify(ruim));
  }
});

test('mostra o que o código antigo deixava passar', () => {
  const antigo = (n: string) => n.startsWith('/') && !n.startsWith('//') && !n.startsWith('/\\');
  assert.equal(antigo('/\t/evil.example'), true); // passava na conferência antiga
  assert.equal(new URL('/\t/evil.example', 'https://orbita.invalid').host, 'evil.example'); // e o navegador ia para fora
});
