from langchain_openai import OpenAIEmbeddings
from src.config import get_settings


def get_embeddings() -> OpenAIEmbeddings:
    s = get_settings()
    return OpenAIEmbeddings(
        model=s.embedding_model,
        openai_api_key=s.siliconflow_api_key,
        openai_api_base=s.siliconflow_base_url,
    )