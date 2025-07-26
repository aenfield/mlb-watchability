"""
LLM client module for generating game summaries and other text content.

Provides an abstracted interface for LLM operations with configurable providers.
Supports OpenAI models by default with environment-based configuration.
"""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

try:
    import openai
except ImportError:
    openai = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def _raise_empty_response_error() -> None:
    """Helper function to raise empty response error."""
    raise LLMClientError("Received empty response from OpenAI")


@dataclass
class LLMResponse:
    """Response from an LLM request."""
    content: str
    model: str
    usage_tokens: int | None = None
    cost_estimate: float | None = None


class LLMClientError(Exception):
    """Base exception for LLM client errors."""


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        model: str | None = None
    ) -> LLMResponse:
        """
        Generate text from a prompt.

        Args:
            prompt: The input prompt text
            max_tokens: Maximum tokens to generate (None for model default)
            temperature: Sampling temperature (0.0-1.0)
            model: Override the default model

        Returns:
            LLMResponse with generated content and metadata

        Raises:
            LLMClientError: If the request fails
        """
        raise NotImplementedError


class OpenAIClient(LLMClient):
    """OpenAI client implementation."""

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "gpt-4o",
        base_url: str | None = None
    ):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            default_model: Default model to use
            base_url: Base URL for API (for compatible services)
        """
        if openai is None:
            raise LLMClientError(
                "OpenAI package not installed. Install with: pip install openai"
            ) from None

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise LLMClientError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.default_model = default_model
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=base_url
        )

        logger.info(f"Initialized OpenAI client with model: {default_model}")

    def generate_text(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        model: str | None = None
    ) -> LLMResponse:
        """Generate text using OpenAI API."""
        model_to_use = model or self.default_model

        try:
            # Prepare request parameters
            request_params: dict[str, Any] = {
                "model": model_to_use,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            }

            if max_tokens is not None:
                request_params["max_tokens"] = max_tokens

            logger.debug(f"Making OpenAI request with model: {model_to_use}")

            response = self.client.chat.completions.create(**request_params)

            content = response.choices[0].message.content
            if not content:
                _raise_empty_response_error()

            # Extract usage information if available
            usage_tokens = None
            if response.usage:
                usage_tokens = response.usage.total_tokens

            logger.info(
                f"Generated {len(content)} characters using {model_to_use}, "
                f"tokens: {usage_tokens}"
            )

            return LLMResponse(
                content=content,
                model=model_to_use,
                usage_tokens=usage_tokens
            )

        except Exception as e:
            if "openai" in str(type(e)).lower():
                # OpenAI-specific error
                raise LLMClientError(f"OpenAI API error: {str(e)}") from e
            else:
                # Other errors
                raise LLMClientError(f"Unexpected error: {str(e)}") from e


def create_llm_client(
    provider: str = "openai",
    model: str | None = None,
    **kwargs: Any
) -> LLMClient:
    """
    Factory function to create LLM clients.

    Args:
        provider: LLM provider ("openai" supported)
        model: Model name to use (provider-specific defaults if None)
        **kwargs: Additional provider-specific arguments

    Returns:
        Configured LLMClient instance

    Raises:
        LLMClientError: If provider is unsupported or configuration fails
    """
    provider = provider.lower()

    if provider == "openai":
        default_model = model or "gpt-4o"
        return OpenAIClient(default_model=default_model, **kwargs)
    else:
        raise LLMClientError(f"Unsupported LLM provider: {provider}")


# Convenience function for quick usage
def generate_summary(
    prompt: str,
    model: str = "gpt-4o",
    max_tokens: int | None = None,
    temperature: float = 0.7
) -> str:
    """
    Convenience function to generate text with default settings.

    Args:
        prompt: Input prompt
        model: Model to use
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature

    Returns:
        Generated text content

    Raises:
        LLMClientError: If generation fails
    """
    client = create_llm_client(model=model)
    response = client.generate_text(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature
    )
    return response.content
