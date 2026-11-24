/**
 * Lente da cena “A base”. Sem mouse, a lente percorre uma elipse inclinada como o símbolo (uma volta
 * a cada 18 s). Com mouse em cima, ela segue o cursor com atraso suave e cresce um pouco.
 * Para quando a cena sai da tela.
 */
export function startLens() {
  document.querySelectorAll<HTMLElement>('[data-lens]').forEach((stage) => {
    const layer = stage.querySelector<HTMLElement>('.lens-layer');
    if (!layer) return;
    const fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    const tilt = (-28 * Math.PI) / 180;
    let x = 74;
    let y = 42;
    let scale = 1;
    let target: { x: number; y: number } | null = null;
    let t = 0;
    let visible = false;
    let last = performance.now();

    const io = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting;
      if (visible) {
        last = performance.now();
        requestAnimationFrame(frame);
      }
    });
    io.observe(stage);

    if (fine) {
      stage.addEventListener('pointermove', (e) => {
        const r = layer.getBoundingClientRect();
        target = { x: ((e.clientX - r.left) / r.width) * 100, y: ((e.clientY - r.top) / r.height) * 100 };
      });
      stage.addEventListener('pointerleave', () => (target = null));
    }

    function frame(now: number) {
      if (!visible) return;
      const dt = Math.min(now - last, 64);
      last = now;
      let tx: number;
      let ty: number;
      if (target) {
        tx = target.x;
        ty = target.y;
      } else {
        t += dt / 18000;
        const a = t * Math.PI * 2;
        const ex = 30 * Math.cos(a);
        const ey = 16 * Math.sin(a);
        tx = 50 + ex * Math.cos(tilt) - ey * Math.sin(tilt);
        ty = 50 + ex * Math.sin(tilt) + ey * Math.cos(tilt);
      }
      const k = Math.min(1, dt / (target ? 140 : 400));
      x += (tx - x) * k;
      y += (ty - y) * k;
      scale += ((target ? 1.18 : 1) - scale) * Math.min(1, dt / 200);
      stage.style.setProperty('--lx', `${x.toFixed(2)}%`);
      stage.style.setProperty('--ly', `${y.toFixed(2)}%`);
      stage.style.setProperty('--lr', `calc(clamp(84px, 11vw, 150px) * ${scale.toFixed(3)})`);
      requestAnimationFrame(frame);
    }
  });
}
