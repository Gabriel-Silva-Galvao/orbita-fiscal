/**
 * Motor de movimento da Órbita.
 * Só roda quando <html> tem .anim (a pessoa não pediu movimento reduzido).
 * Sem ele, a página fica inteira e parada: nada aqui esconde conteúdo por conta própria.
 */
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Lenis from 'lenis';
import { startOrbits } from './orbit';
import { startHeroChips } from './hero-chips';

declare global {
  interface Window {
    __ofMotion?: boolean;
  }
}

const root = document.documentElement;
const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

if (root.classList.contains('anim')) {
  window.__ofMotion = true;
  gsap.registerPlugin(ScrollTrigger);
  // Só em desenvolvimento: permite inspecionar o movimento pelo console.
  if (import.meta.env.DEV) Object.assign(window, { gsap, ScrollTrigger });
  smoothScroll();
  splitHeadings();
  startOrbits();
  progressBar();
  stickyNav();
  heroIntro();
  heroPointer();
  startHeroChips();
  parallax();
  reveals();
  stepsLine();
  story();
  orbitReveal();
  drawOnView();
  // Fontes e imagens mudam alturas: recalcula os gatilhos quando tudo carrega.
  window.addEventListener('load', () => ScrollTrigger.refresh());
}

/* Barra fina de leitura no topo. */
function progressBar() {
  const bar = document.querySelector<HTMLElement>('.progress-bar');
  if (!bar) return;
  gsap.to(bar, {
    scaleX: 1,
    ease: 'none',
    scrollTrigger: { start: 0, end: 'max', scrub: 0.3 },
  });
}

/* O cabeçalho encolhe ao rolar, some ao descer e volta ao subir. */
function stickyNav() {
  const nav = document.querySelector<HTMLElement>('.nav');
  if (!nav) return;
  ScrollTrigger.create({
    start: 0,
    end: 'max',
    onUpdate(self) {
      const y = self.scroll();
      nav.classList.toggle('is-scrolled', y > 24);
      const hide = y > 520 && self.direction === 1 && !nav.contains(document.activeElement);
      nav.classList.toggle('is-hidden', hide);
    },
  });
}

/* Entrada do hero: palavras sobem uma a uma, o símbolo cresce, as citações chegam em órbita. */
function heroIntro() {
  const hero = document.querySelector<HTMLElement>('[data-hero]');
  if (!hero) return;
  const q = gsap.utils.selector(hero);
  const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
  tl.fromTo(q('.overline'), { autoAlpha: 0, y: 10 }, { autoAlpha: 1, y: 0, duration: 0.5 })
    .fromTo(
      q('.hw > span'),
      { yPercent: 110, autoAlpha: 0 },
      { yPercent: 0, autoAlpha: 1, duration: 0.9, stagger: 0.045, ease: 'expo.out' },
      0.1,
    )
    .fromTo(q('[data-hero-in="copy"]'), { autoAlpha: 0, y: 18 }, { autoAlpha: 1, y: 0, duration: 0.7, stagger: 0.1 }, 0.55)
    .fromTo(
      q('.hero-disc'),
      { autoAlpha: 0, scale: 0.82, rotate: -8 },
      { autoAlpha: 1, scale: 1, rotate: 0, duration: 1.3, ease: 'elastic.out(1, 0.75)' },
      0.15,
    )
    .fromTo(q('.hero-ring'), { autoAlpha: 0, scale: 0.9 }, { autoAlpha: 1, scale: 1, duration: 1.1, stagger: 0.12 }, 0.35)
    .fromTo(
      q('.chip-pos'),
      { autoAlpha: 0, scale: 0.9, y: 16 },
      { autoAlpha: 1, scale: 1, y: 0, duration: 0.7, stagger: 0.12, ease: 'back.out(1.8)' },
      0.8,
    )
    .fromTo(q('.hero-cue'), { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.6 }, 1.3);

  // Ao rolar, o hero se afasta: o texto sobe mais devagar e o símbolo afunda.
  gsap.to(q('.hero-copy'), {
    y: -60,
    autoAlpha: 0.2,
    ease: 'none',
    scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: 0.5 },
  });
  gsap.to(q('.hero-art'), {
    y: 90,
    rotate: 6,
    ease: 'none',
    scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: 0.5 },
  });
}

/* Profundidade com o mouse no hero: cada camada anda conforme seu data-depth. */
function heroPointer() {
  const hero = document.querySelector<HTMLElement>('[data-hero]');
  if (!hero || !finePointer) return;
  const layers = Array.from(hero.querySelectorAll<HTMLElement>('[data-depth]')).map((el) => ({
    depth: Number(el.dataset.depth),
    x: gsap.quickTo(el, 'x', { duration: 0.9, ease: 'power3.out' }),
    y: gsap.quickTo(el, 'y', { duration: 0.9, ease: 'power3.out' }),
  }));
  hero.addEventListener('pointermove', (e) => {
    const r = hero.getBoundingClientRect();
    const nx = (e.clientX - r.left) / r.width - 0.5;
    const ny = (e.clientY - r.top) / r.height - 0.5;
    for (const l of layers) {
      l.x(nx * 28 * l.depth);
      l.y(ny * 22 * l.depth);
    }
  });
  hero.addEventListener('pointerleave', () => {
    for (const l of layers) {
      l.x(0);
      l.y(0);
    }
  });
}

/* Parallax de rolagem: data-speed negativo anda contra a rolagem, positivo a favor. */
function parallax() {
  document.querySelectorAll<HTMLElement>('[data-speed]').forEach((el) => {
    const speed = Number(el.dataset.speed);
    const trigger = el.closest<HTMLElement>('[data-parallax]') ?? el;
    gsap.fromTo(
      el,
      { y: () => -speed * 110 },
      {
        y: () => speed * 110,
        ease: 'none',
        scrollTrigger: { trigger, start: 'top bottom', end: 'bottom top', scrub: 0.6, invalidateOnRefresh: true },
      },
    );
  });
}

/* Blocos entram em grupo, em cascata, uma vez. */
function reveals() {
  ScrollTrigger.batch('[data-reveal]', {
    start: 'top 90%',
    once: true,
    onEnter: (batch) =>
      gsap.to(batch, {
        autoAlpha: 1,
        y: 0,
        scale: 1,
        duration: 0.8,
        stagger: 0.09,
        ease: 'power3.out',
        overwrite: true,
        onStart() {
          batch.forEach((el) => {
            el.classList.add('is-in');
            const words = el.querySelectorAll('.sw > span');
            if (words.length)
              gsap.fromTo(
                words,
                { yPercent: 105 },
                { yPercent: 0, duration: 0.8, stagger: 0.035, ease: 'expo.out', delay: 0.1 },
              );
          });
        },
      }),
  });
}

/*
 * Rolagem suave com Lenis (único motor de rolagem), ligada ao ScrollTrigger.
 * Âncoras internas passam por ele, descontando o cabeçalho.
 */
function smoothScroll() {
  const lenis = new Lenis({ lerp: 0.1, wheelMultiplier: 1, anchors: { offset: -72 } });
  lenis.on('scroll', ScrollTrigger.update);
  gsap.ticker.add((t) => lenis.raf(t * 1000));
  gsap.ticker.lagSmoothing(0);
  root.classList.add('has-lenis');
  (window as any).__lenis = lenis;
}

/*
 * Títulos marcados com data-split sobem palavra por palavra.
 * O nome acessível continua inteiro: texto original em .sr-only, palavras com aria-hidden.
 */
function splitHeadings() {
  document.querySelectorAll<HTMLElement>('[data-split]').forEach((h) => {
    if (h.children.length) return; // nunca divide links ou marcação interna
    const text = h.textContent?.trim() ?? '';
    const sr = document.createElement('span');
    sr.className = 'sr-only';
    sr.textContent = text;
    const vis = document.createElement('span');
    vis.setAttribute('aria-hidden', 'true');
    text.split(/\s+/).forEach((w, i, all) => {
      const o = document.createElement('span');
      o.className = 'sw';
      const inner = document.createElement('span');
      inner.textContent = w;
      o.append(inner);
      vis.append(o);
      if (i < all.length - 1) vis.append(' ');
    });
    h.replaceChildren(sr, vis);
  });
}

/*
 * “O dia a dia”: o momento no meio da tela fica ativo e a moldura fixa troca para a foto dele.
 * A linha da esquerda se preenche com a rolagem. Só no desktop; no celular cada momento tem a própria foto.
 */
function story() {
  const grid = document.querySelector<HTMLElement>('[data-story]');
  if (!grid) return;
  const list = grid.querySelector<HTMLElement>('.story-steps')!;
  const steps = Array.from(grid.querySelectorAll<HTMLElement>('.story-step'));
  const shots = Array.from(grid.querySelectorAll<HTMLElement>('.story-shot'));
  const counter = grid.querySelector<HTMLElement>('[data-story-n]');
  let current = 0;

  const activate = (i: number) => {
    if (i === current) return;
    current = i;
    steps.forEach((s, j) => s.classList.toggle('is-active', j === i));
    shots.forEach((s, j) => s.classList.toggle('is-active', j === i));
    if (counter) counter.textContent = String(i + 1).padStart(2, '0');
  };

  gsap.matchMedia().add('(min-width: 900px)', () => {
    steps.forEach((s, i) =>
      ScrollTrigger.create({
        trigger: s,
        start: 'top 55%',
        end: 'bottom 55%',
        onToggle: (self) => self.isActive && activate(i),
      }),
    );
    ScrollTrigger.create({
      trigger: list,
      start: 'top 55%',
      end: 'bottom 55%',
      scrub: true,
      onUpdate: (self) => list.style.setProperty('--p', self.progress.toFixed(3)),
    });
  });

  gsap.matchMedia().add('(max-width: 899px)', () => {
    grid.querySelectorAll<HTMLElement>('.story-inline').forEach((fig) =>
      gsap.fromTo(
        fig,
        { clipPath: 'inset(100% 0 0 0 round 14px)' },
        {
          clipPath: 'inset(0% 0 0 0 round 14px)',
          duration: 1,
          ease: 'expo.out',
          scrollTrigger: { trigger: fig, start: 'top 85%', once: true },
        },
      ),
    );
  });
}

/* Brasília: a foto se abre como uma órbita, de um círculo pequeno até a moldura inteira. */
function orbitReveal() {
  document.querySelectorAll<HTMLElement>('[data-orbit-reveal]').forEach((box) => {
    const photo = box.querySelector<HTMLElement>('.br-photo');
    if (!photo) return;
    gsap.fromTo(
      photo,
      { '--open': 0 },
      {
        '--open': 1,
        ease: 'none',
        scrollTrigger: { trigger: box, start: 'top 90%', end: 'center 50%', scrub: 0.6 },
      },
    );
  });
}

/* Como funciona: a linha corre com a rolagem e acende cada passo quando chega nele. */
function stepsLine() {
  const wrap = document.querySelector<HTMLElement>('[data-steps]');
  if (!wrap) return;
  const steps = Array.from(wrap.querySelectorAll<HTMLElement>('.step'));
  ScrollTrigger.create({
    trigger: wrap,
    start: 'top 75%',
    end: 'bottom 55%',
    scrub: 0.4,
    onUpdate(self) {
      const p = self.progress;
      wrap.style.setProperty('--p', p.toFixed(3));
      steps.forEach((s, i) => s.classList.toggle('is-lit', p >= i / steps.length + 0.02));
    },
  });
}


/* Ilustrações em traço se desenham ao entrar na tela. */
function drawOnView() {
  document.querySelectorAll<SVGElement>('[data-draw]').forEach((svg) => {
    ScrollTrigger.create({
      trigger: svg,
      start: 'top 85%',
      once: true,
      onEnter: () => svg.classList.add('is-drawn'),
    });
  });
}


