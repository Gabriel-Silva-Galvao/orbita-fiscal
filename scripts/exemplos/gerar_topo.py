"""Gera src/data/topo.json: os exemplos que o topo da landing sorteia (item 13 da rodada de testes).

Fonte: o painel "Comparação por pergunta" (artefato da equipe, 16/11/2026), com o texto integral das respostas do
Claude Opus 5.5 com a Órbita. Para cada uma das 11 perguntas: a pergunta, o primeiro parágrafo da resposta (sem mudar
nada) e até 5 fontes citadas nesse trecho ou, se faltar, no resto da resposta, na ordem em que aparecem.

Uso: python scripts/exemplos/gerar_topo.py <arquivo .json do painel>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SAIDA = Path(__file__).resolve().parents[2] / "src" / "data" / "topo.json"

# Mesmo padrão das citações que acendem na geração ao vivo (src/scripts/gerar.ts), um pouco mais amplo.
CITACAO = re.compile(
    r"(Súmula(?: Vinculante| CARF)? (?:nº )?\d+(?:/STJ|/STF| do (?:STF|STJ))?"
    r"|Tema \d+(?:/STJ|/STF| do (?:STF|STJ))?"
    r"|(?:Lei(?: Complementar)?|LC|IN(?: RFB)?|Decreto|PN Cosit) (?:nº )?[\d.]+/\d{2,4}(?:, art\. \d+[ºo]?)?"
    r"|(?:ARE|RE|REsp|AgR|HC|RHC|ADI|AREsp|AgInt) [\d.]+(?: AgR)?"
    r"|(?:AI|Ap) \d\.\d{4}\.\d{2}\.\d{6}-\d/\d{3}"  # acórdãos do TJMG
    r"|arts?\. [\d.]+(?:, parágrafo único,)?(?: e [\d.]+)? do (?:Código Civil|CC|CTN|CPC))"
)


def chave(c: str) -> str:
    """Mesma fonte escrita de jeitos diferentes vira uma só: 'Súmula CARF nº 217' e 'Súmula 217', 'Lei 8.137/90' e
    'Lei 8.137/1990', 'Tema 1199' e 'Tema 1199 do STF'."""
    tipo = c.split()[0].lower().rstrip(".")
    numero = re.search(r"\d[\d.]*", c)
    return f"{tipo}:{numero.group(0).replace('.', '') if numero else c}"


def fontes(texto: str, trecho: str, maximo: int = 5) -> list[str]:
    vistas: list[str] = []
    chaves: set[str] = set()
    for parte in (trecho, texto):
        for m in CITACAO.finditer(parte):
            c = m.group(1).strip()
            if chave(c) not in chaves:
                chaves.add(chave(c))
                vistas.append(c)
            if len(vistas) >= maximo:
                return vistas
    return vistas


def main(origem: str) -> None:
    linhas = json.loads(Path(origem).read_text(encoding="utf-8"))["rows"]
    exemplos = []
    for r in sorted(linhas, key=lambda r: int(r["n"])):
        texto = r["resposta_com"].strip()
        trecho = texto.split("\n")[0].strip()
        exemplos.append({
            "n": int(r["n"]),
            "tribunal": r["tribunal"],
            "pergunta": r["pergunta"].strip(),
            "trecho": trecho,
            "fontes": fontes(texto, trecho),
            "fontes_total": int(r["ref_com"]),
        })
    SAIDA.write_text(json.dumps(exemplos, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(exemplos)} exemplos em {SAIDA}")
    for e in exemplos:
        print(f"  {e['n']:>2} {e['tribunal']:<16} {len(e['trecho'].split()):>3} palavras · {e['fontes']}")


if __name__ == "__main__":
    main(sys.argv[1])
