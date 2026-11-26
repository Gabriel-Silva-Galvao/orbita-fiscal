"""Configuração da API da Órbita, lida do ambiente ou de api/.env."""
from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ARES-SEC-006: onde a API roda. O padrão é produção (o lado seguro); o desenvolvimento declara
    # ORBITA_ENV=development (.claude/launch.json, api/.env.example e os testes). Antes, "produção" era deduzida do
    # COOKIE_SECURE, e bastava COOKIE_SECURE=false para a simulação (acesso sem pagar) subir num servidor público.
    orbita_env: Literal["development", "production"] = "production"
    # Asaas: hoje a simulação local; depois, o sandbox ou a produção do Asaas.
    asaas_base_url: str = "http://127.0.0.1:8000/asaas-sim/v3"
    asaas_api_key: str = "$aact_hmlg_simulacao_orbita"
    # Item 17 (S1): desligada por padrão. Ligue só no desenvolvimento (ASAAS_SIM_ENABLED=true).
    asaas_sim_enabled: bool = False
    # Token que o Asaas manda no cabeçalho asaas-access-token de cada webhook (32 a 255 caracteres).
    asaas_webhook_token: str = "orbita-simulacao-token-do-webhook-0001"
    # Endereço público desta API, usado para cadastrar o webhook (/webhooks/asaas).
    api_public_url: str = "http://127.0.0.1:8000"
    # Banco SQLite com assinantes, assinaturas e eventos recebidos.
    database_path: str = "orbita.db"
    # Conta e login (etapa 7a).
    # Endereço do site, liberado no CORS com cookies (o site chama a API do navegador).
    site_url: str = "http://localhost:4321"
    # Cookies só por HTTPS. Ligue em produção.
    cookie_secure: bool = False
    # Só em desenvolvimento: devolve o código de 6 dígitos na resposta (não há provedor de e-mail ainda).
    auth_codigo_na_resposta: bool = False
    # Envio do código (2FA) por e-mail. Sem smtp_host, o código vai para o log da API.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_ssl: bool = False  # true para a porta 465 (SSL direto); false usa STARTTLS
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "Órbita <nao-responda@orbitafiscal.com.br>"
    # Item 26: para onde vão as mensagens de planos empresariais (e-mail da Órbita, a confirmar).
    contato_email: str = "contato@orbitafiscal.com.br"
    # Item 40: segredo que o servidor MCP da Órbita manda no cabeçalho X-Orbita-Servidor ao avisar que o plugin
    # de um assinante fez uma pergunta (POST /plugin/uso). Vazio = rota desligada. Mínimo de 32 caracteres.
    plugin_servidor_token: str = ""


# Valores de exemplo que estão no repositório: em produção, nenhum deles pode ser usado.
TOKEN_WEBHOOK_EXEMPLO = "orbita-simulacao-token-do-webhook-0001"
CHAVE_SIMULACAO = "$aact_hmlg_simulacao_orbita"


def _local(url: str) -> bool:
    return (urlsplit(url).hostname or "") in ("localhost", "127.0.0.1", "::1")


def problemas_de_producao(s: "Settings") -> list[str]:
    """Configurações perigosas (docs/backend-e-seguranca.md, S1, S2 e S4; ARES-SEC-006). Lista vazia = pode subir.

    - Em produção (ORBITA_ENV=production, o padrão): simulação proibida e COOKIE_SECURE obrigatório.
    - Em qualquer ambiente: a simulação só roda com o site e a API em localhost (nunca num endereço público).
    - Sem a simulação (Asaas de verdade): exige token do webhook e chave próprios, e o código do 2FA fora da resposta.
    """
    erros = []
    if s.orbita_env == "production":
        if s.asaas_sim_enabled:
            erros.append("ASAAS_SIM_ENABLED=true em produção (ORBITA_ENV=production): a simulação daria acesso sem pagar.")
        if not s.cookie_secure:
            erros.append("COOKIE_SECURE=false em produção (ORBITA_ENV=production): o cookie da sessão precisa de HTTPS.")
        if not s.smtp_host:
            # ARES-QA-007 (S4): sem SMTP, o código do 2FA vai para o log da API, onde quem lê o log entra na conta.
            erros.append("SMTP_HOST vazio em produção (ORBITA_ENV=production): o código do 2FA iria para o log em vez do e-mail.")
    if s.asaas_sim_enabled and s.cookie_secure:
        erros.append("ASAAS_SIM_ENABLED=true com COOKIE_SECURE=true: a simulação do Asaas não pode rodar em produção.")
    if s.asaas_sim_enabled and not (_local(s.site_url) and _local(s.api_public_url)):
        erros.append("ASAAS_SIM_ENABLED=true com SITE_URL ou API_PUBLIC_URL fora de localhost: a simulação é só para a máquina local.")
    if not s.asaas_sim_enabled:
        if s.asaas_webhook_token == TOKEN_WEBHOOK_EXEMPLO or len(s.asaas_webhook_token) < 32:
            erros.append("ASAAS_WEBHOOK_TOKEN é o de exemplo (ou tem menos de 32 caracteres): gere um segredo próprio.")
        if s.asaas_api_key == CHAVE_SIMULACAO:
            erros.append("ASAAS_API_KEY é a chave da simulação: use a chave do Asaas (sandbox ou produção).")
        if s.plugin_servidor_token and len(s.plugin_servidor_token) < 32:
            erros.append("PLUGIN_SERVIDOR_TOKEN tem menos de 32 caracteres: gere um segredo maior.")
        if s.auth_codigo_na_resposta:
            erros.append("AUTH_CODIGO_NA_RESPOSTA=true fora da simulação: o código do 2FA não pode ir na resposta.")
    return erros


@lru_cache
def get_settings() -> Settings:
    return Settings()
