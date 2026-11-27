# Órbita: regras do projeto

## Segurança em toda funcionalidade nova

- Antes de construir qualquer funcionalidade, passe pelo checklist de `docs/ciberseguranca.md`, seção 0.1.
- Riscos que a funcionalidade traz e que não forem resolvidos na hora entram em `docs/seguranca/registro.json`
  (situação `futura` ou `observacao`) no mesmo commit.
- Vulnerabilidade encontrada ou corrigida: atualize a ficha no `registro.json` (situação, teste, commit), a seção 5.1
  de `docs/ciberseguranca.md` e republique o painel `docs/seguranca/painel.html` no mesmo link
  (https://claude.ai/artifact/HPpHTMdkdzKGD2T5Xr41d6), publicando o `registro.json` junto como `registro.json`.
- Toda correção de segurança tem teste de regressão e commit próprio.
