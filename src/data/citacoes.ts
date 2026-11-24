/**
 * Citações que se revezam em volta do símbolo no topo da landing (src/scripts/hero-chips.ts).
 * Só referências reais, com número e órgão: aparecem soltas, sem tese, para a pessoa reconhecer
 * o tipo de fonte que o plugin traz. As quatro primeiras são as do exemplo e abrem a página.
 * Antes de publicar, entram na mesma revisão jurídica das citações dos exemplos.
 */
export type Citacao = { kind: 'Norma' | 'Súmula' | 'Súmula vinculante' | 'Precedente'; text: string };

const n = (text: string): Citacao => ({ kind: 'Norma', text });
const s = (text: string): Citacao => ({ kind: 'Súmula', text });
const sv = (num: number): Citacao => ({ kind: 'Súmula vinculante', text: `SV ${num} · STF` });
const p = (text: string): Citacao => ({ kind: 'Precedente', text });

export const citacoes: Citacao[] = [
  // As do exemplo, nesta ordem: são as primeiras que a pessoa vê.
  s('Súmula 314 · STJ'),
  n('CTN, art. 174'),
  n('Lei 6.830/1980'),
  p('Tema 566 · STJ'),

  // Código Tributário Nacional
  n('CTN, art. 3º'),
  n('CTN, art. 97'),
  n('CTN, art. 108'),
  n('CTN, art. 113'),
  n('CTN, art. 116, par. único'),
  n('CTN, art. 121'),
  n('CTN, art. 135, III'),
  n('CTN, art. 138'),
  n('CTN, art. 142'),
  n('CTN, art. 150, § 4º'),
  n('CTN, art. 151'),
  n('CTN, art. 156'),
  n('CTN, art. 165'),
  n('CTN, art. 168'),
  n('CTN, art. 170-A'),
  n('CTN, art. 173, I'),
  n('CTN, art. 185'),
  n('CTN, art. 195'),
  n('CTN, art. 205'),
  n('CTN, art. 206'),

  // Constituição Federal
  n('CF, art. 145, § 1º'),
  n('CF, art. 146, III'),
  n('CF, art. 150, I'),
  n('CF, art. 150, III, "b"'),
  n('CF, art. 150, VI, "c"'),
  n('CF, art. 153, VIII'),
  n('CF, art. 155, § 2º'),
  n('CF, art. 156, § 1º'),
  n('CF, art. 156-A'),
  n('CF, art. 195, I'),
  n('CF, art. 195, V'),

  // Leis e decretos
  n('Lei 6.830/1980, art. 40'),
  n('Lei 9.430/1996, art. 44'),
  n('Lei 9.430/1996, art. 74'),
  n('Lei 10.637/2002, art. 3º'),
  n('Lei 10.833/2003, art. 3º'),
  n('Lei 8.137/1990'),
  n('Lei 8.212/1991, art. 22'),
  n('Lei 9.784/1999'),
  n('Lei 12.016/2009'),
  n('Lei 13.988/2020'),
  n('Lei 14.689/2023'),
  n('Lei 11.101/2005'),
  n('LC 87/1996'),
  n('LC 116/2003'),
  n('LC 123/2006'),
  n('LC 214/2025'),
  n('Decreto 70.235/1972'),
  n('CPC, art. 1.036'),
  n('CPC, art. 489, § 1º'),
  n('LINDB, art. 24'),

  // Súmulas do STJ
  s('Súmula 7 · STJ'),
  s('Súmula 106 · STJ'),
  s('Súmula 112 · STJ'),
  s('Súmula 162 · STJ'),
  s('Súmula 166 · STJ'),
  s('Súmula 188 · STJ'),
  s('Súmula 213 · STJ'),
  s('Súmula 360 · STJ'),
  s('Súmula 391 · STJ'),
  s('Súmula 392 · STJ'),
  s('Súmula 393 · STJ'),
  s('Súmula 409 · STJ'),
  s('Súmula 430 · STJ'),
  s('Súmula 431 · STJ'),
  s('Súmula 435 · STJ'),
  s('Súmula 436 · STJ'),
  s('Súmula 446 · STJ'),
  s('Súmula 460 · STJ'),
  s('Súmula 461 · STJ'),
  s('Súmula 509 · STJ'),
  s('Súmula 515 · STJ'),
  s('Súmula 523 · STJ'),
  s('Súmula 555 · STJ'),
  s('Súmula 558 · STJ'),
  s('Súmula 559 · STJ'),
  s('Súmula 560 · STJ'),
  s('Súmula 583 · STJ'),
  s('Súmula 612 · STJ'),
  s('Súmula 622 · STJ'),
  s('Súmula 625 · STJ'),
  s('Súmula 649 · STJ'),
  s('Súmula 653 · STJ'),

  // Súmulas do STF e do CARF
  s('Súmula 70 · STF'),
  s('Súmula 323 · STF'),
  s('Súmula 547 · STF'),
  s('Súmula 1 · CARF'),
  s('Súmula 2 · CARF'),
  s('Súmula 11 · CARF'),

  // Súmulas vinculantes
  sv(8),
  sv(19),
  sv(21),
  sv(24),
  sv(28),
  sv(29),
  sv(31),
  sv(32),
  sv(41),
  sv(48),
  sv(50),
  sv(52),
  sv(57),

  // Temas de repercussão geral (STF) e repetitivos (STJ)
  p('Tema 69 · STF'),
  p('Tema 118 · STF'),
  p('Tema 745 · STF'),
  p('Tema 796 · STF'),
  p('Tema 881 · STF'),
  p('Tema 885 · STF'),
  p('Tema 962 · STF'),
  p('Tema 985 · STF'),
  p('Tema 1.048 · STF'),
  p('Tema 1.093 · STF'),
  p('Tema 1.124 · STF'),
  p('Tema 444 · STJ'),
  p('Tema 779 · STJ'),
  p('Tema 962 · STJ'),
  p('Tema 981 · STJ'),
  p('Tema 1.079 · STJ'),
  p('Tema 1.125 · STJ'),
  p('Tema 1.182 · STJ'),
];
