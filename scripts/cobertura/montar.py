"""Transforma scripts/cobertura/resumos.json em src/data/cobertura.json (item 20 da rodada de testes).

Para cada base: total de documentos, período (data mais antiga e mais recente), última carga quando a base
informa, tipo (para os filtros da página /bases) e UF (para o mapa). Bases que aparecem nos dois plugins
(STF, STJ, Planalto) entram uma vez só. Base sem número legível fica com `total: null` ("a confirmar").

Uso: python scripts/cobertura/montar.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = Path(__file__).with_name("resumos.json")
SAIDA = RAIZ / "src" / "data" / "cobertura.json"

UFS = {
    "ac": "AC", "al": "AL", "ap": "AP", "am": "AM", "ba": "BA", "ce": "CE", "df": "DF", "dft": "DF", "es": "ES",
    "go": "GO", "ma": "MA", "mt": "MT", "ms": "MS", "mg": "MG", "pa": "PA", "pb": "PB", "pr": "PR", "pe": "PE",
    "pi": "PI", "rj": "RJ", "rn": "RN", "rs": "RS", "ro": "RO", "rr": "RR", "sc": "SC", "sp": "SP", "se": "SE",
    "to": "TO",
}
ESTADOS = {
    "acre": "AC", "alagoas": "AL", "amapa": "AP", "amazonas": "AM", "bahia": "BA", "ceara": "CE",
    "maranhao": "MA", "mineira": "MG", "para": "PA", "paraiba": "PB", "pernambuco": "PE", "piaui": "PI",
    "rio-grande-do-norte": "RN", "rondonia": "RO", "roraima": "RR", "sergipe": "SE", "tocantins": "TO",
}
# Siglas avulsas no nome da base: ccmg, consef-ba, tit-sp, conat-ce...
SIGLA_UF = {"ccmg": "MG", "tit-sp": "SP", "cojup-rn": "RN", "jupaf-ap": "AP", "conat-ce": "CE"}

TIPOS = [
    ("superiores", "Tribunais superiores"),
    ("federal", "Justiça Federal"),
    ("estadual", "Justiça estadual"),
    ("adm-federal", "Contencioso administrativo federal"),
    ("adm-estadual", "Contencioso administrativo estadual"),
    ("consultas", "Consultas e pareceres"),
    ("legislacao", "Legislação e normas"),
    ("contas", "Controle externo"),
    ("liminares", "Liminares"),
]


def tipo(i: str) -> str:
    if i in ("jurisprudencia-stf", "jurisprudencia-stj"):
        return "superiores"
    if i.startswith("jurisprudencia-trf"):
        return "federal"
    if i.startswith("jurisprudencia-tj"):
        return "estadual"
    if i == "jurisprudencia-carf":
        return "adm-federal"
    if i.startswith(("acordaos-", "decisoes-", "resolucoes-conat", "jurisprudencia-tit")):
        return "adm-estadual"
    if i.startswith(("consultas-", "pareceres-", "solucoes-", "respostas-", "resolucoes-consulta")):
        return "consultas"
    if i.startswith(("legislacao-", "normas-")):
        return "legislacao"
    if "tcu" in i or "tce" in i:
        return "contas"
    if i.startswith("liminares"):
        return "liminares"
    return "outros"


def uf(i: str) -> str | None:
    for sig, u in SIGLA_UF.items():
        if sig in i:
            return u
    if i.startswith("legislacao-tributaria-"):
        return ESTADOS.get(i.removeprefix("legislacao-tributaria-"))
    if "tce-mg" in i or i.startswith("jurisprudencia-tjmg"):
        return "MG"
    if i in ("jurisprudencia-tjdft",):
        return "DF"
    m = re.match(r"jurisprudencia-tj([a-z]{2})", i)
    if m:
        return UFS.get(m.group(1))
    m = re.search(r"-([a-z]{2})$", i)
    if m and i.split("-")[0] in ("acordaos", "consultas", "decisoes", "pareceres", "solucoes", "respostas", "resolucoes"):
        return UFS.get(m.group(1))
    return None


DATA = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b|\b(\d{4})-(\d{2})-(\d{2})\b")


def primeira_data(texto: str) -> str | None:
    """Primeira data do primeiro resultado (pula a linha do total)."""
    corpo = texto.split("\n", 1)[1] if "\n" in texto else ""
    for m in DATA.finditer(corpo):
        d = f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m.group(1) else f"{m.group(4)}-{m.group(5)}-{m.group(6)}"
        if d != "1899-12-30":  # data vazia vinda de planilha: não é data real
            return d
    return None


def fonte(b: dict) -> str | None:
    """Descrição curta da base, como o próprio servidor a apresenta (primeira linha do resumo)."""
    linha = b["texto"].splitlines()[0] if b["texto"] else ""
    if b.get("modo") == "resumo":
        return linha or None
    m = re.match(r"\d+ resultado\(s\) em (.+?)(?:; mostrando.*)?$", linha)
    if not m:
        return None
    nome = m.group(1).strip()
    sigla = re.fullmatch(r"(\w+)/acordaos", nome)  # "STJ/acordaos" -> "Acórdãos do STJ"
    return f"Acórdãos do {sigla.group(1)}" if sigla else nome


def ler(b: dict) -> dict:
    t = b["texto"]
    out = {"total": None, "inicio": None, "fim": None, "ultima_carga": None, "unidade": "documentos", "fonte": fonte(b)}
    if b.get("modo") == "resumo":
        linha = t.splitlines()[1] if len(t.splitlines()) > 1 else ""
        m = re.match(r"(\d+) (\S+)", linha)
        if m:
            out["total"], out["unidade"] = int(m.group(1)), m.group(2)
        p = re.search(r"\((\d{2})/(\d{2})/(\d{4}) a (\d{2})/(\d{2})/(\d{4})\)", linha)
        if p:
            out["inicio"] = f"{p.group(3)}-{p.group(2)}-{p.group(1)}"
            out["fim"] = f"{p.group(6)}-{p.group(5)}-{p.group(4)}"
        else:
            a = re.search(r"\((\d{4})\D(\d{4})\)", linha)
            if a:
                out["inicio"], out["fim"] = a.group(1), a.group(2)
        c = re.search(r"última carga (\d{4}-\d{2}-\d{2})", linha)
        if c:
            out["ultima_carga"] = c.group(1)
        return out
    m = re.match(r"(\d+) (resultado\(s\)|acórdãos)", t)
    if m and int(m.group(1)) > 0:
        out["total"] = int(m.group(1))
        out["fim"] = primeira_data(t)
        out["inicio"] = primeira_data(b.get("texto_antigo", ""))
    return out


def main() -> None:
    dados = json.loads(ENTRADA.read_text(encoding="utf-8"))
    vistos, bases = set(), []
    for b in dados["bases"]:
        if b["id"] in vistos:
            continue
        vistos.add(b["id"])
        info = ler(b)
        bases.append({
            "id": b["id"], "plugin": b["plugin"], "titulo": b["titulo"], "tipo": tipo(b["id"]), "uf": uf(b["id"]),
            **info,
        })
    total = sum(b["total"] or 0 for b in bases)
    saida = {
        "levantado_em": dados["levantado_em"],
        "total_documentos": total,
        "total_bases": len(bases),
        "a_confirmar": [b["id"] for b in bases if b["total"] is None],
        "tipos": [{"id": i, "nome": n} for i, n in TIPOS],
        "bases": sorted(bases, key=lambda b: -(b["total"] or 0)),
    }
    SAIDA.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(bases)} bases, {total:,} documentos. A confirmar: {saida['a_confirmar']}".replace(",", "."))
    for b in bases:
        if b["tipo"] == "outros":
            print("  revisar tipo:", b["id"])


if __name__ == "__main__":
    main()
