from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="allow")

    api_prefix: str = "/api"
    port: int = 5010

    # Database
    database_url: Optional[str] = None
    postgres_host: Optional[str] = None
    postgres_port: Optional[int] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_db: Optional[str] = None
    postgres_ssl: Optional[bool] = True
    cloud_sql_connection_name: Optional[str] = None

    # Firebase
    fb_project_id: Optional[str] = None
    fb_client_email: Optional[str] = None
    fb_private_key: Optional[str] = None

    # CORS
    cors_origins: List[str] = ["*"]

    def build_db_url(self) -> Optional[str]:
        if self.database_url:
            return self.database_url

        if not self.postgres_db:
            return None

        host = self.cloud_sql_connection_name
        if host:
            host = f"/cloudsql/{host}"
        else:
            host = self.postgres_host or "127.0.0.1"

        port = self.postgres_port or 5432
        user = self.postgres_user or ""
        password = self.postgres_password or ""
        return f"postgresql://{user}:{password}@{host}:{port}/{self.postgres_db}"

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
        def parse_env_settings(settings: BaseSettings):
            data = env_settings(settings)
            cors_val = data.get("cors_origins")
            if isinstance(cors_val, str):
                data["cors_origins"] = [v.strip() for v in cors_val.split(",") if v.strip()]
            return data

        return (
            init_settings,
            parse_env_settings,
            dotenv_settings,
            file_secret_settings,
        )


settings = Settings()
