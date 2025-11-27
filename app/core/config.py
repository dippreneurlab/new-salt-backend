import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.production", ".env"),
        case_sensitive=False,
        extra="allow",
    )

    port: int = int(os.getenv("PORT", 5000))
    api_prefix: str = "/api"

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

        user = self.postgres_user or ""
        password = self.postgres_password or ""
        
        # Cloud SQL with Unix socket (Cloud Run)
        if self.cloud_sql_connection_name:
            # Format for Unix socket: postgresql://user:password@/database?host=/cloudsql/connection_name
            host_path = f"/cloudsql/{self.cloud_sql_connection_name}"
            return f"postgresql://{user}:{password}@/{self.postgres_db}?host={host_path}"
        
        # TCP connection (local or external)
        else:
            host = self.postgres_host or "127.0.0.1"
            port = self.postgres_port or 5432
            return f"postgresql://{user}:{password}@{host}:{port}/{self.postgres_db}"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources to parse CORS origins from comma-separated string."""
        
        class CustomEnvSettings(PydanticBaseSettingsSource):
            def get_field_value(self, field, field_name):
                value = env_settings.get_field_value(field, field_name)
                
                # Parse cors_origins if it's a comma-separated string
                if field_name == "cors_origins" and isinstance(value[0] if value else None, str):
                    return ([v.strip() for v in value[0].split(",") if v.strip()], field_name, False)
                
                return value
            
            def __call__(self):
                return env_settings()
        
        return (
            init_settings,
            CustomEnvSettings(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )


settings = Settings()