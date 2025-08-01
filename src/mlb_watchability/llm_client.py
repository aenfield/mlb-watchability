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

# Model constants
MODEL_STRING_FULL = "claude-sonnet-4-20250514"
MODEL_STRING_CHEAP = "claude-3-5-haiku-latest"


def _raise_empty_response_error() -> None:
    """Helper function to raise empty response error."""
    raise LLMClientError("Received empty response from LLM")


@dataclass
class LLMResponse:
    """Response from an LLM request."""

    content: str
    model: str
    usage: dict[str, int] | None = (
        None  # Contains input_tokens, output_tokens, web_search_requests
    )
    cost_estimate: float | None = None
    web_sources: list[dict[str, Any]] | None = None


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
        include_web_search: bool = False,
    ) -> LLMResponse:
        """
        Generate text from a prompt.

        Args:
            prompt: The input prompt text
            max_tokens: Maximum tokens to generate (None for model default)
            temperature: Sampling temperature (0.0-1.0)
            model: Override the default model
            include_web_search: Whether to enable web search capabilities

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
        default_model: str = MODEL_STRING_FULL,
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
        include_web_search: bool = False,
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

            # Add web search tool if requested
            if include_web_search:
                request_params["tools"] = [
                    {
                        "type": "web_search_20250305",
                        "name": "web_search",
                        "max_uses": 1,
                    }
                ]

            logger.debug(
                f"Making Anthropic request with model: {model_to_use}, web_search: {include_web_search}"
            )

            response = self.client.messages.create(**request_params)

            # Extract content from response
            content = ""
            for content_block in response.content:
                if hasattr(content_block, "text"):
                    content += content_block.text

            if not content:
                _raise_empty_response_error()

            # Extract usage information if available
            usage = None
            if hasattr(response, "usage") and response.usage is not None:
                # Extract web search requests from server_tool_use if available
                web_search_requests = 0
                if (
                    hasattr(response.usage, "server_tool_use")
                    and response.usage.server_tool_use is not None
                ):
                    web_search_requests = getattr(
                        response.usage.server_tool_use, "web_search_requests", 0
                    )

                usage = {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "web_search_requests": web_search_requests,
                }

            # Extract web search sources if available
            web_sources = []
            if include_web_search:
                for block in response.content:
                    if (
                        hasattr(block, "type")
                        and block.type == "web_search_tool_result"
                        and hasattr(block, "content")
                    ):
                        # Check if this is an error result first
                        content_str = str(block.content)
                        if (
                            "WebSearchToolResultError" in content_str
                            or "error_code" in content_str
                            or "max_uses_exceeded" in content_str
                        ):
                            continue  # Skip error results

                        # block.content is a list of search results
                        if isinstance(block.content, list):
                            for result in block.content:
                                if hasattr(result, "url") and hasattr(result, "title"):
                                    web_sources.append(
                                        {
                                            "url": result.url,
                                            "title": result.title,
                                            "page_age": getattr(
                                                result, "page_age", None
                                            ),
                                        }
                                    )

            # Log usage details
            if usage:
                logger.info(
                    f"Generated {len(content)} characters using {model_to_use}, "
                    f"input_tokens: {usage['input_tokens']}, output_tokens: {usage['output_tokens']}, "
                    f"web_search_requests: {usage['web_search_requests']}, web_sources: {len(web_sources)}"
                )
            else:
                logger.info(
                    f"Generated {len(content)} characters using {model_to_use}, "
                    f"usage: unavailable, web_sources: {len(web_sources)}"
                )

            return LLMResponse(
                content=content,
                model=model_to_use,
                usage=usage,
                web_sources=web_sources,
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
        default_model = model or MODEL_STRING_FULL
        return AnthropicClient(default_model=default_model, **kwargs)
    else:
        raise LLMClientError(f"Unsupported LLM provider: {provider}")


# Convenience function for quick usage
def generate_text_from_llm(
    prompt: str,
    model: str = MODEL_STRING_FULL,
    max_tokens: int | None = None,
    temperature: float = 0.7,
    include_web_search: bool = False,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Convenience function to generate text with default settings.

    Args:
        prompt: Input prompt
        model: Model to use
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        include_web_search: Whether to enable web search capabilities

    Returns:
        Tuple of (generated text content, list of web sources)
        Web sources list will be empty if include_web_search is False or no sources found

    Raises:
        LLMClientError: If generation fails
    """
    client = create_llm_client(model=model)
    response = client.generate_text(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        include_web_search=include_web_search,
    )
    return response.content, response.web_sources or []
