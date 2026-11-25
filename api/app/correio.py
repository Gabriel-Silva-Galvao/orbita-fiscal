"""Envio do código de verificação (2FA) por e-mail.

Com SMTP_HOST definido no api/.env, o código vai por SMTP (STARTTLS na porta 587 ou SSL na 465),
em texto e HTML. Sem SMTP_HOST, vai para o log da API: serve para desenvolvimento, junto com
AUTH_CODIGO_NA_RESPOSTA=true, que mostra o código na tela. Usuário e senha do SMTP ficam só no .env.
"""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.config import get_settings

log = logging.getLogger("orbita.email")

ASSUNTO = "Seu código da Órbita: {codigo}"
TEXTO = """Olá,

Seu código de verificação da Órbita é {codigo}.
Ele vale por 10 minutos. Se não foi você que pediu, ignore este e-mail: sem o código, ninguém entra na sua conta.

Equipe Órbita
"""
HTML = """<div style="font-family:Arial,sans-serif;color:#102f31;max-width:480px">
<p>Olá,</p>
<p>Seu código de verificação da Órbita é:</p>
<p style="font-size:32px;letter-spacing:8px;font-weight:bold;color:#10634f;margin:16px 0">{codigo}</p>
<p>Ele vale por 10 minutos. Se não foi você que pediu, ignore este e-mail: sem o código, ninguém entra na sua conta.</p>
<p>Equipe Órbita</p>
</div>"""


def montar(destino: str, codigo: str) -> EmailMessage:
    s = get_settings()
    m = EmailMessage()
    m["Subject"] = ASSUNTO.format(codigo=codigo)
    m["From"] = s.smtp_from
    m["To"] = destino
    m.set_content(TEXTO.format(codigo=codigo))
    m.add_alternative(HTML.format(codigo=codigo), subtype="html")
    return m


def enviar_codigo(destino: str, codigo: str) -> None:
    s = get_settings()
    if not s.smtp_host:
        log.warning("Código de verificação para %s: %s (SMTP_HOST vazio: e-mail não enviado)", destino, codigo)
        return
    msg = montar(destino, codigo)
    ctx = ssl.create_default_context()
    try:
        if s.smtp_ssl:
            with smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, context=ctx, timeout=15) as c:
                if s.smtp_user:
                    c.login(s.smtp_user, s.smtp_password)
                c.send_message(msg)
        else:
            with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=15) as c:
                c.starttls(context=ctx)
                if s.smtp_user:
                    c.login(s.smtp_user, s.smtp_password)
                c.send_message(msg)
    except (smtplib.SMTPException, OSError):
        # Não derruba o login: a pessoa pode pedir o reenvio. O erro fica no log, sem o código.
        log.exception("Falha ao enviar o código para %s pelo SMTP", destino)
