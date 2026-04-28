APP_VERSION = "5.0.0"

from app.core.logger import log
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:10000/auth/callback"
    token_storage_path: str = "./tokens.json"
    mcp_server_url: str = "http://localhost:10000"

    google_scopes: list[str] = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/presentations",
        "https://www.googleapis.com/auth/classroom.courses.readonly",
        "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
        "https://www.googleapis.com/auth/classroom.student-submissions.me.readonly",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def validate_startup(self) -> None:
        missing = [
            k for k, v in {
                "GOOGLE_CLIENT_ID": self.google_client_id,
                "GOOGLE_CLIENT_SECRET": self.google_client_secret,
            }.items()
            if not v
        ]
        if missing:
            log.warning(
                "google_oauth_not_configured missing=%s — visit /auth/login or use Claude custom connector to authenticate",
                missing,
            )


settings = Settings()
