// CPF e CNPJ (inclusive o CNPJ alfanumérico da Receita, 2026) no site. Rodar: npm run test:site
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { docChars, isCNPJ, isCPF, maskDoc } from '../../src/scripts/validate.ts';

test('CNPJ alfanumérico: exemplo oficial da Receita confere; dígito errado não', () => {
  assert.equal(isCNPJ('12.ABC.345/01DE-35'), true);
  assert.equal(isCNPJ('12.abc.345/01de-35'), true);
  assert.equal(isCNPJ('12.ABC.345/01DE-36'), false);
  assert.equal(isCNPJ('AB.CDE.FGH/IJKL-MN'), false); // dígitos verificadores precisam ser números
});

test('CNPJ e CPF numéricos continuam como antes', () => {
  assert.equal(isCNPJ('11.222.333/0001-81'), true);
  assert.equal(isCNPJ('11.222.333/0001-80'), false);
  assert.equal(isCNPJ('00000000000000'), false);
  assert.equal(isCPF('529.982.247-25'), true);
  assert.equal(isCPF('529.982.247-24'), false);
});

test('máscara aceita letras só no CNPJ', () => {
  assert.equal(maskDoc('52998224725'), '529.982.247-25');
  assert.equal(maskDoc('11222333000181'), '11.222.333/0001-81');
  assert.equal(maskDoc('12abc34501de35'), '12.ABC.345/01DE-35');
  assert.equal(maskDoc('12ABC'), '12.ABC');
  assert.equal(docChars('12.ABC.345/01DE-35'), '12ABC34501DE35');
});
