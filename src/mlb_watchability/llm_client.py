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

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

# Model constants
# Anthropic Models
ANTHROPIC_MODEL_FULL = "claude-sonnet-4-20250514"
ANTHROPIC_MODEL_CHEAP = "claude-3-5-haiku-latest"

# OpenAI Models
OPENAI_MODEL_FULL = "gpt-5"
OPENAI_MODEL_CHEAP = "gpt-5-mini"

# Backward compatibility aliases
MODEL_STRING_FULL = ANTHROPIC_MODEL_FULL
MODEL_STRING_CHEAP = ANTHROPIC_MODEL_CHEAP


def _raise_empty_response_error() -> None:
    """Helper function to raise empty response error."""
    raise LLMClientError("Received empty response from LLM")


def _log_generation_details(
    content: str,
    model: str,
    usage: dict[str, int] | None,
    web_sources: list[dict[str, Any]],
) -> None:
    """Helper function to log generation details consistently."""
    if usage:
        logger.info(
            f"Generated {len(content)} characters using {model}, "
            f"input_tokens: {usage['input_tokens']}, output_tokens: {usage['output_tokens']}, "
            f"web_search_requests: {usage['web_search_requests']}, web_sources: {len(web_sources)}"
        )
    else:
        logger.info(
            f"Generated {len(content)} characters using {model}, "
            f"usage: unavailable, web_sources: {len(web_sources)}"
        )


def _validate_response_content(content: str) -> None:
    """Helper function to validate response content is not empty."""
    if not content:
        _raise_empty_response_error()


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

            _validate_response_content(content)

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
            _log_generation_details(content, model_to_use, usage, web_sources)

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


class OpenAIClient(LLMClient):
    """OpenAI client implementation using GPT-5 and Responses API."""

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = OPENAI_MODEL_FULL,
    ):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            default_model: Default model to use
        """
        if OpenAI is None:
            raise LLMClientError("OpenAI package not installed.") from None

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise LLMClientError("OpenAI API key not provided.")

        self.default_model = default_model
        self.client = OpenAI(api_key=self.api_key)

        logger.info(f"Initialized OpenAI client with model: {default_model}")

    def generate_text(
        self,
        prompt: str,
        max_tokens: (  # noqa: ARG002 - Kept for interface compatibility
            int | None
        ) = None,
        temperature: float = 0.7,  # noqa: ARG002 - Kept for interface compatibility
        model: str | None = None,
        include_web_search: bool = False,
    ) -> LLMResponse:
        """Generate text using OpenAI Responses API."""
        model_to_use = model or self.default_model

        try:
            # Prepare request parameters for Responses API
            request_params: dict[str, Any] = {
                "model": model_to_use,
                "input": prompt,
            }

            # Note: OpenAI Responses API with GPT-5 models doesn't support some parameters:
            # - max_tokens/max_completion_tokens: API handles response length internally
            # - temperature: Not supported with GPT-5 models
            # The API is designed to be simpler and more autonomous

            # Add web search tool if requested
            if include_web_search:
                request_params["tools"] = [{"type": "web_search"}]

            logger.debug(
                f"Making OpenAI request with model: {model_to_use}, web_search: {include_web_search}"
            )

            # First try with web search if requested
            try:
                response = self.client.responses.create(**request_params)
            except Exception as e:
                # If web search fails due to model incompatibility, retry without web search
                if include_web_search and (
                    "web_search" in str(e).lower() or "tool" in str(e).lower()
                ):
                    logger.warning(
                        f"Web search not supported with model {model_to_use}, retrying without web search"
                    )
                    # Remove tools and retry
                    request_params.pop("tools", None)
                    include_web_search = False  # Update flag for later processing
                    response = self.client.responses.create(**request_params)
                else:
                    raise  # Re-raise if it's a different error

            # Extract content from response - check both output_text and output
            content = getattr(response, "output_text", "")
            if not content and hasattr(response, "output"):
                # For newer OpenAI responses, content might be in output messages
                output = getattr(response, "output", [])
                if output:
                    try:
                        for message in output:
                            if hasattr(message, "content"):
                                for content_item in message.content:
                                    if hasattr(content_item, "text"):
                                        content += content_item.text
                    except (TypeError, AttributeError):
                        # Handle mock objects or other non-iterable outputs
                        pass
            _validate_response_content(content)

            # Extract usage information if available
            usage = None
            if hasattr(response, "usage") and response.usage is not None:
                usage = {
                    "input_tokens": getattr(response.usage, "input_tokens", 0),
                    "output_tokens": getattr(response.usage, "output_tokens", 0),
                    "web_search_requests": 0,  # Will be updated if web search was used
                }

            # Extract web search sources if available
            web_sources = []
            if include_web_search:
                # Method 1: Check for citations in the output messages (newer OpenAI Responses API format)
                if hasattr(response, "output"):
                    output = getattr(response, "output", [])
                    try:
                        for message in output:
                            if hasattr(message, "content"):
                                for content_item in message.content:
                                    if hasattr(content_item, "annotations"):
                                        for annotation in content_item.annotations:
                                            if (
                                                hasattr(annotation, "type")
                                                and annotation.type == "url_citation"
                                                and hasattr(annotation, "url")
                                                and hasattr(annotation, "title")
                                            ):
                                                web_sources.append(
                                                    {
                                                        "url": annotation.url,
                                                        "title": annotation.title,
                                                        "page_age": None,
                                                    }
                                                )
                    except (TypeError, AttributeError):
                        # Handle mock objects or other non-iterable outputs
                        pass

                # Method 2: Check for tool_calls (fallback for older format or testing)
                if not web_sources:
                    tool_calls = getattr(response, "tool_calls", [])
                    if tool_calls and hasattr(tool_calls, "__iter__"):
                        try:
                            for tool_call in tool_calls:
                                if hasattr(tool_call, "type") and (
                                    tool_call.type
                                    in (
                                        "web_search",
                                        "web_search_preview",
                                        "web_search_call",
                                    )
                                ):
                                    # Update web search request count
                                    if usage:
                                        usage["web_search_requests"] += 1

                                    # Try different possible output structures
                                    output = getattr(tool_call, "output", None)
                                    if output and hasattr(output, "results"):
                                        for result in output.results:
                                            if hasattr(result, "url") and hasattr(
                                                result, "title"
                                            ):
                                                web_sources.append(
                                                    {
                                                        "url": result.url,
                                                        "title": result.title,
                                                        "page_age": getattr(
                                                            result, "page_age", None
                                                        ),
                                                    }
                                                )
                        except (TypeError, AttributeError):
                            # Handle mock objects or other non-iterable outputs
                            pass

                # Update web search requests count if we found citations
                if web_sources and usage:
                    usage["web_search_requests"] = max(
                        1, usage.get("web_search_requests", 0)
                    )

                # Final fallback: If content has URLs but no sources found,
                # assume web search occurred based on content pattern
                if (
                    not web_sources
                    and ("http" in content or ".com" in content)
                    and usage
                ):
                    usage["web_search_requests"] = 1

            # Log usage details
            _log_generation_details(content, model_to_use, usage, web_sources)

            return LLMResponse(
                content=content,
                model=model_to_use,
                usage=usage,
                web_sources=web_sources,
            )

        except Exception as e:
            if "openai" in str(type(e)).lower():
                # OpenAI-specific error
                raise LLMClientError(f"OpenAI API error: {str(e)}") from e
            else:
                # Other errors
                raise LLMClientError(f"Unexpected error: {str(e)}") from e


def create_llm_client(
    provider: str = "anthropic", model: str | None = None, **kwargs: Any
) -> LLMClient:
    """
    Factory function to create LLM clients.

    Args:
        provider: LLM provider ("anthropic" or "openai")
        model: Model name to use. Can be:
            - Provider-specific model string (e.g. "gpt-5", "claude-sonnet-4-20250514")
            - Generic model type ("normal", "cheap", "full")
            - None (uses provider default)
        **kwargs: Additional provider-specific arguments

    Returns:
        Configured LLMClient instance

    Raises:
        LLMClientError: If provider is unsupported or configuration fails
    """
    provider = provider.lower()

    # Map generic model names to provider-specific models
    def get_provider_model(provider: str, model: str | None) -> str:
        # Model mapping for each provider
        model_maps = {
            "anthropic": {
                "full": ANTHROPIC_MODEL_FULL,
                "normal": ANTHROPIC_MODEL_FULL,
                "cheap": ANTHROPIC_MODEL_CHEAP,
                None: ANTHROPIC_MODEL_FULL,  # Default
            },
            "openai": {
                "full": OPENAI_MODEL_FULL,
                "normal": OPENAI_MODEL_FULL,
                "cheap": OPENAI_MODEL_CHEAP,
                None: OPENAI_MODEL_FULL,  # Default
            },
        }

        # Return mapped model or original model string
        return model_maps.get(provider, {}).get(model, model or "")

    if provider == "anthropic":
        default_model = get_provider_model("anthropic", model)
        return AnthropicClient(default_model=default_model, **kwargs)
    elif provider == "openai":
        default_model = get_provider_model("openai", model)
        return OpenAIClient(default_model=default_model, **kwargs)
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
