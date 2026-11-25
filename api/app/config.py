"""Configuração da API da Órbita, lida do ambiente ou de api/.env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Asaas: hoje a simulação local; depois, o sandbox ou a produção do Asaas.
    asaas_base_url: str = "http://127.0.0.1:8000/asaas-sim/v3"
    asaas_api_key: str = "$aact_hmlg_simulacao_orbita"
    asaas_sim_enabled: bool = True
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
