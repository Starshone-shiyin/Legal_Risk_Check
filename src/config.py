from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM
    llm_api_key: str
    llm_provider: str = "openai_compatible"
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    vision_llm_enabled: bool = True
    vision_llm_api_key: str | None = None
    vision_llm_base_url: str | None = None
    vision_llm_model: str = "deepseek-v4-flash-vision-exp"

    # Embedding（硅基流动）
    siliconflow_api_key: str
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"
    embedding_model: str = "BAAI/bge-m3"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "legal_knowledge"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
