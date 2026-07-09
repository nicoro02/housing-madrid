"""Configuración centralizada leída de variables de entorno y .env."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # Databases
    mongo_uri: str = "mongodb://admin:admin@localhost:27017"
    postgres_uri: str = "postgresql://housing:housing@localhost:5432/housing"

    # MLflow
    mlflow_tracking_uri: str = "http://localhost:5001"

    # Scraper
    scrape_min_delay_sec: float = 2.5
    scrape_max_delay_sec: float = 5.5
    scrape_user_agent: str = Field(
        default="Mozilla/5.0 (educational-portfolio; contact nicoro02@ucm.es)"
    )

    # GCP
    gcp_project: str = ""
    gcp_region: str = "europe-southwest1"


settings = Settings()
