"""Levantamento da cobertura da Órbita (item 20 da rodada de testes).

Roda o `buscar.py --resumo` de cada base dos plugins orbita-fiscal e orbita-juridica, em paralelo,
e grava o texto bruto de cada resumo em scripts/cobertura/resumos.json. Depois, `montar.py` transforma
esses resumos em src/data/cobertura.json, que a página /bases lê no build.

Uso (as pastas dos plugins mudam de máquina para máquina):
    python scripts/cobertura/levantar.py <pasta do plugin> [<pasta do plugin> ...]
Cada pasta é a que contém `skills/` e `.claude-plugin/plugin.json`.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

SAIDA = Path(__file__).with_name("resumos.json")


def frontmatter(skill_md: Path) -> dict:
    texto = skill_md.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"---\n(.*?)\n---", texto, re.S)
    meta = {}
    if m:
        for linha in m.group(1).splitlines():
            if ":" in linha and not linha.startswith(" "):
                k, v = linha.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')
    titulo = re.search(r"^# (.+)$", texto, re.M)
    meta["titulo"] = titulo.group(1).strip() if titulo else meta.get("name", skill_md.parent.name)
    return meta


def rodar(skill: Path, args: list[str]) -> tuple[bool, str, str]:
    try:
        r = subprocess.run(
            [sys.executable, "-I", str(skill / "scripts" / "buscar.py"), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180, cwd=skill,
        )
        return r.returncode == 0 and bool(r.stdout.strip()), r.stdout.strip(), r.stderr.strip()[-500:]
    except subprocess.TimeoutExpired:
        return False, "", "tempo esgotado"


def resumo(skill: Path) -> dict:
    """Só comandos documentados das skills: `--resumo` quando a base tem; senão, uma consulta só de filtro
    (todos os anos), que devolve o total, e a mesma consulta pela ordem mais recente e mais antiga, para o período."""
    fonte = (skill / "scripts" / "buscar.py").read_text(encoding="utf-8", errors="replace")
    if '"--resumo"' in fonte:
        ok, texto, erro = rodar(skill, ["--resumo"])
        return {"modo": "resumo", "ok": ok, "texto": texto, "erro": erro}
    base = ["--ano", "1500-2100", "--max", "1", "--sem-anexo", "--sem-cauda"]
    ok1, recente, e1 = rodar(skill, [*base, "--ordem", "recente"])
    ok2, antiga, e2 = rodar(skill, [*base, "--ordem", "antiga"])
    return {"modo": "filtro", "ok": ok1, "texto": recente, "texto_antigo": antiga if ok2 else "", "erro": e1 or e2}


def main(pastas: list[str]) -> None:
    tarefas = []
    for pasta in map(Path, pastas):
        plugin = json.loads((pasta / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["name"]
        for skill in sorted((pasta / "skills").iterdir()):
            if (skill / "scripts" / "buscar.py").exists():
                tarefas.append((plugin, skill))
    # Cada resumo espera o servidor: muitas em paralelo, sem pesar no computador.
    with ThreadPoolExecutor(max_workers=24) as pool:
        resultados = list(pool.map(lambda t: resumo(t[1]), tarefas))
    bases = []
    for (plugin, skill), res in zip(tarefas, resultados):
        meta = frontmatter(skill / "SKILL.md")
        bases.append({"id": skill.name, "plugin": plugin, "titulo": meta["titulo"], "descricao": meta.get("description", ""), **res})
    SAIDA.write_text(json.dumps({"levantado_em": date.today().isoformat(), "bases": bases}, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = sum(b["ok"] for b in bases)
    print(f"{ok} de {len(bases)} bases responderam. Gravado em {SAIDA}")
    for b in bases:
        if not b["ok"]:
            print(f"  sem resposta: {b['plugin']}/{b['id']}: {b['erro'][:120]}")


if __name__ == "__main__":
    main(sys.argv[1:])
