/**
 * Motor de movimento da Órbita.
 * Só roda quando <html> tem .anim (a pessoa não pediu movimento reduzido).
 * Sem ele, a página fica inteira e parada: nada aqui esconde conteúdo por conta própria.
 */
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Lenis from 'lenis';
import { startOrbits } from './orbit';

declare global {
  interface Window {
    __ofMotion?: boolean;
  }
}

const root = document.documentElement;

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
  parallax();
  reveals();
  stepsLine();
  drawOnView();
  irParaAncora((window as any).__lenis);
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
      // O cabeçalho fica sempre fixo à vista (25/11/2026): não se esconde mais ao rolar para baixo.
    },
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
            if (el.classList.contains('is-in')) return; // já mostrado na chegada por âncora (item 35)
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
 * Item 35: ao chegar de outra página com #âncora (ex.: /ajuda#contato), o navegador pula antes de fontes e imagens
 * mudarem as alturas, e a tela ficava vazia por segundos. Vai direto ao alvo agora e de novo quando tudo carrega.
 */
function irParaAncora(lenis: Lenis) {
  const id = decodeURIComponent(location.hash.slice(1));
  const alvo = id ? document.getElementById(id) : null;
  if (!alvo) return;
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  // A seção de destino aparece pronta, sem esperar a animação de entrada.
  const blocos = [alvo, ...alvo.querySelectorAll<HTMLElement>('[data-reveal]')].filter((el) => el.matches('[data-reveal]'));
  gsap.set(blocos, { autoAlpha: 1, y: 0, scale: 1 });
  blocos.forEach((el) => el.classList.add('is-in'));
  gsap.set(alvo.querySelectorAll('.sw > span'), { yPercent: 0 });
  const ir = () => {
    ScrollTrigger.refresh();
    lenis.scrollTo(alvo, { offset: -72, immediate: true, force: true });
    ScrollTrigger.update();
  };
  requestAnimationFrame(ir);
  document.fonts?.ready.then(ir);
  window.addEventListener('load', ir, { once: true });
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


