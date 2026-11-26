/**
 * Destino do ?next= depois de entrar: só caminhos deste site.
 *
 * ARES-SEC-004 (open redirect): a conferência antiga só barrava "//" e "/\" no começo. "/%09/site" (TAB depois da
 * barra) passava; o navegador remove TAB e quebra de linha de endereços e o destino virava "//site", outro domínio.
 * Agora: caractere de controle ou barra invertida em qualquer lugar é recusado, e o caminho é resolvido como URL
 * para conferir que continua na mesma origem.
 */
const BASE = 'https://orbita.invalid';
const PROIBIDO = /[\u0000-\u001f\u007f\\]/;

export function caminhoSeguro(next: string | null | undefined, padrao = '/conta'): string {
  if (!next || !next.startsWith('/') || next.startsWith('//') || PROIBIDO.test(next)) return padrao;
  try {
    const u = new URL(next, BASE);
    if (u.origin !== BASE) return padrao;
    return u.pathname + u.search + u.hash;
  } catch {
    return padrao;
  }
}
