/**
 * Motor das órbitas do símbolo atômico.
 * Repouso: elétrons internos dão uma volta a cada 7 s, o de valência a cada 12 s.
 * Mouse ou foco: aceleram até 6x e os anéis se inclinam de −28° para −14°.
 * `data-boost` no <svg> pede uma aceleração temporária (ex.: “consultando a base”).
 * Fora da tela, o símbolo para de calcular.
 */
const TAU = Math.PI * 2;
const RINGS = {
  in: { rx: 27, ry: 17, period: 7000 },
  out: { rx: 43, ry: 28, period: 12000 },
} as const;

interface Electron {
  el: SVGGElement;
  ring: keyof typeof RINGS;
  angle: number;
}

interface Orbit {
  svg: SVGSVGElement;
  rings: SVGGElement;
  electrons: Electron[];
  pace: number;
  speed: number;
  tilt: number;
  hot: boolean;
  visible: boolean;
}

export function startOrbits(root: ParentNode = document) {
  const orbits: Orbit[] = [];

  root.querySelectorAll<SVGSVGElement>('svg[data-orbit]').forEach((svg) => {
    const rings = svg.querySelector<SVGGElement>('.sym-rings');
    if (!rings) return;
    const electrons = Array.from(svg.querySelectorAll<SVGGElement>('.sym-e')).map((el) => ({
      el,
      ring: (el.dataset.ring as 'in' | 'out') ?? 'in',
      angle: Number(el.dataset.phase ?? 0),
    }));
    const o: Orbit = {
      svg,
      rings,
      electrons,
      pace: Number(svg.dataset.pace ?? 1),
      speed: 1,
      tilt: -28,
      hot: false,
      visible: true,
    };
    const host = svg.closest<HTMLElement>('a, button, [data-orbit-host]') ?? (svg as unknown as HTMLElement);
    const on = () => {
      o.hot = true;
      svg.classList.add('is-hot');
    };
    const off = () => {
      o.hot = false;
      svg.classList.remove('is-hot');
    };
    host.addEventListener('pointerenter', on);
    host.addEventListener('pointerleave', off);
    host.addEventListener('focusin', on);
    host.addEventListener('focusout', off);
    orbits.push(o);
  });

  if (!orbits.length) return;

  const io = new IntersectionObserver((entries) => {
    for (const e of entries) {
      const o = orbits.find((x) => x.svg === e.target);
      if (o) o.visible = e.isIntersecting;
    }
  });
  orbits.forEach((o) => io.observe(o.svg));

  const place = (r: { rx: number; ry: number }, a: number) =>
    [(50 + r.rx * Math.cos(a)).toFixed(2), (50 + r.ry * Math.sin(a)).toFixed(2)] as const;

  let last = performance.now();
  const frame = (now: number) => {
    const dt = Math.min(now - last, 64);
    last = now;
    for (const o of orbits) {
      if (!o.visible) continue;
      const boost = Number(o.svg.dataset.boost ?? 0);
      const target = o.hot ? 6 : boost > 0 ? boost : 1;
      o.speed += (target - o.speed) * Math.min(1, dt / 220);
      const tiltTarget = o.hot ? -14 : -28;
      o.tilt += (tiltTarget - o.tilt) * Math.min(1, dt / 260);
      o.rings.setAttribute('transform', `rotate(${o.tilt.toFixed(2)} 50 50)`);
      for (const e of o.electrons) {
        const r = RINGS[e.ring];
        e.angle = (e.angle + (TAU * dt * o.speed * o.pace) / r.period) % TAU;
        const [x, y] = place(r, e.angle);
        e.el.setAttribute('transform', `translate(${x} ${y})`);
      }
    }
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
}
