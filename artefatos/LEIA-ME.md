# Artefatos da Órbita Fiscal

Cópia de todos os artefatos publicados no claude.ai, exportada em 24/11/2026.

| Pasta | Artefato | Link original | Formato |
| --- | --- | --- | --- |
| `01-briefings/` | Briefings das páginas da Órbita Fiscal | https://claude.ai/artifact/RAhv8e9CD2NQ5F2DXqHs44 | Markdown + mapa de páginas (imagem) |
| `02-pendencias-e-decisoes/` | Órbita Fiscal: pendências e decisões | https://claude.ai/artifact/LFaGLAW9EJnNm4Q1R26eTU | Markdown |
| `03-progresso-doc/` | Órbita Fiscal: progresso do site (doc antigo, substituído pelo painel) | https://claude.ai/artifact/FvYozFYej3pkvZKoBsknqH | Markdown |
| `04-painel-de-progresso/` | Progresso do site Órbita Fiscal (painel interativo) | https://claude.ai/artifact/Ea4BJ3bdkkshfCkQemurZu | HTML + dados em JSON |
| `05-design-system/` | Design system Órbita Fiscal (Limiar Esmeralda) | https://claude.ai/artifact/RvyazHgvww5Zk3qzojPFYA | Markdown, JSON, prévias HTML, SVG e PNG |

## Observações

- **Docs (01 a 03):** para Word ou PDF, abra o doc no claude.ai e use o menu Export, que fica no nome do doc.
- **Painel (04):** `progresso.html` lê o status das páginas e os bloqueios do banco de dados do claude.ai. Fora de lá, a página mostra só a parte fixa (passo a passo, histórico, links); o status atual está em `dados/paginas/*.json` e `dados/bloqueios/*.json`.
- **Design system (05):** `tokens.json` é a fonte das cores, fontes, espaços e raios; `tokens.css` é a versão usada no site. Cada componente tem `README.md` com as regras e `preview.html` com a prévia. As prévias usam as variáveis de `tokens.css`; para abrir uma solta no navegador, inclua esse arquivo.
- Os artefatos são privados no claude.ai. Para outra pessoa abrir os links, compartilhe pelo menu Share.
