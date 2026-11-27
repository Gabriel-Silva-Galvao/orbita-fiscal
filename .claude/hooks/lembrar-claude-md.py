"""Hook PreToolUse (Bash): antes de um git commit, lembra de atualizar o CLAUDE.md se ele não vai junto.

Não bloqueia nada: só devolve um aviso ao Claude (additionalContext) e ao usuário (systemMessage).
"""
import json
import subprocess
import sys

try:
    entrada = json.load(sys.stdin)
except ValueError:
    sys.exit(0)

comando = (entrada.get("tool_input") or {}).get("command", "")
if "git commit" not in comando or "CLAUDE.md" in comando:
    sys.exit(0)

try:
    preparados = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, timeout=10
    ).stdout.split()
except (OSError, subprocess.SubprocessError):
    preparados = []
if "CLAUDE.md" in preparados:
    sys.exit(0)

aviso = (
    "O CLAUDE.md não está neste commit. Se o commit muda o estado do projeto, o próximo passo, uma regra, "
    "uma decisão, como rodar ou testar, ou cria documento ou artefato novo, atualize o CLAUDE.md "
    "(seção 7, 'Manter este arquivo') e inclua-o no commit."
)
print(json.dumps({
    "systemMessage": "Lembrete: conferir se o CLAUDE.md precisa ir neste commit.",
    "hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": aviso},
}))  # ensure_ascii padrão: os acentos saem como \u e não quebram no console do Windows
