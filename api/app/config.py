"""Configuração da API da Órbita, lida do ambiente ou de api/.env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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


# Valores de exemplo que estão no repositório: em produção, nenhum deles pode ser usado.
TOKEN_WEBHOOK_EXEMPLO = "orbita-simulacao-token-do-webhook-0001"
CHAVE_SIMULACAO = "$aact_hmlg_simulacao_orbita"


def problemas_de_producao(s: "Settings") -> list[str]:
    """Configurações perigosas (docs/backend-e-seguranca.md, S1, S2 e S4). Lista vazia = pode subir.

    - Simulação ligada com COOKIE_SECURE=true (sinal de produção): daria acesso sem pagar.
    - Sem a simulação (Asaas de verdade): exige token do webhook e chave próprios, e o código do 2FA fora da resposta.
    """
    erros = []
    if s.asaas_sim_enabled and s.cookie_secure:
        erros.append("ASAAS_SIM_ENABLED=true com COOKIE_SECURE=true: a simulação do Asaas não pode rodar em produção.")
    if not s.asaas_sim_enabled:
        if s.asaas_webhook_token == TOKEN_WEBHOOK_EXEMPLO or len(s.asaas_webhook_token) < 32:
            erros.append("ASAAS_WEBHOOK_TOKEN é o de exemplo (ou tem menos de 32 caracteres): gere um segredo próprio.")
        if s.asaas_api_key == CHAVE_SIMULACAO:
            erros.append("ASAAS_API_KEY é a chave da simulação: use a chave do Asaas (sandbox ou produção).")
        if s.auth_codigo_na_resposta:
            erros.append("AUTH_CODIGO_NA_RESPOSTA=true fora da simulação: o código do 2FA não pode ir na resposta.")
    return erros


@lru_cache
def get_settings() -> Settings:
    return Settings()
