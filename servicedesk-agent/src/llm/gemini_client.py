"""Gemini LLM client configuration using langchain-google-genai."""

from functools import lru_cache
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI

from src.config.settings import get_settings


@lru_cache
def get_gemini_client(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> ChatGoogleGenerativeAI:
    """Get configured Gemini client instance.

    Uses langchain-google-genai which supports both:
    - Direct Gemini API (with GOOGLE_API_KEY)
    - Vertex AI (with GOOGLE_CLOUD_PROJECT and GOOGLE_GENAI_USE_VERTEXAI)

    Args:
        model: Model name override. Defaults to settings.llm_model.
        temperature: Temperature override. Defaults to settings.llm_temperature.

    Returns:
        Configured ChatGoogleGenerativeAI instance.
    """
    settings = get_settings()

    return ChatGoogleGenerativeAI(
        model=model or settings.llm_model,
        temperature=temperature if temperature is not None else settings.llm_temperature,
        # Vertex AI configuration is picked up from environment variables:
        # - GOOGLE_CLOUD_PROJECT
        # - GOOGLE_GENAI_USE_VERTEXAI
        # - VERTEXAI_LOCATION
    )


def get_gemini_client_for_classification() -> ChatGoogleGenerativeAI:
    """Get Gemini client optimized for classification tasks.

    Uses lower temperature for more deterministic outputs.

    Returns:
        ChatGoogleGenerativeAI configured for classification.
    """
    settings = get_settings()

    return ChatGoogleGenerativeAI(
        model=settings.llm_model,
        temperature=0.3,  # Lower temperature for classification
    )


def get_gemini_client_for_generation() -> ChatGoogleGenerativeAI:
    """Get Gemini client optimized for text generation.

    Uses default temperature for natural responses.

    Returns:
        ChatGoogleGenerativeAI configured for generation.
    """
    return get_gemini_client()
