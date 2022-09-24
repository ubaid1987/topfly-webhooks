from pydantic import BaseSettings


class Settings(BaseSettings):
    TOKEN: str
    SENTRY_DNS: str = None

    class Config:
        env_file = ".env"
