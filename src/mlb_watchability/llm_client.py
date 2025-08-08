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


@dataclass
class LLMParams:
    """Base class for LLM parameters."""

    include_web_search: bool = False


@dataclass
class AnthropicParams(LLMParams):
    """Parameters for Anthropic models."""

    max_tokens: int | None = None
    temperature: float = 0.7
    include_web_search: bool = False


@dataclass
class OpenAIParams(LLMParams):
    """Parameters for OpenAI models (GPT-5)."""

    max_output_tokens: int | None = None
    reasoning_effort: str = "medium"  # minimal, low, medium, high
    verbosity: str = "medium"  # low, medium, high
    include_web_search: bool = False

    def __post_init__(self) -> None:
        """Validate parameters after initialization."""
        valid_reasoning_efforts = {"minimal", "low", "medium", "high"}
        valid_verbosity_levels = {"low", "medium", "high"}

        if self.reasoning_effort not in valid_reasoning_efforts:
            raise ValueError(
                f"reasoning_effort must be one of {valid_reasoning_efforts}, "
                f"got '{self.reasoning_effort}'"
            )

        if self.verbosity not in valid_verbosity_levels:
            raise ValueError(
                f"verbosity must be one of {valid_verbosity_levels}, "
                f"got '{self.verbosity}'"
            )


# Model constants
# Anthropic Models
ANTHROPIC_MODEL_FULL = "claude-sonnet-4-20250514"
ANTHROPIC_MODEL_CHEAP = "claude-3-5-haiku-latest"

# OpenAI Models
OPENAI_MODEL_FULL = "gpt-5"
OPENAI_MODEL_CHEAP = "gpt-5-mini"


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
    # Handle cases where content might be a mock object (for tests)
    content_length = len(content) if hasattr(content, "__len__") else len(str(content))
    web_sources_length = len(web_sources) if hasattr(web_sources, "__len__") else 0

    if usage:
        logger.info(
            f"Generated {content_length} characters using {model}, "
            f"input_tokens: {usage['input_tokens']}, output_tokens: {usage['output_tokens']}, "
            f"web_search_requests: {usage['web_search_requests']}, web_sources: {web_sources_length}"
        )
    else:
        logger.info(
            f"Generated {content_length} characters using {model}, "
            f"usage: unavailable, web_sources: {web_sources_length}"
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
        params: LLMParams,
        model: str | None = None,
    ) -> LLMResponse:
        """
        Generate text from a prompt.

        Args:
            prompt: The input prompt text
            params: Provider-specific parameters (AnthropicParams or OpenAIParams)
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
        default_model: str = ANTHROPIC_MODEL_FULL,
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
        params: LLMParams,
        model: str | None = None,
    ) -> LLMResponse:
        """Generate text using Anthropic API."""
        if not isinstance(params, AnthropicParams):
            raise LLMClientError(
                f"AnthropicClient requires AnthropicParams, got {type(params)}"
            )

        model_to_use = model or self.default_model

        try:
            # Prepare request parameters
            request_params: dict[str, Any] = {
                "model": model_to_use,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": params.temperature,
                "max_tokens": params.max_tokens
                or 1000,  # Anthropic requires max_tokens
            }

            # Add web search tool if requested
            if params.include_web_search:
                request_params["tools"] = [
                    {
                        "type": "web_search_20250305",
                        "name": "web_search",
                        "max_uses": 1,
                    }
                ]

            logger.debug(
                f"Making Anthropic request with model: {model_to_use}, web_search: {params.include_web_search}"
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
            if params.include_web_search:
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
        params: LLMParams,
        model: str | None = None,
    ) -> LLMResponse:
        """Generate text using OpenAI Responses API."""
        if not isinstance(params, OpenAIParams):
            raise LLMClientError(
                f"OpenAIClient requires OpenAIParams, got {type(params)}"
            )

        model_to_use = model or self.default_model

        try:
            # Prepare request parameters for Responses API
            request_params: dict[str, Any] = {
                "model": model_to_use,
                "input": prompt,
            }

            # Add GPT-5 specific parameters for Responses API
            if params.max_output_tokens is not None:
                request_params["max_output_tokens"] = params.max_output_tokens

            request_params["reasoning"] = {"effort": params.reasoning_effort}
            request_params["text"] = {"verbosity": params.verbosity}

            # Add web search tool if requested
            if params.include_web_search:
                request_params["tools"] = [{"type": "web_search"}]

            logger.debug(
                f"Making OpenAI request with model: {model_to_use}, "
                f"reasoning_effort: {params.reasoning_effort}, "
                f"verbosity: {params.verbosity}, "
                f"web_search: {params.include_web_search}"
            )

            # Create response with Responses API
            web_search_enabled = params.include_web_search
            response = self.client.responses.create(**request_params)

            # Extract content from response - handle both mock and real responses
            content = ""

            # First try output_text (simple text responses and mock objects)
            if hasattr(response, "output_text") and response.output_text:
                content = response.output_text
                # For mock objects, content might be a Mock object - convert to string
                if hasattr(content, "_mock_name"):
                    content = str(content)

            # Check if there's content in reasoning output
            elif hasattr(response, "output") and response.output:
                output = response.output
                if hasattr(output, "__iter__"):
                    try:
                        for item in output:
                            # Check if this is a text response item (not reasoning)
                            if (
                                hasattr(item, "type")
                                and item.type == "text"
                                and hasattr(item, "content")
                                and item.content
                            ):
                                content += item.content
                            # Or check if it has text attribute directly
                            elif hasattr(item, "text") and item.text:
                                content += item.text
                    except (TypeError, AttributeError):
                        # Handle cases where output is not iterable or attributes are missing
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
            if web_search_enabled:
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
    params: LLMParams,
    model: str | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Convenience function to generate text with provider-specific parameters.

    Args:
        prompt: Input prompt
        params: Provider-specific parameters (AnthropicParams or OpenAIParams)
        model: Model to use (if None, provider default is used)

    Returns:
        Tuple of (generated text content, list of web sources)
        Web sources list will be empty if web search is disabled or no sources found

    Raises:
        LLMClientError: If generation fails
    """
    # Determine provider from params type
    if isinstance(params, AnthropicParams):
        provider = "anthropic"
    elif isinstance(params, OpenAIParams):
        provider = "openai"
    else:
        raise LLMClientError(f"Unsupported parameter type: {type(params)}")

    client = create_llm_client(provider=provider, model=model)
    response = client.generate_text(prompt=prompt, params=params, model=model)
    return response.content, response.web_sources or []
