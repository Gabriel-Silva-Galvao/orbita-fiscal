/**
 * Mini cartões de citação (Norma, Súmula, Precedente) em revezamento pelo site.
 *
 * Cada grupo é um elemento com [data-chips] (a lista de citações em JSON) e cartões [data-chip],
 * cada um com [data-chip-kind], [data-chip-text] e [data-chip-i] (índice da citação inicial).
 * O jeito da troca automática vem de [data-chips-mode]:
 *   "orbita" (topo): o cartão é puxado em espiral para o núcleo do átomo, o núcleo pulsa e solta
 *     um anel, e a citação nova sai do centro dando três quartos de volta na órbita até pousar.
 *   "pagina" (cena dos livros): o cartão vira como a página de um livro e volta com a nova.
 *   "carimbo" (cena de Brasília): o cartão sobe e some; a nova desce e bate no lugar, com um anel.
 * Em todos, a citação nova se "decifra" da esquerda para a direita, e passar o mouse vira o
 * cartão na hora, como uma placa de aeroporto.
 *
 * Um baralho só para o site inteiro: nenhuma citação repete até todas terem aparecido, e nunca há
 * duas iguais na tela. Cada grupo para quando sai da tela ou a aba fica em segundo plano.
 * Só roda com movimento (motion.ts); sem ele, ficam as citações iniciais, paradas.
 */
import { gsap } from 'gsap';
import type { Citacao } from '../data/citacoes';

// Uma troca a cada 6 s por grupo (cerca de 10 por minuto), em câmera lenta: as trocas
// automáticas rodam a 60% da velocidade original (cerca de 4 s do começo ao pouso no topo).
const INTERVALO = 6000;
const RITMO = 0.6;

type Slot = {
  el: HTMLElement;
  pos: HTMLElement;
  kind: HTMLElement;
  text: HTMLElement;
  atual: number;
  ocupado: boolean;
  sobMouse: boolean;
};

export function startHeroChips() {
  const grupos = Array.from(document.querySelectorAll<HTMLElement>('[data-chips]'));
  if (!grupos.length) return;
  const todas: Citacao[] = JSON.parse(grupos[0].dataset.chips ?? '[]');

  const todosSlots: Slot[] = [];
  const slotsPorGrupo = grupos.map((g) =>
    Array.from(g.querySelectorAll<HTMLElement>('[data-chip]')).map((el) => {
      const s: Slot = {
        el,
        pos: el.parentElement as HTMLElement,
        kind: el.querySelector<HTMLElement>('[data-chip-kind]')!,
        text: el.querySelector<HTMLElement>('[data-chip-text]')!,
        atual: Number(el.dataset.chipI),
        ocupado: false,
        sobMouse: false,
      };
      todosSlots.push(s);
      return s;
    }),
  );
  if (todas.length <= todosSlots.length) return;

  // Baralho: começa pelas que ainda não apareceram; ao acabar, embaralha tudo de novo.
  const iniciais = new Set(todosSlots.map((s) => s.atual));
  let baralho: number[] = gsap.utils.shuffle(todas.map((_, i) => i).filter((i) => !iniciais.has(i)));
  const proxima = () => {
    const naTela = new Set(todosSlots.map((s) => s.atual));
    for (;;) {
      if (!baralho.length) baralho = gsap.utils.shuffle(todas.map((_, i) => i));
      const i = baralho.pop()!;
      if (!naTela.has(i)) return i;
    }
  };
  const escrever = (s: Slot, i: number) => {
    s.atual = i;
    s.kind.textContent = todas[i].kind;
    s.text.textContent = todas[i].text;
  };

  /* O texto final se revela da esquerda para a direita, com caracteres trocando até assentar. */
  function decifrar(alvo: HTMLElement, duracao = 0.6 / RITMO) {
    const final = alvo.textContent ?? '';
    const sinais = '§0123456789ºªIVXLCDM.,/-';
    const estado = { p: 0 };
    gsap.to(estado, {
      p: 1,
      duration: duracao,
      ease: 'none',
      onUpdate() {
        const n = Math.floor(estado.p * final.length);
        alvo.textContent =
          final.slice(0, n) +
          final
            .slice(n)
            .split('')
            .map((ch) => (ch === ' ' ? ' ' : sinais[(Math.random() * sinais.length) | 0]))
            .join('');
      },
      onComplete: () => (alvo.textContent = final),
    });
  }

  /* Virada no hover: placa que gira no eixo horizontal e volta com a citação nova. */
  function virar(s: Slot) {
    s.ocupado = true;
    gsap
      .timeline({ onComplete: () => (s.ocupado = false) })
      .to(s.el, { rotateX: -90, duration: 0.3, ease: 'power2.in', transformOrigin: '50% 50%' })
      .add(() => escrever(s, proxima()))
      .fromTo(s.el, { rotateX: 90 }, { rotateX: 0, duration: 0.75, ease: 'back.out(2)' })
      .fromTo(s.kind, { x: -8, autoAlpha: 0 }, { x: 0, autoAlpha: 1, duration: 0.4, ease: 'power2.out' }, '-=0.5');
  }

  /*
   * Troca automática "carimbo" (cena de Brasília): o cartão sobe e some como um carimbo
   * levantado, e a citação nova desce de cima, bate no lugar com um tranco e deixa um anel.
   */
  function carimbar(s: Slot, grupo: HTMLElement) {
    s.ocupado = true;
    gsap
      .timeline({ onComplete: () => (s.ocupado = false) })
      .timeScale(RITMO)
      .to(s.el, { y: -18, scale: 1.08, autoAlpha: 0, filter: 'blur(2px)', duration: 0.45, ease: 'power2.in' })
      .add(() => {
        escrever(s, proxima());
        decifrar(s.text);
      })
      .fromTo(
        s.el,
        { y: -30, scale: 1.35, rotate: -6, autoAlpha: 0, filter: 'blur(3px)' },
        { y: 0, scale: 1, rotate: 0, autoAlpha: 1, filter: 'blur(0px)', duration: 0.5, ease: 'power4.in' },
      )
      .add(() => {
        const g = grupo.getBoundingClientRect();
        const c = s.el.getBoundingClientRect();
        const anel = document.createElement('span');
        anel.className = 'chip-spark';
        anel.setAttribute('aria-hidden', 'true');
        Object.assign(anel.style, { left: `${c.left - g.left + c.width / 2}px`, top: `${c.top - g.top + c.height / 2}px` });
        grupo.append(anel);
        gsap.fromTo(
          anel,
          { scale: 1, autoAlpha: 0.9 },
          { scale: 14, autoAlpha: 0, duration: 0.8 / RITMO, ease: 'expo.out', onComplete: () => anel.remove() },
        );
      })
      .to(s.el, { keyframes: [{ scale: 0.95, duration: 0.08 }, { scale: 1, duration: 0.4, ease: 'elastic.out(1, 0.45)' }] })
      .fromTo(s.kind, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.3 }, '-=0.3')
      .set(s.el, { clearProps: 'filter' });
  }

  /* Troca automática "pagina": o cartão vira pela borda esquerda como a folha de um livro. */
  function virarPagina(s: Slot) {
    s.ocupado = true;
    gsap
      .timeline({ onComplete: () => (s.ocupado = false) })
      .timeScale(RITMO)
      .to(s.el, { rotateY: -100, autoAlpha: 0.2, duration: 0.55, ease: 'power2.in', transformOrigin: '0% 50%' })
      .add(() => {
        escrever(s, proxima());
        decifrar(s.text);
      })
      .fromTo(
        s.el,
        { rotateY: 100, autoAlpha: 0.2 },
        { rotateY: 0, autoAlpha: 1, duration: 0.9, ease: 'back.out(1.4)', transformOrigin: '0% 50%' },
      )
      .fromTo(s.kind, { autoAlpha: 0, y: 4 }, { autoAlpha: 1, y: 0, duration: 0.3 }, '-=0.5');
  }

  /* Troca automática "orbita": espiral até o núcleo, pulso, lançamento de volta em órbita. */
  function capturar(s: Slot, grupo: HTMLElement) {
    s.ocupado = true;
    const a = grupo.getBoundingClientRect();
    const c = s.el.getBoundingClientRect();
    const dx = a.left + a.width / 2 - (c.left + c.width / 2);
    const dy = a.top + a.height / 2 - (c.top + c.height / 2);
    const giro = dx > 0 ? 160 : -160;
    const simbolo = grupo.querySelector<SVGElement>('.symbol');

    gsap
      .timeline({ onComplete: () => (s.ocupado = false) })
      .timeScale(RITMO)
      .to(s.el, {
        keyframes: [
          { x: dx * 0.45 + dy * 0.25, y: dy * 0.45 - dx * 0.25, scale: 0.7, rotate: giro * 0.4, duration: 0.35, ease: 'sine.in' },
          { x: dx, y: dy, scale: 0.1, rotate: giro, autoAlpha: 0, filter: 'blur(3px)', duration: 0.35, ease: 'power3.in' },
        ],
      })
      .add(() => {
        escrever(s, proxima());
        simbolo?.classList.add('is-hot');
        setTimeout(() => simbolo?.classList.remove('is-hot'), 700 / RITMO);
        const anel = document.createElement('span');
        anel.className = 'chip-spark';
        anel.setAttribute('aria-hidden', 'true');
        grupo.append(anel);
        gsap.fromTo(
          anel,
          { scale: 1, autoAlpha: 0.9 },
          { scale: 9, autoAlpha: 0, duration: 0.9 / RITMO, ease: 'expo.out', onComplete: () => anel.remove() },
        );
      })
      .add(entrarEmOrbita(s, dx, dy), '+=0.1');
  }

  /*
   * A citação nasce no núcleo e sai em espiral pela mesma elipse inclinada do símbolo (−28°),
   * dando três quartos de volta em torno do átomo até pousar no lugar dela.
   */
  function entrarEmOrbita(s: Slot, dx: number, dy: number) {
    const tilt = (-28 * Math.PI) / 180;
    const vx = -dx;
    const vy = -dy;
    const ux = vx * Math.cos(-tilt) - vy * Math.sin(-tilt);
    const uy = vx * Math.sin(-tilt) + vy * Math.cos(-tilt);
    const achat = 0.55;
    const a = Math.hypot(ux, uy / achat);
    const fim = Math.atan2(uy / achat, ux);
    const volta = Math.PI * 1.5;
    const ponto = (t: number) => {
      const r = 0.1 + 0.9 * gsap.parseEase('power2.out')(t);
      const phi = fim - volta * (1 - t);
      const ex = r * a * Math.cos(phi);
      const ey = r * a * achat * Math.sin(phi);
      return { x: ex * Math.cos(tilt) - ey * Math.sin(tilt) - vx, y: ex * Math.sin(tilt) + ey * Math.cos(tilt) - vy };
    };

    const voo = { t: 0 };
    const p0 = ponto(0);
    return gsap
      .timeline()
      .set(s.el, { x: p0.x, y: p0.y, scale: 0.25, rotate: 0, autoAlpha: 0, filter: 'blur(2px)' })
      .to(s.el, { autoAlpha: 1, filter: 'blur(0px)', duration: 0.35, ease: 'power1.out' }, 0)
      .to(
        voo,
        {
          t: 1,
          duration: 1.25,
          ease: 'power2.inOut',
          onUpdate() {
            const p = ponto(voo.t);
            const q = ponto(Math.min(1, voo.t + 0.02));
            // O cartão se inclina na direção do voo e endireita ao pousar.
            const rumo = (Math.atan2(q.y - p.y, q.x - p.x) * 180) / Math.PI;
            const peso = 1 - voo.t;
            gsap.set(s.el, { x: p.x, y: p.y, scale: 0.25 + 0.75 * voo.t, rotate: gsap.utils.wrap(-180, 180, rumo) * 0.18 * peso });
          },
        },
        0,
      )
      .add(() => decifrar(s.text), 0.75)
      .fromTo(s.kind, { autoAlpha: 0, y: 4 }, { autoAlpha: 1, y: 0, duration: 0.3 }, 1.05)
      .to(s.el, { keyframes: [{ scale: 1.06, duration: 0.12 }, { scale: 1, duration: 0.35, ease: 'elastic.out(1, 0.5)' }] }, 1.25)
      .set(s.el, { clearProps: 'filter' });
  }

  const hover = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  grupos.forEach((grupo, gi) => {
    const slots = slotsPorGrupo[gi];
    if (!slots.length) return;
    const modo = grupo.dataset.chipsMode ?? 'orbita';

    if (hover) {
      for (const s of slots) {
        s.el.addEventListener('pointerenter', () => {
          s.sobMouse = true;
          if (!s.ocupado) virar(s);
        });
        s.el.addEventListener('pointerleave', () => (s.sobMouse = false));
      }
    }

    const visivel = (s: Slot) => getComputedStyle(s.pos).display !== 'none';
    let ultimo = -1;
    let timer = 0;
    let naTela = false;
    const tick = () => {
      const livres = slots.filter((s, i) => i !== ultimo && !s.ocupado && !s.sobMouse && visivel(s));
      if (!livres.length) return;
      const s = gsap.utils.random(livres);
      ultimo = slots.indexOf(s);
      if (modo === 'pagina') virarPagina(s);
      else if (modo === 'carimbo') carimbar(s, grupo);
      else capturar(s, grupo);
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
    }).observe(grupo);
    document.addEventListener('visibilitychange', () => (document.hidden ? desligar() : ligar()));
  });
}
