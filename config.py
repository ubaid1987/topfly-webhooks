from pydantic import BaseSettings


class Settings(BaseSettings):
    TOKEN: str
    SENTRY_DNS: str

    class Config:
        env_file = ".env"
