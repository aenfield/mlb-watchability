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
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


def _raise_empty_response_error() -> None:
    """Helper function to raise empty response error."""
    raise LLMClientError("Received empty response from LLM")


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
        model: str | None = None,
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


class AnthropicClient(LLMClient):
    """Anthropic client implementation."""

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "claude-sonnet-4-20250514",
    ):
        """
        Initialize Anthropic client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            default_model: Default model to use
        """
        if Anthropic is None:
            raise LLMClientError("Anthropic package not installed.") from None

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise LLMClientError("Anthropic API key not provided.")

        self.default_model = default_model
        self.client = Anthropic(api_key=self.api_key)

        logger.info(f"Initialized Anthropic client with model: {default_model}")

    def generate_text(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        model: str | None = None,
    ) -> LLMResponse:
        """Generate text using Anthropic API."""
        model_to_use = model or self.default_model

        try:
            # Prepare request parameters
            request_params: dict[str, Any] = {
                "model": model_to_use,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens or 1000,  # Anthropic requires max_tokens
            }

            logger.debug(f"Making Anthropic request with model: {model_to_use}")

            response = self.client.messages.create(**request_params)

            # Extract content from response
            content = ""
            for content_block in response.content:
                if hasattr(content_block, "text"):
                    content += content_block.text

            if not content:
                _raise_empty_response_error()

            # Extract usage information if available
            usage_tokens = None
            if hasattr(response, "usage") and response.usage is not None:
                usage_tokens = (
                    response.usage.input_tokens + response.usage.output_tokens
                )

            logger.info(
                f"Generated {len(content)} characters using {model_to_use}, "
                f"tokens: {usage_tokens}"
            )

            return LLMResponse(
                content=content, model=model_to_use, usage_tokens=usage_tokens
            )

        except Exception as e:
            if "anthropic" in str(type(e)).lower():
                # Anthropic-specific error
                raise LLMClientError(f"Anthropic API error: {str(e)}") from e
            else:
                # Other errors
                raise LLMClientError(f"Unexpected error: {str(e)}") from e


def create_llm_client(
    provider: str = "anthropic", model: str | None = None, **kwargs: Any
) -> LLMClient:
    """
    Factory function to create LLM clients.

    Args:
        provider: LLM provider ("anthropic" supported)
        model: Model name to use (provider-specific defaults if None)
        **kwargs: Additional provider-specific arguments

    Returns:
        Configured LLMClient instance

    Raises:
        LLMClientError: If provider is unsupported or configuration fails
    """
    provider = provider.lower()

    if provider == "anthropic":
        default_model = model or "claude-sonnet-4-20250514"
        return AnthropicClient(default_model=default_model, **kwargs)
    else:
        raise LLMClientError(f"Unsupported LLM provider: {provider}")


# Convenience function for quick usage
def generate_text_from_llm(
    prompt: str,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int | None = None,
    temperature: float = 0.7,
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
        prompt=prompt, max_tokens=max_tokens, temperature=temperature
    )
    return response.content
