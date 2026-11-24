import { defineConfig, envField } from 'astro/config';

import react from '@astrojs/react';
import node from '@astrojs/node';

// Plano A (24/11/2026): o site inteiro em Astro. Páginas públicas são estáticas; as rotas do
// assinante declaram `prerender = false` e rodam no servidor Node. React entra só como ilha.
// Regra de negócio fica na API em Python/FastAPI (API_URL); o Astro só protege rotas e repassa.
export default defineConfig({
  site: 'https://orbitafiscal.com.br',
  trailingSlash: 'never',
  integrations: [react()],
  adapter: node({
    mode: 'standalone',
  }),
  env: {
    schema: {
      API_URL: envField.string({ context: 'server', access: 'secret', optional: true, url: true }),
    },
  },
});
