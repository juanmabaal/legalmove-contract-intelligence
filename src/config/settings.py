import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / os.getenv("OUTPUT_DIR", "outputs")

#PROVIDERS
SUPPORTED_VISION_PROVIDERS = {"openai", "xai"}
SUPPORTED_LLM_PROVIDERS = {"openai", "xai", "deepseek"}

VISION_PROVIDER = os.getenv("VISION_PROVIDER", "openai").lower()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
LLM_FALLBACK_PROVIDER = os.getenv("LLM_FALLBACK_PROVIDER", "openai").lower()

#openai
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")
OPENAI_TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")

# XAI / GROK
XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_VISION_MODEL = os.getenv("XAI_VISION_MODEL", "grok-4.5")
XAI_TEXT_MODEL = os.getenv("XAI_TEXT_MODEL", "grok-4.5")
XAI_BASE_URL = "https://api.x.ai/v1"

# DEEPSEEK
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_TEXT_MODEL = os.getenv("DEEPSEEK_TEXT_MODEL", "deepseek-chat")

# LANGFUSE
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

# APPLICATION
APP_ENV = os.getenv("APP_ENV", "development")

def validate_vision_provider(provider: str) ->str:
    normalized_provider = provider.lower()

    if normalized_provider not in SUPPORTED_VISION_PROVIDERS:
        raise ValueError(
            f"Unsupported vision provider: {provider}. "
            f"Supported providers are: {sorted(SUPPORTED_VISION_PROVIDERS)}"
        )
    
    return normalized_provider

def validate_llm_provider(provider: str) -> str:
    normalized_provider = provider.lower()

    if normalized_provider not in SUPPORTED_LLM_PROVIDERS:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers are: {sorted(SUPPORTED_LLM_PROVIDERS)}"
        )

    return normalized_provider