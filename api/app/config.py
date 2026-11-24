"""Configuração da API da Órbita, lida do ambiente ou de api/.env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Asaas: hoje a simulação local; depois, o sandbox ou a produção do Asaas.
    asaas_base_url: str = "http://localhost:8000/asaas-sim/v3"
    asaas_api_key: str = "$aact_hmlg_simulacao_orbita"
    asaas_sim_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
