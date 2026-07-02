from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvConfig(BaseSettings):
    # TODO: Extend this as more providers come into play
    model_config = SettingsConfigDict(
        env_prefix="ORCHFLOW_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    visible_turns: bool = True


@lru_cache
def get_settings() -> EnvConfig:
    return EnvConfig()
