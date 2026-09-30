"""Central, validated configuration. Fails closed in production; never prints secret values."""
from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PLACEHOLDERS = {"", "changeme", "change-me", "secret", "password", "your-secret-here"}
_MIN_SECRET_LEN = 32


class Environment(str, Enum):
    development = "development"
    test = "test"
    production = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", case_sensitive=True,
        hide_input_in_errors=True,  # validation errors must never echo secret inputs
    )

    ENVIRONMENT: Environment = Environment.development
    DEBUG: bool = False
    DATABASE_URL: SecretStr = SecretStr("")
    SECRET_KEY: SecretStr = SecretStr("")
    MODEL_SIGNING_KEY: SecretStr = SecretStr("")
    # Kept as a plain string (comma-separated) to avoid JSON-parsing surprises.
    CORS_ORIGINS: str = ""

    SESSION_IDLE_MINUTES: int = 30
    SESSION_ABSOLUTE_HOURS: int = 8
    RATE_LIMIT_LOGIN_PER_MIN: int = 5
    RATE_LIMIT_UPLOAD_PER_HOUR: int = 10
    RATE_LIMIT_TRAIN_PER_HOUR: int = 10
    RATE_LIMIT_PREDICT_PER_MIN: int = 60
    MAX_UPLOAD_MB: int = 10
    MAX_UPLOAD_ROWS: int = 50_000
    ARTIFACT_DIR: str = "./artifacts"

    @field_validator(
        "SESSION_IDLE_MINUTES", "SESSION_ABSOLUTE_HOURS", "RATE_LIMIT_LOGIN_PER_MIN",
        "RATE_LIMIT_UPLOAD_PER_HOUR", "RATE_LIMIT_TRAIN_PER_HOUR",
        "RATE_LIMIT_PREDICT_PER_MIN", "MAX_UPLOAD_MB", "MAX_UPLOAD_ROWS",
    )
    @classmethod
    def _positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("must be a positive integer")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT is Environment.production

    @model_validator(mode="after")
    def _validate_security(self) -> Settings:
        problems: list[str] = []  # names only; values are never included

        for origin in self.cors_origin_list:
            if origin == "*":
                problems.append("CORS_ORIGINS must not contain '*'")
            elif not origin.startswith(("http://", "https://")):
                problems.append("CORS_ORIGINS entries must start with http:// or https://")

        if self.ENVIRONMENT is not Environment.test and not self.DATABASE_URL.get_secret_value():
            problems.append("DATABASE_URL is required")

        if self.is_production:
            if self.DEBUG:
                problems.append("DEBUG must be false in production")
            if not self.cors_origin_list:
                problems.append("CORS_ORIGINS is required in production")
            if any(not o.startswith("https://") for o in self.cors_origin_list):
                problems.append("production CORS_ORIGINS must be https://")
            for name in ("SECRET_KEY", "MODEL_SIGNING_KEY"):
                val = getattr(self, name).get_secret_value()
                if val.lower() in _PLACEHOLDERS or len(val) < _MIN_SECRET_LEN:
                    problems.append(f"{name} must be a strong secret (>= {_MIN_SECRET_LEN} chars)")
            if (self.SECRET_KEY.get_secret_value() == self.MODEL_SIGNING_KEY.get_secret_value()):
                problems.append("SECRET_KEY and MODEL_SIGNING_KEY must differ")
        if problems:
            raise ValueError("Invalid configuration: " + "; ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
