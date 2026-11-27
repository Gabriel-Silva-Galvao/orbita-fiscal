"""Camada de serviços (preparação para suporte e admin, passo 2, 27/11/2026).

As regras de negócio ficam aqui, sem FastAPI, para que as rotas do cliente e, depois, as da equipe e as rotinas
usem as mesmas funções. Toda função que muda algo recebe o `Ator` (quem pediu). Ver docs/preparacao-suporte-admin.md.
"""
