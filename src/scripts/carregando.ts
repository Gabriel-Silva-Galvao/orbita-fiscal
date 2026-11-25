/**
 * Item 23 da rodada de testes: carregamento entre páginas.
 * A troca em si é suave pelas View Transitions do navegador (global.css, @view-transition). Se a próxima
 * página demorar mais que 250 ms, aparece o átomo da Órbita girando no centro; numa troca rápida ele nem
 * aparece. Ao voltar pelo histórico (cache do navegador), o átomo some.
 */
const caixa = document.querySelector<HTMLElement>('[data-carregando]');
let espera: number | undefined;

function esconder() {
  clearTimeout(espera);
  caixa?.classList.remove('is-on');
}

document.addEventListener('click', (e) => {
  if (!caixa || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
  const a = (e.target as Element).closest?.('a');
  if (!a || a.target === '_blank' || a.hasAttribute('download')) return;
  const url = new URL(a.href, location.href);
  if (url.origin !== location.origin) return;
  // Mesma página (só muda a âncora): não há carregamento.
  if (url.pathname === location.pathname && url.search === location.search) return;
  clearTimeout(espera);
  espera = window.setTimeout(() => caixa.classList.add('is-on'), 250);
});

addEventListener('pageshow', esconder);
addEventListener('pagehide', () => clearTimeout(espera));
