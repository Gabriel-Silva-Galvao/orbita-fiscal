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
  lombadas: {
    id: 'photo-1765969934461-2f945e5aacb8',
    page: u('wPCfwvdTdJs'),
    author: 'Antony Hyson Seltran',
    profile: p('hyson'),
    alt: 'Lombadas de livros antigos lado a lado em uma estante.',
  },
  estante: {
    id: 'photo-1769093031054-a8d8846de39c',
    page: u('uhfABvl9C74'),
    author: 'Ilya Semenov',
    profile: p('si1og'),
    alt: 'Fileiras de livros antigos em prateleiras de madeira.',
  },
  pilha: {
    id: 'photo-1583521214690-73421a1829a9',
    page: u('snNHKZ-mGfE'),
    author: 'Wesley Tingey',
    profile: p('wesleyphotography'),
    alt: 'Pilhas altas de documentos em papel e pastas de arquivo sobre uma mesa.',
  },
  laptop: {
    id: 'photo-1749648329134-75ed14f7dae5',
    page: u('nHBfgBht998'),
    author: 'Vinícius Marçall',
    profile: p('viniciusmarcall'),
    alt: 'Mãos digitando em um notebook sobre uma mesa de trabalho.',
  },
  livros: {
    id: 'photo-1423592707957-3b212afa6733',
    page: u('EKy2OTRPXdw'),
    author: 'Mikhail Pavstyuk',
    profile: p('pavstyuk'),
    alt: 'Três livros empilhados ao lado de um caderno aberto e uma caneta.',
  },
  assinatura: {
    id: 'photo-1763729805496-b5dbf7f00c79',
    page: u('QI6NLgN5XnM'),
    author: 'Jakub Żerdzicki',
    profile: p('jakubzerdzicki'),
    alt: 'Pessoa assinando um documento com caneta.',
  },
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
