"""CPF e CNPJ da nota fiscal: normaliza e confere os dígitos verificadores.

ARES-QA-009: a API só olhava se havia 11 ou 14 dígitos, então qualquer número inventado ia para o Asaas e para a nota.
CNPJ alfanumérico (Receita Federal, a partir de julho de 2026): as 12 primeiras posições podem ter letras maiúsculas e
os 2 dígitos verificadores continuam numéricos; no cálculo, cada caractere vale ord(c) - 48 (0 a 9 valem 0 a 9,
A vale 17, B vale 18...), com os mesmos pesos do CNPJ numérico.
"""
from __future__ import annotations

import re

_SEPARADORES = re.compile(r"[\s./-]")
_CPF = re.compile(r"^\d{11}$")
_CNPJ = re.compile(r"^[0-9A-Z]{12}\d{2}$")


def _dv(valores: list[int], pesos: list[int]) -> int:
    resto = sum(v * p for v, p in zip(valores, pesos)) % 11
    return 0 if resto < 2 else 11 - resto


def cpf_valido(cpf: str) -> bool:
    if not _CPF.match(cpf) or len(set(cpf)) == 1:
        return False
    n = [int(c) for c in cpf]
    d1 = (sum(v * p for v, p in zip(n[:9], range(10, 1, -1))) * 10) % 11 % 10
    d2 = (sum(v * p for v, p in zip(n[:10], range(11, 1, -1))) * 10) % 11 % 10
    return n[9] == d1 and n[10] == d2


def cnpj_valido(cnpj: str) -> bool:
    if not _CNPJ.match(cnpj) or len(set(cnpj)) == 1:
        return False
    v = [ord(c) - 48 for c in cnpj]
    d1 = _dv(v[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = _dv(v[:12] + [d1], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return v[12] == d1 and v[13] == d2


def normalizar_documento(texto: str) -> str | None:
    """Devolve o CPF ou CNPJ só com os caracteres que contam (letras em maiúscula), ou None se não for válido."""
    doc = _SEPARADORES.sub("", texto or "").upper()
    if len(doc) == 11 and cpf_valido(doc):
        return doc
    if len(doc) == 14 and cnpj_valido(doc):
        return doc
    return None
