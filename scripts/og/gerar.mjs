/**
 * Gera public/og.png (1200x630) a partir de scripts/og/og.html, com o Edge ou o Chrome sem janela.
 * Uso: npm run og
 */
import { execFileSync } from 'node:child_process';
import { existsSync, statSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const aqui = path.dirname(fileURLToPath(import.meta.url));
const html = pathToFileURL(path.join(aqui, 'og.html')).href;
const saida = path.resolve(aqui, '../../public/og.png');

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

execFileSync(navegador, [
  '--headless=new',
  '--disable-gpu',
  '--hide-scrollbars',
  '--allow-file-access-from-files',
  '--force-device-scale-factor=1',
  '--virtual-time-budget=3000', // dá tempo de as fontes carregarem
  '--window-size=1200,630',
  `--screenshot=${saida}`,
  html,
]);
console.log(`Gerado ${path.relative(process.cwd(), saida)} (${Math.round(statSync(saida).size / 1024)} KB)`);
