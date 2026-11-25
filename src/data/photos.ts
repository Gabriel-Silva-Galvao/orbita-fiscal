/**
 * Fotos reais, Licença Unsplash (uso gratuito, comercial inclusive, sem obrigação de crédito;
 * creditamos mesmo assim). Servidas pelo CDN do Unsplash (images.unsplash.com), que é o uso
 * recomendado por eles. Escolhidas em 23/11/2026. Para produção, dá para baixar e servir do
 * próprio site com o mesmo crédito.
 */
export interface Photo {
  id: string;
  page: string;
  author: string;
  profile: string;
  alt: string;
}

const u = (slug: string) => `https://unsplash.com/photos/${slug}`;
const p = (handle: string) => `https://unsplash.com/@${handle}`;

export const photos = {
  congresso: {
    id: 'photo-1720650154225-ab0dbdf78d2c',
    page: u('fYy4SWxcgOs'),
    author: 'Gabriel Tiveron',
    profile: p('gabrieltiveron'),
    alt: 'Congresso Nacional, em Brasília, refletido no espelho d’água.',
  },
  mesa: {
    id: 'photo-1487017159836-4e23ece2e4cf',
    page: u('9l_326FISzk'),
    author: 'Luca Bravo',
    profile: p('lucabravo'),
    alt: 'Notebook aberto sobre uma mesa de madeira, ao lado de uma cadeira branca.',
  },
} satisfies Record<string, Photo>;

export type PhotoKey = keyof typeof photos;

/** URL no tamanho certo; `auto=format` entrega AVIF/WebP quando o navegador aceita. */
export const src = (key: PhotoKey, w: number, q = 72) =>
  `https://images.unsplash.com/${photos[key].id}?auto=format&fit=crop&w=${w}&q=${q}`;

export const srcset = (key: PhotoKey, widths = [480, 800, 1200, 1600, 2000]) =>
  widths.map((w) => `${src(key, w)} ${w}w`).join(', ');
