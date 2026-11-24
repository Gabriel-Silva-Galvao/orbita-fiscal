/**
 * Citações em revezamento em volta do símbolo do topo.
 *
 * Troca automática ("captura"): a cada poucos segundos, um cartão é puxado em espiral para o
 * núcleo do átomo e some; o núcleo pulsa, solta um anel, e uma citação nova é lançada do centro
 * de volta para a mesma posição.
 * Troca no hover ("virada"): ao passar o mouse, o cartão vira como uma placa de aeroporto e
 * mostra outra citação na hora.
 *
 * As citações saem de um baralho embaralhado: nenhuma repete até todas terem aparecido, e nunca
 * há duas iguais na tela. Para quando o topo sai da tela ou a aba fica em segundo plano.
 * Só roda com movimento (motion.ts); sem ele, ficam as quatro citações do exemplo, paradas.
 */
import { gsap } from 'gsap';
import type { Citacao } from '../data/citacoes';

const INTERVALO = 2600;

export function startHeroChips() {
  const art = document.querySelector<HTMLElement>('[data-chips]');
  if (!art) return;
  const todas: Citacao[] = JSON.parse(art.dataset.chips ?? '[]');
  const slots = Array.from(art.querySelectorAll<HTMLElement>('[data-chip]')).map((el, i) => ({
    el,
    pos: el.parentElement as HTMLElement,
    kind: el.querySelector<HTMLElement>('.chip-kind')!,
    text: el.querySelector<HTMLElement>('.chip-text')!,
    atual: i,
    ocupado: false,
    sobMouse: false,
  }));
  if (todas.length <= slots.length || !slots.length) return;

  // Baralho: começa pelas que ainda não apareceram; ao acabar, embaralha tudo de novo.
  let baralho: number[] = gsap.utils.shuffle(todas.map((_, i) => i).slice(slots.length));
  const proxima = () => {
    const naTela = new Set(slots.map((s) => s.atual));
    for (;;) {
      if (!baralho.length) baralho = gsap.utils.shuffle(todas.map((_, i) => i));
      const i = baralho.pop()!;
      if (!naTela.has(i)) return i;
    }
  };
  const escrever = (s: (typeof slots)[number], i: number) => {
    s.atual = i;
    s.kind.textContent = todas[i].kind;
    s.text.textContent = todas[i].text;
  };

  const visivel = (s: (typeof slots)[number]) => getComputedStyle(s.pos).display !== 'none';
  const simbolo = art.querySelector<SVGElement>('.symbol');

  /* Captura: espiral até o núcleo, pulso, lançamento de volta. */
  function capturar(s: (typeof slots)[number]) {
    s.ocupado = true;
    const a = art!.getBoundingClientRect();
    const c = s.el.getBoundingClientRect();
    const dx = a.left + a.width / 2 - (c.left + c.width / 2);
    const dy = a.top + a.height / 2 - (c.top + c.height / 2);
    const giro = dx > 0 ? 160 : -160;

    const tl = gsap.timeline({ onComplete: () => (s.ocupado = false) });
    tl.to(s.el, {
      keyframes: [
        { x: dx * 0.45 + dy * 0.25, y: dy * 0.45 - dx * 0.25, scale: 0.7, rotate: giro * 0.4, duration: 0.35, ease: 'sine.in' },
        { x: dx, y: dy, scale: 0.1, rotate: giro, autoAlpha: 0, filter: 'blur(3px)', duration: 0.35, ease: 'power3.in' },
      ],
    })
      .add(() => {
        escrever(s, proxima());
        simbolo?.classList.add('is-hot');
        setTimeout(() => simbolo?.classList.remove('is-hot'), 700);
        const anel = document.createElement('span');
        anel.className = 'chip-spark';
        anel.setAttribute('aria-hidden', 'true');
        art!.append(anel);
        gsap.fromTo(
          anel,
          { scale: 1, autoAlpha: 0.9 },
          { scale: 9, autoAlpha: 0, duration: 0.9, ease: 'expo.out', onComplete: () => anel.remove() },
        );
      })
      .fromTo(
        s.el,
        { x: dx, y: dy, scale: 0.1, rotate: -giro * 0.25, autoAlpha: 0, filter: 'blur(3px)' },
        { x: 0, y: 0, scale: 1, rotate: 0, autoAlpha: 1, filter: 'blur(0px)', duration: 0.95, ease: 'back.out(1.7)' },
        '+=0.12',
      )
      .set(s.el, { clearProps: 'filter' });
  }

  /* Virada: placa que gira no eixo horizontal e volta com a citação nova. */
  function virar(s: (typeof slots)[number]) {
    s.ocupado = true;
    gsap
      .timeline({ onComplete: () => (s.ocupado = false) })
      .to(s.el, { rotateX: -90, duration: 0.18, ease: 'power2.in', transformOrigin: '50% 50%' })
      .add(() => escrever(s, proxima()))
      .fromTo(s.el, { rotateX: 90 }, { rotateX: 0, duration: 0.5, ease: 'back.out(2.4)' })
      .fromTo(s.kind, { x: -8, autoAlpha: 0 }, { x: 0, autoAlpha: 1, duration: 0.3, ease: 'power2.out' }, '-=0.35');
  }

  if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    for (const s of slots) {
      s.el.addEventListener('pointerenter', () => {
        s.sobMouse = true;
        if (!s.ocupado) virar(s);
      });
      s.el.addEventListener('pointerleave', () => (s.sobMouse = false));
    }
  }

  let ultimo = -1;
  let timer = 0;
  let naTela = true;
  const tick = () => {
    const livres = slots.filter((s, i) => i !== ultimo && !s.ocupado && !s.sobMouse && visivel(s));
    if (livres.length) {
      const s = gsap.utils.random(livres);
      ultimo = slots.indexOf(s);
      capturar(s);
    }
  };
  const ligar = () => {
    if (!timer && naTela && !document.hidden) timer = window.setInterval(tick, INTERVALO);
  };
  const desligar = () => {
    clearInterval(timer);
    timer = 0;
  };

  new IntersectionObserver(([e]) => {
    naTela = e.isIntersecting;
    naTela ? ligar() : desligar();
  }).observe(art);
  document.addEventListener('visibilitychange', () => (document.hidden ? desligar() : ligar()));

  // Espera a entrada do topo terminar antes da primeira troca.
  setTimeout(ligar, 2400);
}
