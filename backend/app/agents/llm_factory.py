from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from app.core.config import get_settings

settings = get_settings()


def get_chat_model(temperature: float = 0.0, use_reasoning_model: bool = False) -> BaseChatModel:
    """Returns a ChatModel configured with either the fast or frontier model."""
    model_name = settings.REASONING_MODEL if use_reasoning_model else settings.FAST_MODEL
    has_valid_key = (
        settings.OPENAI_API_KEY
        and settings.OPENAI_API_KEY.startswith("sk-")
        and not settings.OPENAI_API_KEY.endswith("here")
    )

    if has_valid_key:
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=SecretStr(settings.OPENAI_API_KEY),
        )

    from langchain_core.messages import AIMessage
    from langchain_core.runnables import RunnableLambda

    def dummy_invoke(inputs: object) -> AIMessage:
        return AIMessage(
            content='{"intent": "FULL_AUDIT", "reasoning": "Test route triggered."}'
        )

    return RunnableLambda(dummy_invoke)  # type: ignore[return-value]
