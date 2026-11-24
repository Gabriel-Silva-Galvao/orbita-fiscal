/**
 * Exemplos da landing (a conversa em abas).
 * Fonte: comparação "Comparação por pergunta" (dashboard da equipe, 16/11/2026), com o texto
 * integral das respostas dadas COM o plugin. Os cinco são as perguntas tributárias da
 * comparação; aqui aparecem resumidos, sem acrescentar nada que não esteja na resposta original.
 * Pendência: revisão jurídica antes de ir ao ar (briefing, Página 1).
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
    id: 'prescricao',
    tab: 'Prescrição intercorrente',
    question: 'Qual é a tese do STJ sobre a contagem da prescrição intercorrente do art. 40 da Lei de Execuções Fiscais?',
    consulted: 'Consultou a base: recursos repetitivos e súmulas do STJ',
    sources: [
      {
        kind: 'PRECEDENTE',
        title: 'REsp 1.340.553/RS, Tema 566 do STJ',
        text: 'O ano de suspensão começa automaticamente quando a Fazenda toma ciência de que não há devedor ou bens localizados.',
      },
      {
        kind: 'SÚMULA',
        title: 'Súmula 314 do STJ',
        text: 'Um ano de suspensão e, em seguida, o prazo prescricional, contados em sequência.',
      },
      {
        kind: 'PRECEDENTE',
        title: 'Tema 568 do STJ',
        text: 'Só a efetiva constrição patrimonial e a efetiva citação interrompem a prescrição. O simples pedido não basta.',
      },
    ],
    answer:
      'A contagem é automática: corre por força da lei, sem depender de pedido da Fazenda nem de despacho do juiz. Terminado o ano de suspensão, começa o prazo de cinco anos.',
  },
  {
    id: 'tema69',
    tab: 'ICMS no PIS/Cofins',
    question: 'O que o STF decidiu no Tema 69 da repercussão geral e como ficou a modulação de efeitos?',
    consulted: 'Consultou a base: repercussão geral do STF',
    sources: [
      {
        kind: 'PRECEDENTE',
        title: 'RE 574.706, Tema 69 do STF',
        text: 'O ICMS não compõe a base de cálculo do PIS e da Cofins. Mérito julgado em 15/03/2017.',
      },
      {
        kind: 'PRECEDENTE',
        title: 'RE 574.706 ED (2021)',
        text: 'Modula os efeitos a partir de 15/03/2017 e define que se exclui o ICMS destacado na nota fiscal.',
      },
      {
        kind: 'NORMA',
        title: 'CF, art. 195, I, b',
        text: 'Conceito constitucional de faturamento: o ICMS é repassado ao Estado e não é receita do contribuinte.',
      },
    ],
    answer: 'Na prática, depois da modulação:',
    answerList: [
      'quem ajuizou ação ou pediu administrativamente até 15/03/2017 recupera também os valores anteriores;',
      'os demais excluem o ICMS de 15/03/2017 em diante;',
      'trânsito em julgado em 09/09/2021, segundo o portal do STF.',
    ],
  },
  {
    id: 'frete',
    tab: 'Frete entre filiais',
    question:
      'Uma indústria no lucro real quer tomar crédito de PIS/Cofins sobre o frete na transferência de produtos acabados entre seus estabelecimentos. Qual é a posição atual do CARF e da Receita?',
    consulted: 'Consultou a base: súmulas e acórdãos do CARF e normas da Receita',
    sources: [
      {
        kind: 'SÚMULA',
        title: 'Súmula CARF 217',
        text: 'Frete de produtos acabados entre estabelecimentos da empresa não gera crédito de PIS/Cofins não cumulativos.',
      },
      {
        kind: 'NORMA',
        title: 'IN RFB 2.121/2022, art. 176, § 2º, V',
        text: 'Não são insumos os serviços de transporte de produtos acabados em ou entre estabelecimentos da pessoa jurídica.',
      },
      {
        kind: 'PRECEDENTE',
        title: 'Acórdão CSRF 9303-017.374 (28/05/2026)',
        text: 'A 3ª Turma da Câmara Superior segue aplicando a súmula, por unanimidade.',
      },
    ],
    answer: 'CARF e Receita são contrários ao crédito. Onde ainda há caminho:',
    answerList: [
      'frete na venda dá crédito quando o ônus é do vendedor (Lei 10.833/2003, art. 3º, IX);',
      'frete na compra de insumos segue o crédito do insumo;',
      'para a transferência entre filiais, resta a via judicial.',
    ],
  },
  {
    id: 'crime',
    tab: 'Crime tributário',
    question: 'A partir de quando se pode falar em crime material contra a ordem tributária e quando começa a correr a prescrição?',
    consulted: 'Consultou a base: súmulas vinculantes e julgados do STF',
    sources: [
      {
        kind: 'SÚMULA',
        title: 'Súmula Vinculante 24',
        text: 'Não há crime material do art. 1º, I a IV, da Lei 8.137/1990 antes do lançamento definitivo do tributo.',
      },
      {
        kind: 'PRECEDENTE',
        title: 'ARE 1.388.712 AgR (STF, 2ª Turma)',
        text: 'A prescrição penal só começa com a constituição definitiva do crédito tributário.',
      },
      {
        kind: 'NORMA',
        title: 'Lei 9.430/1996, art. 83',
        text: 'Representação penal só após a decisão administrativa final; o parcelamento suspende a pretensão punitiva.',
      },
    ],
    answer:
      'A prescrição conta do lançamento definitivo, não da data da sonegação. Novidade de 2026: a LC 225/2026 tirou o efeito suspensivo do parcelamento para o devedor contumaz.',
  },
  {
    id: 'issqn',
    tab: 'ISSQN e LRF',
    question:
      'Qual é o entendimento do TCE-MG sobre município que concede benefício fiscal de ISSQN sem estimativa de impacto orçamentário?',
    consulted: 'Consultou a base: teses e deliberações do TCE-MG',
    sources: [
      {
        kind: 'NORMA',
        title: 'LRF, art. 14',
        text: 'Exige estimativa de impacto no exercício de início da vigência e nos dois seguintes, além de LOA ou compensação.',
      },
      {
        kind: 'PRECEDENTE',
        title: 'Representação 965785 (TCE-MG, Lavras)',
        text: 'A compensação é alternativa; a estimativa de impacto não pode faltar.',
      },
      {
        kind: 'NORMA',
        title: 'LC 116/2003, art. 8º-A',
        text: 'Alíquota mínima de 2% do ISSQN; lei municipal que a desrespeite é nula.',
      },
    ],
    answer: 'O TCE-MG não tem tese própria para o ISSQN e aplica a regra geral:',
    answerList: [
      'sem estimativa, tende a haver apontamento de irregularidade e recomendação;',
      'multa ou débito dependem de prejuízo demonstrado;',
      'abaixo de 2%, o risco é nulidade da lei e improbidade.',
    ],
  },
];
