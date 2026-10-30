import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- API Keys ---
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_FALLBACK_API_KEY = os.getenv("GROQ_FALLBACK_API_KEY")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_CLUSTER_ENDPOINT = os.getenv("QDRANT_CLUSTER_ENDPOINT")
    QDRANT_COLLECTION = "enterprise_rag"
    QDRANT_TIMEOUT = int(os.getenv("QDRANT_TIMEOUT", "30"))
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # --- Model Settings ---
    PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "openai/gpt-oss-120b")
    Fallback_MODEL = os.getenv("FALLBACK_MODEL", "openai/gpt-oss-20b")
    
    
settings = Settings()