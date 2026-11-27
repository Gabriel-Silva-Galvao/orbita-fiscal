"""Quem pediu cada ação (`Ator`) e o erro de negócio que as rotas devolvem como resposta HTTP."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TipoAtor = Literal["cliente", "equipe", "sistema"]


@dataclass(frozen=True)
class Ator:
    """Quem pediu a ação.

    - cliente: a própria pessoa, pelo Portal; `id` é o usuário da sessão e ela só age sobre a própria conta;
    - equipe: alguém do suporte ou da administração, com `papel` e `motivo` (ainda não usado: passo 7);
    - sistema: webhook do Asaas e rotinas agendadas.
    """

    tipo: TipoAtor
    id: str | None = None
    papel: str | None = None
    motivo: str | None = None

    @staticmethod
    def cliente(usuario_id: str) -> "Ator":
        return Ator("cliente", usuario_id)

    @staticmethod
    def sistema(origem: str) -> "Ator":
        return Ator("sistema", origem)

    def pode_agir_sobre(self, usuario_id: str) -> None:
        """O cliente só mexe na própria conta. A checagem de papel da equipe acontece na rota da equipe (passo 7)."""
        if self.tipo == "cliente" and self.id != usuario_id:
            raise ErroDeNegocio(403, "outra_conta", "Esta ação é só sobre a sua própria conta.")


class ErroDeNegocio(Exception):
    """Erro com status HTTP, código e mensagem para a pessoa. O main.py devolve como {"detail": {codigo, mensagem}},
    no mesmo formato das HTTPException que as rotas usavam antes."""

    def __init__(self, status: int, codigo: str, mensagem: str):
        super().__init__(mensagem)
        self.status, self.codigo, self.mensagem = status, codigo, mensagem
