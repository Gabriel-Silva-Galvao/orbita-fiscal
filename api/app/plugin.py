"""Download do plugin (item 6 da rodada de testes, 25/11/2026).

O plugin real ainda não existe: depende do servidor MCP e do formato aceito pela loja do Claude
(docs/planejamento.md). Até lá, a API entrega um zip de DEMONSTRAÇÃO com o mesmo fluxo que o real vai ter:

  POST /plugin/link            (sessão + assinatura com acesso) -> 201 {url, expira_em, arquivo}
                                                                  | 401 sem sessão | 403 sem_acesso
  GET  /plugin/baixar/{token}  -> 200 application/zip (attachment) | 404 link desconhecido | 410 link expirado

O link vale 15 minutos e pode ser usado mais de uma vez nesse prazo (um download interrompido pode ser
retomado). O token é aleatório e guardado só como SHA-256. Quando o plugin real existir, troque `montar_zip`
pelo arquivo publicado; o resto do fluxo continua igual.
"""
from __future__ import annotations

import hashlib
import io
import json
import secrets
import time
import zipfile
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response

from app.auth import usuario_logado
from app.billing import tem_acesso
from app.config import get_settings

VALIDADE = 15 * 60
VERSAO = "0.0.0-demo"
ARQUIVO = f"orbita-plugin-{VERSAO}.zip"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS downloads (
    token_hash  TEXT PRIMARY KEY,
    usuario_id  TEXT NOT NULL,
    expira      REAL NOT NULL,
    criado      REAL NOT NULL
);
"""

README = """# Órbita: plugin de demonstração

Este arquivo é uma DEMONSTRAÇÃO. Ele não instala nada no Claude e não consulta nenhuma base.

O plugin real da Órbita liga o Claude à base de legislação e jurisprudência brasileira, pelo servidor MCP
da Órbita. Ele será publicado quando o servidor estiver no ar; a página Instalar avisa quando a versão
real estiver disponível.

Conteúdo deste pacote:
- .claude-plugin/plugin.json: exemplo do manifesto que o plugin real terá;
- skills/orbita-pesquisa/SKILL.md: exemplo de como a skill de pesquisa será descrita.

Dúvidas: https://orbitafiscal.com.br/ajuda
"""

MANIFESTO = {
    "name": "orbita",
    "displayName": "Órbita",
    "version": VERSAO,
    "description": "DEMONSTRAÇÃO. Pesquisa de legislação e jurisprudência brasileira, com a fonte, no Claude.",
    "author": {"name": "Órbita"},
}

SKILL = """---
name: orbita-pesquisa
description: DEMONSTRAÇÃO do formato. No plugin real, pesquisa leis, súmulas e julgados na base da Órbita.
---

# Pesquisa na base da Órbita (demonstração)

Este é um exemplo do formato. A versão real chama o servidor MCP da Órbita e devolve cada resposta com a
norma, a súmula ou o julgado de onde saiu.
"""


def _sha(v: str) -> str:
    return hashlib.sha256(v.encode()).hexdigest()


def montar_zip() -> bytes:
    """Zip de demonstração, montado na memória (não grava nada em disco)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("orbita/README.md", README)
        z.writestr("orbita/.claude-plugin/plugin.json", json.dumps(MANIFESTO, ensure_ascii=False, indent=2))
        z.writestr("orbita/skills/orbita-pesquisa/SKILL.md", SKILL)
    return buf.getvalue()


def criar_router() -> APIRouter:
    r = APIRouter(prefix="/plugin", tags=["Plugin"])

    @r.post("/link", status_code=201)
    def gerar_link(req: Request, u: dict = Depends(usuario_logado)):
        banco = req.app.state.banco
        a = banco.um("SELECT * FROM assinaturas WHERE usuario_id = ?", u["id"])
        if not a or not tem_acesso(a):
            return JSONResponse(
                {"codigo": "sem_acesso", "descricao": "O download fica disponível com a assinatura ativa."}, status_code=403
            )
        token, agora = secrets.token_urlsafe(32), time.time()
        banco.executar("DELETE FROM downloads WHERE expira < ?", agora)  # limpa links vencidos
        banco.executar("INSERT INTO downloads VALUES (?,?,?,?)", _sha(token), u["id"], agora + VALIDADE, agora)
        expira = datetime.fromtimestamp(agora + VALIDADE, tz=timezone.utc).isoformat()
        return {"url": f"{get_settings().api_public_url}/plugin/baixar/{token}", "expira_em": expira, "arquivo": ARQUIVO, "demonstracao": True}

    @r.get("/baixar/{token}")
    def baixar(token: str, req: Request):
        d = req.app.state.banco.um("SELECT expira FROM downloads WHERE token_hash = ?", _sha(token))
        if not d:
            return JSONResponse({"codigo": "link_invalido", "descricao": "Link de download desconhecido."}, status_code=404)
        if d["expira"] < time.time():
            return JSONResponse({"codigo": "link_expirado", "descricao": "O link expirou. Gere outro na página Instalar."}, status_code=410)
        return Response(
            montar_zip(),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{ARQUIVO}"', "Cache-Control": "no-store"},
        )

    return r
