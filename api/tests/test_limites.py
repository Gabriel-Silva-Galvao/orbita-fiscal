"""Segurança (26/11/2026): a API travou com um e-mail montado para o regex antigo voltar atrás (ReDoS).
Estes testes garantem que o regex é linear, que texto grande é recusado antes de ser processado e que
o corpo do pedido tem limite."""
from __future__ import annotations

import time

from app.auth import EMAIL_RE


def test_regex_de_email_nao_volta_atras():
    for ataque in ("a@" + "." * 200_000 + " ", "a@" + "a." * 100_000 + " ", "a" * 200_000 + "@"):
        t = time.perf_counter()
        assert EMAIL_RE.match(ataque) is None
        assert time.perf_counter() - t < 0.05


def test_regex_aceita_e_recusa_o_que_deve():
    for ok in ("ana@exemplo.com", "a.b+c@sub.dominio.com.br", "x@y.io"):
        assert EMAIL_RE.match(ok), ok
    for ruim in ("ana@exemplo", "ana@@exemplo.com", "ana @exemplo.com", "ana@.com", "ana@exemplo..com", "@exemplo.com"):
        assert not EMAIL_RE.match(ruim), ruim


def test_email_gigante_volta_422_sem_travar(api):
    http, *_ = api
    t = time.perf_counter()
    r = http.post("/auth/cadastro", json={"nome": "Ana", "email": "a@" + "." * 50_000, "senha": "senha-forte-1"})
    assert r.status_code == 422 and time.perf_counter() - t < 1
    assert http.post("/auth/email/trocar", json={"email": "a" * 300}).status_code in (401, 422)


def test_corpo_acima_de_64kb_volta_413(api):
    http, *_ = api
    r = http.post("/auth/login", content=b'{"email":"' + b"a" * 70_000 + b'"}', headers={"content-type": "application/json"})
    assert r.status_code == 413
    assert http.post("/auth/login", json={"email": "ana@exemplo.com", "senha": "x"}).status_code in (401, 404, 422)
