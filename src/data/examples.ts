/**
 * Exemplos da landing. Todos ILUSTRATIVOS.
 * Pendência: revisão jurídica antes de ir ao ar (briefing, Página 1).
 * As abas 2 e 3 foram redigidas pelo Claude em 23/11/2026 com normas e precedentes
 * reais de execução fiscal; conferir redação, números e datas com um advogado.
 */
export interface Source {
  kind: 'NORMA' | 'SÚMULA' | 'PRECEDENTE';
  title: string;
  text: string;
}

export interface Example {
  id: string;
  tab: string;
  question: string;
  consulted: string;
  sources: Source[];
  answer: string;
  answerList?: string[];
}

export const examples: Example[] = [
  {
    id: 'pesquisar',
    tab: 'Pesquisar',
    question:
      'Execução fiscal parada sem bens localizados. Quando começa a correr a prescrição intercorrente? Traga o fundamento.',
    consulted: 'Consultou a base: legislação e súmulas do STJ',
    sources: [
      {
        kind: 'NORMA',
        title: 'Lei 6.830/1980, art. 40',
        text: 'Suspende a execução enquanto não há devedor ou bens localizados. Passado um ano, os autos vão ao arquivo.',
      },
      {
        kind: 'SÚMULA',
        title: 'Súmula 314 do STJ',
        text: 'Sem bens penhoráveis, o processo fica suspenso por um ano. Depois disso corre o prazo prescricional de cinco anos.',
      },
      {
        kind: 'NORMA',
        title: 'CTN, art. 174',
        text: 'Fixa em cinco anos o prazo para cobrar o crédito tributário, contado da constituição definitiva.',
      },
    ],
    answer:
      'Próximo passo: conferir nos autos a data em que a Fazenda tomou ciência da suspensão.',
  },
  {
    id: 'conferir',
    tab: 'Conferir o processo',
    question:
      'Vou alegar prescrição intercorrente nesta execução fiscal. O que ainda falta reunir nos autos?',
    consulted: 'Consultou a base: legislação e recursos repetitivos do STJ',
    sources: [
      {
        kind: 'PRECEDENTE',
        title: 'REsp 1.340.553/RS, Tema 566 do STJ',
        text: 'O prazo de um ano de suspensão começa quando a Fazenda é intimada de que não há bens ou devedor, sem depender de despacho.',
      },
      {
        kind: 'NORMA',
        title: 'Lei 6.830/1980, art. 40, § 4º',
        text: 'O juiz pode reconhecer a prescrição intercorrente de ofício, depois de ouvir a Fazenda Pública.',
      },
    ],
    answer: 'Para sustentar o pedido, confira se os autos têm:',
    answerList: [
      'a intimação da Fazenda sobre a falta de bens, com data;',
      'a contagem de um ano de suspensão e mais cinco anos;',
      'a ausência de penhora ou citação efetiva no período.',
    ],
  },
  {
    id: 'peca',
    tab: 'Preparar a peça',
    question:
      'Monte o esboço de uma exceção de pré-executividade por prescrição intercorrente, com as citações marcadas.',
    consulted: 'Consultou a base: súmulas, repetitivos e legislação',
    sources: [
      {
        kind: 'SÚMULA',
        title: 'Súmula 393 do STJ',
        text: 'Admite a exceção de pré-executividade em execução fiscal para matéria conhecível de ofício que não exija prova.',
      },
      {
        kind: 'PRECEDENTE',
        title: 'REsp 1.340.553/RS, Tema 566 do STJ',
        text: 'Define o marco inicial da suspensão e o que interrompe a contagem.',
      },
      {
        kind: 'NORMA',
        title: 'Lei 6.830/1980, art. 40, § 4º',
        text: 'Base para o reconhecimento da prescrição intercorrente.',
      },
    ],
    answer: 'Esboço em quatro partes, cada citação marcada para conferência:',
    answerList: [
      'Cabimento da exceção [Súmula 393];',
      'Marco inicial da suspensão [Tema 566];',
      'Decurso de um ano mais cinco anos [art. 40, § 4º];',
      'Pedido de extinção da execução.',
    ],
  },
];
