/**
 * "A IA em ação" (etapa 10g): as respostas aparecem como se estivessem sendo geradas.
 * O texto é sempre o real, que já está no HTML: o script só o esconde e o devolve palavra por palavra.
 * Sem movimento (movimento reduzido, ou o motor de animação desligado), nada acontece e tudo aparece pronto.
 *
 * - Topo: a pergunta é digitada, a Órbita "consulta a base" (as bases passam no status), a resposta é escrita com as citações acendendo e as fontes surgem uma a uma.
 * - Comparativo: as duas colunas são geradas ao mesmo tempo. Sem a Órbita, o texto sai direto da memória do
 *   modelo; com a Órbita, primeiro a busca (bases acendendo, barra e contador de fontes) e depois o texto.
 *   No fim aparece o selo da análise. Cada pergunta toca uma vez, quando a aba é aberta.
 */

const BASES = ['Planalto', 'STF', 'STJ', 'TRFs', 'TJs', 'CARF', 'Receita Federal', 'PGFN'];
// Citações que acendem: súmulas, temas, leis, artigos e números de processo.
const CITACAO =
  /(Súmula(?: Vinculante| CARF)? \d+(?: do (?:STF|STJ))?|Tema \d+(?: do (?:STF|STJ))?|(?:Lei(?: Complementar)?|LC|IN(?: RFB)?|Decreto|PN Cosit) (?:nº )?[\d.]+\/\d{2,4}|art\. \d+[ºo]?(?:, [IVX]+)?|(?:ARE|RE|REsp|AgR|HC|RHC|ADI) [\d.]+(?: AgR)?)/g;

const nFontes = (n: number) => (n === 0 ? 'nenhuma fonte' : n === 1 ? '1 fonte' : `${n} fontes`);
const comMovimento = () =>
  document.documentElement.classList.contains('anim') && !matchMedia('(prefers-reduced-motion: reduce)').matches;
const esperar = (ms: number) => new Promise((r) => setTimeout(r, ms));
const escapar = (t: string) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const acender = (t: string) => escapar(t).replace(CITACAO, '<span class="g-cite">$1</span>');

/** Escreve `texto` em `el` palavra por palavra; com `citacoes`, as citações acendem. */
async function escrever(el: HTMLElement, texto: string, ms: number, citacoes = false) {
  const partes = texto.split(/(\s+)/);
  const cursor = document.createElement('span');
  cursor.className = 'g-caret';
  let feito = '';
  for (const parte of partes) {
    feito += parte;
    el.innerHTML = citacoes ? acender(feito) : escapar(feito);
    el.append(cursor);
    if (parte.trim()) await esperar(ms);
  }
  el.innerHTML = citacoes ? acender(texto) : escapar(texto);
}

/** Toca `fn` uma vez, quando `el` aparece na tela. */
function quandoVisivel(el: Element, fn: () => void) {
  const io = new IntersectionObserver(
    (entradas) => {
      if (entradas.some((e) => e.isIntersecting)) {
        io.disconnect();
        fn();
      }
    },
    { threshold: 0.35 },
  );
  io.observe(el);
}

/* ---------------- Comparativo ---------------- */
const LIMITE = 90; // palavras geradas ao vivo por coluna; o resto aparece de uma vez

interface Bloco {
  el: HTMLElement;
  texto: string;
}

/** Os blocos de texto de uma coluna (parágrafos, títulos e itens de lista), na ordem. */
function blocos(caixa: HTMLElement): Bloco[] {
  return Array.from(caixa.querySelectorAll<HTMLElement>(':scope > p, :scope > h4, :scope > ul > li')).map((el) => ({
    el,
    texto: el.textContent ?? '',
  }));
}

interface Preparo {
  col: HTMLElement;
  comOrbita: boolean;
  status: HTMLElement;
  barra: HTMLElement | null;
}

/** O aviso e a barra de busca já vêm no HTML, no estado final; aqui voltam ao início, sem mudar de tamanho. */
function prepararColuna(col: HTMLElement, comOrbita: boolean): Preparo {
  const status = col.querySelector<HTMLElement>('[data-g-status]')!;
  const barra = comOrbita ? col.querySelector<HTMLElement>('.g-scan') : null;
  status.textContent = comOrbita ? 'Consultando a base da Órbita…' : 'Respondendo de memória, sem consultar fontes.';
  if (barra) {
    barra.querySelectorAll('span').forEach((s) => s.classList.remove('is-hit'));
    barra.querySelector<HTMLElement>('i')!.style.width = '0';
  }
  return { col, comOrbita, status, barra };
}

async function gerarColuna({ col, comOrbita, status, barra }: Preparo, fontesTotal: number) {
  const caixa = col.querySelector<HTMLElement>('[data-clip]')!;
  const mais = col.querySelector<HTMLButtonElement>('[data-more]');
  const maisVisivel = mais ? !mais.hidden : false;
  if (mais) mais.hidden = true; // só aparece quando o texto terminar de ser gerado
  const lista = blocos(caixa);
  lista.forEach((b) => {
    b.el.textContent = '';
    b.el.hidden = true;
  });

  const contador = col.querySelector<HTMLElement>('[data-g-count]');
  if (contador) contador.textContent = '0';
  if (barra) {
    const pills = Array.from(barra.querySelectorAll('span'));
    const preenche = barra.querySelector<HTMLElement>('i')!;
    for (let i = 0; i < pills.length; i++) {
      status.textContent = `Consultando a base da Órbita: ${BASES[i]}…`;
      pills[i].classList.add('is-hit');
      preenche.style.width = `${((i + 1) / pills.length) * 100}%`;
      await esperar(200);
    }
    status.textContent = 'Base consultada. Escrevendo com as fontes.';
    if (contador) contar(contador, fontesTotal);
  } else {
    status.textContent = 'Respondendo de memória, sem consultar fontes.';
  }

  let usadas = 0;
  for (const b of lista) {
    b.el.hidden = false;
    if (usadas < LIMITE) {
      await escrever(b.el, b.texto, 26, comOrbita);
      usadas += b.texto.split(/\s+/).length;
    } else {
      b.el.innerHTML = comOrbita ? acender(b.texto) : escapar(b.texto);
    }
  }
  if (!comOrbita && contador) await contar(contador, fontesTotal);
  if (mais) mais.hidden = !maisVisivel;
  const citadas = fontesTotal <= 1 ? 'citada' : 'citadas';
  status.textContent = comOrbita
    ? `Pronto: ${nFontes(fontesTotal)} ${citadas}.`
    : `Pronto: ${nFontes(fontesTotal)} ${citadas} de memória.`;
}

async function contar(el: HTMLElement, ate: number) {
  for (let i = 0; i <= ate; i++) {
    el.textContent = String(i);
    await esperar(140);
  }
}

export function gerarNoComparativo() {
  const root = document.querySelector<HTMLElement>('[data-cmp]');
  if (!root || !comMovimento()) return;
  const feitos = new WeakSet<HTMLElement>();

  const tocar = async (painel: HTMLElement) => {
    if (feitos.has(painel)) return;
    feitos.add(painel);
    const selo = painel.querySelector<HTMLElement>('.cmp-result');
    selo?.classList.add('g-wait');
    const sem = painel.querySelector<HTMLElement>('.cmp-col.sem')!;
    const com = painel.querySelector<HTMLElement>('.cmp-col.com')!;
    const prepSem = prepararColuna(sem, false);
    const prepCom = prepararColuna(com, true);
    // Com o texto ainda inteiro, cada coluna mostra a altura final: ela fica reservada, para nada abaixo
    // pular enquanto o texto é apagado e gerado de novo.
    [sem, com].forEach((c) => (c.style.minHeight = `${c.offsetHeight}px`));
    await Promise.all([
      gerarColuna(prepSem, Number(sem.dataset.fontes ?? 0)),
      gerarColuna(prepCom, Number(com.dataset.fontes ?? 0)),
    ]);
    selo?.classList.remove('g-wait');
    selo?.classList.add('g-pop');
  };

  // A primeira pergunta toca quando o comparativo aparece; as outras, quando a aba é aberta.
  quandoVisivel(root, () => {
    const aberto = root.querySelector<HTMLElement>('.cmp-panel.is-on');
    if (aberto) tocar(aberto);
    root.addEventListener('cmp:aba', (e) => tocar((e as CustomEvent<HTMLElement>).detail));
  });
}
