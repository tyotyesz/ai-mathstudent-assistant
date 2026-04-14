from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 60
    artificial_latency_ms: int = 0
    hf_token: str = ""
    qwen_model_id: str = "Qwen/Qwen2.5-Math-1.5B-Instruct"
    qwen_max_new_tokens: int = 64
    qwen_temperature: float = 0.2

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = ""
        case_sensitive = False


def get_settings() -> Settings:
    return Settings()
