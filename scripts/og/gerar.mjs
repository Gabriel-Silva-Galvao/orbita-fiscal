/**
 * Gera, com o Edge ou o Chrome sem janela:
 *   public/og.png   (1200x630) de scripts/og/og.html   (imagem de compartilhamento, etapa 8b)
 *   public/logo.png (512x512)  de scripts/og/logo.html (logo dos dados estruturados, etapa 8c)
 * Uso: npm run og
 */
import { execFileSync } from 'node:child_process';
import { existsSync, statSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const aqui = path.dirname(fileURLToPath(import.meta.url));

const candidatos = [
  process.env.BROWSER,
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
].filter(Boolean);
const navegador = candidatos.find((c) => existsSync(c));
if (!navegador) {
  console.error('Não achei o Edge nem o Chrome. Informe o caminho em BROWSER.');
  process.exit(1);
}

const imagens = [
  { html: 'og.html', png: 'og.png', w: 1200, h: 630 },
  { html: 'logo.html', png: 'logo.png', w: 512, h: 512 },
];
for (const img of imagens) {
  const html = pathToFileURL(path.join(aqui, img.html)).href;
  const saida = path.resolve(aqui, '../../public', img.png);
  execFileSync(navegador, [
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--allow-file-access-from-files',
    '--force-device-scale-factor=1',
    '--virtual-time-budget=3000', // dá tempo de as fontes carregarem
    `--window-size=${img.w},${img.h}`,
    `--screenshot=${saida}`,
    html,
  ]);
  console.log(`Gerado public/${img.png} (${Math.round(statSync(saida).size / 1024)} KB)`);
}
