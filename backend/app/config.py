import os
from functools import lru_cache
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    amap_api_key: str = os.getenv("AMAP_API_KEY", "")
    unsplash_access_key: str = os.getenv("UNSPLASH_ACCESS_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model_name: str = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")

@lru_cache()
def get_settings():
    return Settings()
