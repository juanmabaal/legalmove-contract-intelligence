from src.config.settings import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_TEXT_MODEL,
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_TEXT_MODEL,
    XAI_API_KEY,
    XAI_TEXT_MODEL,
    validate_llm_provider,
)

class LLMProviderError(RuntimeError):
    """Raised when a text LLM provider cannot be initialized."""


def get_chat_model(
        provider: str | None = None,
        temperature: float = 0,
):
    selected_provider = validate_llm_provider(provider or LLM_PROVIDER)

    if selected_provider == "openai":
        if not OPENAI_API_KEY:
            raise LLMProviderError(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai."
            )

        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=OPENAI_TEXT_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=temperature,
        )

    if selected_provider == "xai":
        if not XAI_API_KEY:
            raise LLMProviderError(
                "XAI_API_KEY is required when LLM_PROVIDER=xai."
            )

        from langchain_xai import ChatXAI

        return ChatXAI(
            model=XAI_TEXT_MODEL,
            api_key=XAI_API_KEY,
            temperature=temperature,
        )

    if selected_provider == "deepseek":
        if not DEEPSEEK_API_KEY:
            raise LLMProviderError(
                "DEEPSEEK_API_KEY is required when LLM_PROVIDER=deepseek."
            )

        from langchain_deepseek import ChatDeepSeek

        return ChatDeepSeek(
            model=DEEPSEEK_TEXT_MODEL,
            api_key=DEEPSEEK_API_KEY,
            temperature=temperature,
        )

    raise LLMProviderError(
        f"Unsupported LLM provider: {selected_provider}"
    )