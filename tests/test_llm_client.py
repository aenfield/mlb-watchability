"""
Tests for the LLM client module.
"""

import os
from unittest.mock import Mock, patch

import pytest

from mlb_watchability.llm_client import (
    MODEL_STRING_CHEAP,
    MODEL_STRING_FULL,
    OPENAI_MODEL_CHEAP,
    OPENAI_MODEL_FULL,
    AnthropicClient,
    LLMClientError,
    LLMResponse,
    OpenAIClient,
    create_llm_client,
    generate_text_from_llm,
)

# Test constants
TEST_PROMPT_MARINERS_GAME = (
    "Generate a short 150 character summary of today's Seattle Mariners game"
)
TEST_PROMPT_MARINERS_GAME_WITH_SEARCH = "Search the web for the latest and generate a short 100 character summary of today's Seattle Mariners game"


class TestLLMResponse:
    """Test LLMResponse dataclass."""

    def test_basic_response(self) -> None:
        """Test basic response creation."""
        response = LLMResponse(content="test content", model=MODEL_STRING_CHEAP)
        assert response.content == "test content"
        assert response.model == MODEL_STRING_CHEAP
        assert response.usage is None
        assert response.cost_estimate is None

    def test_response_with_metadata(self) -> None:
        """Test response with optional metadata."""
        response = LLMResponse(
            content="test content",
            model=MODEL_STRING_CHEAP,
            usage={"input_tokens": 75, "output_tokens": 75, "web_search_requests": 0},
            cost_estimate=0.003,
        )
        assert response.usage == {
            "input_tokens": 75,
            "output_tokens": 75,
            "web_search_requests": 0,
        }
        assert response.cost_estimate == 0.003
        assert response.web_sources is None

    def test_response_with_web_sources(self) -> None:
        """Test response with web sources."""
        web_sources = [
            {
                "url": "https://example.com",
                "title": "Example Title",
                "page_age": "1 day",
            }
        ]
        response = LLMResponse(
            content="test content",
            model=MODEL_STRING_CHEAP,
            web_sources=web_sources,
        )
        assert response.web_sources == web_sources


class TestAnthropicClient:
    """Test Anthropic client implementation."""

    def test_init_with_api_key(self) -> None:
        """Test initialization with explicit API key."""
        with patch("mlb_watchability.llm_client.Anthropic") as mock_anthropic:
            client = AnthropicClient(
                api_key="test-key", default_model=MODEL_STRING_CHEAP
            )
            assert client.api_key == "test-key"
            assert client.default_model == MODEL_STRING_CHEAP
            mock_anthropic.assert_called_once_with(api_key="test-key")

    def test_init_with_env_var(self) -> None:
        """Test initialization with environment variable."""
        with (
            patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}),
            patch("mlb_watchability.llm_client.Anthropic") as mock_anthropic,
        ):
            client = AnthropicClient()
            assert client.api_key == "env-key"
            assert client.default_model == MODEL_STRING_FULL
            mock_anthropic.assert_called_once_with(api_key="env-key")

    def test_init_without_api_key(self) -> None:
        """Test initialization fails without API key."""
        with (
            patch.dict(os.environ, {}, clear=True),
            pytest.raises(LLMClientError, match="Anthropic API key not provided"),
        ):
            AnthropicClient()

    def test_init_missing_anthropic_package(self) -> None:
        """Test initialization fails if anthropic package is missing."""
        with (
            patch("mlb_watchability.llm_client.Anthropic", None),
            pytest.raises(LLMClientError, match="Anthropic package not installed"),
        ):
            AnthropicClient(api_key="test-key")

    def test_generate_text_success(self) -> None:
        """Test successful text generation."""
        # Mock the Anthropic response
        mock_content_block = Mock()
        mock_content_block.text = "Generated response text"

        mock_usage = Mock()
        mock_usage.input_tokens = 50
        mock_usage.output_tokens = 50
        mock_usage.server_tool_use = None

        mock_response = Mock()
        mock_response.content = [mock_content_block]
        mock_response.usage = mock_usage

        with patch("mlb_watchability.llm_client.Anthropic") as mock_anthropic_class:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic_class.return_value = mock_client

            client = AnthropicClient(
                api_key="test-key", default_model=MODEL_STRING_CHEAP
            )
            response = client.generate_text(
                "Test prompt", max_tokens=150, temperature=0.5
            )

            assert isinstance(response, LLMResponse)
            assert response.content == "Generated response text"
            assert response.model == MODEL_STRING_CHEAP
            assert response.usage == {
                "input_tokens": 50,
                "output_tokens": 50,
                "web_search_requests": 0,
            }

            # Verify the API call
            mock_client.messages.create.assert_called_once_with(
                model=MODEL_STRING_CHEAP,
                messages=[{"role": "user", "content": "Test prompt"}],
                temperature=0.5,
                max_tokens=150,
            )

    def test_generate_text_with_custom_model(self) -> None:
        """Test text generation with custom model."""
        mock_content_block = Mock()
        mock_content_block.text = "Generated response"

        mock_response = Mock()
        mock_response.content = [mock_content_block]
        mock_response.usage = None

        with patch("mlb_watchability.llm_client.Anthropic") as mock_anthropic_class:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic_class.return_value = mock_client

            client = AnthropicClient(api_key="test-key")
            response = client.generate_text("Test prompt", model=MODEL_STRING_CHEAP)

            assert response.model == MODEL_STRING_CHEAP
            assert response.usage is None

            mock_client.messages.create.assert_called_once_with(
                model=MODEL_STRING_CHEAP,
                messages=[{"role": "user", "content": "Test prompt"}],
                temperature=0.7,
                max_tokens=1000,
            )

    def test_generate_text_empty_response(self) -> None:
        """Test handling of empty response."""
        mock_response = Mock()
        mock_response.content = []

        with patch("mlb_watchability.llm_client.Anthropic") as mock_anthropic_class:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic_class.return_value = mock_client

            client = AnthropicClient(api_key="test-key")

            with pytest.raises(LLMClientError, match="Received empty response"):
                client.generate_text("Test prompt")

    def test_generate_text_api_error(self) -> None:
        """Test handling of Anthropic API errors."""
        with patch("mlb_watchability.llm_client.Anthropic") as mock_anthropic_class:
            mock_client = Mock()
            mock_client.messages.create.side_effect = Exception(
                "API rate limit exceeded"
            )
            mock_anthropic_class.return_value = mock_client

            client = AnthropicClient(api_key="test-key")

            with pytest.raises(LLMClientError, match="Unexpected error"):
                client.generate_text("Test prompt")

    def test_generate_text_with_web_search(self) -> None:
        """Test text generation with web search enabled."""
        # Mock text content block
        mock_text_block = Mock()
        mock_text_block.type = "text"
        mock_text_block.text = "Generated response with web search"

        # Mock web search result block
        mock_web_result = Mock()
        mock_web_result.url = "https://example.com"
        mock_web_result.title = "Example Article"
        mock_web_result.page_age = "2 hours"

        mock_web_search_block = Mock()
        mock_web_search_block.type = "web_search_tool_result"
        mock_web_search_block.content = [mock_web_result]
        # Ensure this block doesn't have a text attribute
        del mock_web_search_block.text

        mock_response = Mock()
        mock_response.content = [mock_text_block, mock_web_search_block]
        mock_response.usage = None

        with patch("mlb_watchability.llm_client.Anthropic") as mock_anthropic_class:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic_class.return_value = mock_client

            client = AnthropicClient(api_key="test-key")
            response = client.generate_text(
                "Test prompt with web search", include_web_search=True
            )

            assert response.content == "Generated response with web search"
            assert response.web_sources is not None
            assert len(response.web_sources) == 1
            assert response.web_sources[0]["url"] == "https://example.com"
            assert response.web_sources[0]["title"] == "Example Article"
            assert response.web_sources[0]["page_age"] == "2 hours"

            # Verify the API call includes web search tools
            mock_client.messages.create.assert_called_once()
            call_args = mock_client.messages.create.call_args[1]
            assert "tools" in call_args
            assert call_args["tools"][0]["type"] == "web_search_20250305"
            assert call_args["tools"][0]["name"] == "web_search"
            assert call_args["tools"][0]["max_uses"] == 1

    def test_generate_text_web_search_disabled(self) -> None:
        """Test text generation with web search disabled (default)."""
        mock_content_block = Mock()
        mock_content_block.text = "Generated response without web search"

        mock_response = Mock()
        mock_response.content = [mock_content_block]
        mock_response.usage = None

        with patch("mlb_watchability.llm_client.Anthropic") as mock_anthropic_class:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic_class.return_value = mock_client

            client = AnthropicClient(api_key="test-key")
            response = client.generate_text("Test prompt", include_web_search=False)

            assert response.content == "Generated response without web search"
            assert response.web_sources == []

            # Verify the API call does not include tools
            mock_client.messages.create.assert_called_once()
            call_args = mock_client.messages.create.call_args[1]
            assert "tools" not in call_args

    def test_generate_text_web_search_error_handling(self) -> None:
        """Test handling of web search errors."""
        mock_text_block = Mock()
        mock_text_block.type = "text"
        mock_text_block.text = "Generated response"

        # Mock web search error block
        mock_web_error_block = Mock()
        mock_web_error_block.type = "web_search_tool_result"
        mock_web_error_block.content = "WebSearchToolResultError: Search failed"
        # Ensure this block doesn't have a text attribute
        del mock_web_error_block.text

        mock_response = Mock()
        mock_response.content = [mock_text_block, mock_web_error_block]
        mock_response.usage = None

        with patch("mlb_watchability.llm_client.Anthropic") as mock_anthropic_class:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic_class.return_value = mock_client

            client = AnthropicClient(api_key="test-key")
            response = client.generate_text("Test prompt", include_web_search=True)

            assert response.content == "Generated response"
            assert response.web_sources == []  # Error results filtered out

    def test_generate_text_web_search_requests_tracking(self) -> None:
        """Test that web_search_requests are properly tracked from server_tool_use."""
        mock_text_block = Mock()
        mock_text_block.text = "Generated response with web search"

        # Mock usage with server_tool_use containing web_search_requests
        mock_server_tool_use = Mock()
        mock_server_tool_use.web_search_requests = 2

        mock_usage = Mock()
        mock_usage.input_tokens = 100
        mock_usage.output_tokens = 50
        mock_usage.server_tool_use = mock_server_tool_use

        mock_response = Mock()
        mock_response.content = [mock_text_block]
        mock_response.usage = mock_usage

        with patch("mlb_watchability.llm_client.Anthropic") as mock_anthropic_class:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic_class.return_value = mock_client

            client = AnthropicClient(api_key="test-key")
            response = client.generate_text("Test prompt", include_web_search=True)

            assert response.content == "Generated response with web search"
            assert response.usage == {
                "input_tokens": 100,
                "output_tokens": 50,
                "web_search_requests": 2,
            }


class TestOpenAIClient:
    """Test OpenAI client implementation."""

    def test_init_with_api_key(self) -> None:
        """Test initialization with explicit API key."""
        with patch("mlb_watchability.llm_client.OpenAI") as mock_openai:
            client = OpenAIClient(api_key="test-key", default_model=OPENAI_MODEL_CHEAP)
            assert client.api_key == "test-key"
            assert client.default_model == OPENAI_MODEL_CHEAP
            mock_openai.assert_called_once_with(api_key="test-key")

    def test_init_with_env_var(self) -> None:
        """Test initialization with environment variable."""
        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}),
            patch("mlb_watchability.llm_client.OpenAI") as mock_openai,
        ):
            client = OpenAIClient()
            assert client.api_key == "env-key"
            assert client.default_model == OPENAI_MODEL_FULL
            mock_openai.assert_called_once_with(api_key="env-key")

    def test_init_without_api_key(self) -> None:
        """Test initialization fails without API key."""
        with (
            patch.dict(os.environ, {}, clear=True),
            pytest.raises(LLMClientError, match="OpenAI API key not provided"),
        ):
            OpenAIClient()

    def test_init_missing_openai_package(self) -> None:
        """Test initialization fails if openai package is missing."""
        with (
            patch("mlb_watchability.llm_client.OpenAI", None),
            pytest.raises(LLMClientError, match="OpenAI package not installed"),
        ):
            OpenAIClient(api_key="test-key")

    def test_generate_text_success(self) -> None:
        """Test successful text generation."""
        # Mock the OpenAI response
        mock_usage = Mock()
        mock_usage.input_tokens = 40
        mock_usage.output_tokens = 60

        mock_response = Mock()
        mock_response.output_text = "Generated OpenAI response text"
        mock_response.usage = mock_usage

        with patch("mlb_watchability.llm_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_client.responses.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            client = OpenAIClient(api_key="test-key", default_model=OPENAI_MODEL_CHEAP)
            response = client.generate_text(
                "Test prompt", max_tokens=150, temperature=0.5
            )

            assert isinstance(response, LLMResponse)
            assert response.content == "Generated OpenAI response text"
            assert response.model == OPENAI_MODEL_CHEAP
            assert response.usage == {
                "input_tokens": 40,
                "output_tokens": 60,
                "web_search_requests": 0,
            }

            # Verify the API call (GPT-5 Responses API doesn't support temperature/max_tokens)
            mock_client.responses.create.assert_called_once_with(
                model=OPENAI_MODEL_CHEAP,
                input="Test prompt",
            )

    def test_generate_text_with_custom_model(self) -> None:
        """Test text generation with custom model."""
        mock_response = Mock()
        mock_response.output_text = "Generated response"
        mock_response.usage = None

        with patch("mlb_watchability.llm_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_client.responses.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            client = OpenAIClient(api_key="test-key")
            response = client.generate_text("Test prompt", model=OPENAI_MODEL_CHEAP)

            assert response.model == OPENAI_MODEL_CHEAP
            assert response.usage is None

            mock_client.responses.create.assert_called_once_with(
                model=OPENAI_MODEL_CHEAP,
                input="Test prompt",
            )

    def test_generate_text_empty_response(self) -> None:
        """Test handling of empty response."""
        mock_response = Mock()
        mock_response.output_text = ""

        with patch("mlb_watchability.llm_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_client.responses.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            client = OpenAIClient(api_key="test-key")

            with pytest.raises(LLMClientError, match="Received empty response"):
                client.generate_text("Test prompt")

    def test_generate_text_api_error(self) -> None:
        """Test handling of OpenAI API errors."""
        with patch("mlb_watchability.llm_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_client.responses.create.side_effect = Exception(
                "API rate limit exceeded"
            )
            mock_openai_class.return_value = mock_client

            client = OpenAIClient(api_key="test-key")

            with pytest.raises(LLMClientError, match="Unexpected error"):
                client.generate_text("Test prompt")

    def test_generate_text_with_web_search(self) -> None:
        """Test text generation with web search enabled."""
        # Mock web search tool call
        mock_web_result = Mock()
        mock_web_result.url = "https://example.com"
        mock_web_result.title = "Example Article"
        mock_web_result.page_age = "1 hour"

        mock_tool_output = Mock()
        mock_tool_output.results = [mock_web_result]

        mock_tool_call = Mock()
        mock_tool_call.type = "web_search"
        mock_tool_call.output = mock_tool_output

        mock_usage = Mock()
        mock_usage.input_tokens = 50
        mock_usage.output_tokens = 75

        mock_response = Mock()
        mock_response.output_text = "Generated response with web search"
        mock_response.usage = mock_usage
        mock_response.tool_calls = [mock_tool_call]

        with patch("mlb_watchability.llm_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_client.responses.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            client = OpenAIClient(api_key="test-key")
            response = client.generate_text(
                "Test prompt with web search", include_web_search=True
            )

            assert response.content == "Generated response with web search"
            assert response.web_sources is not None
            assert len(response.web_sources) == 1
            assert response.web_sources[0]["url"] == "https://example.com"
            assert response.web_sources[0]["title"] == "Example Article"
            assert response.web_sources[0]["page_age"] == "1 hour"
            assert response.usage is not None
            assert response.usage["web_search_requests"] == 1

            # Verify the API call includes web search tools
            mock_client.responses.create.assert_called_once()
            call_args = mock_client.responses.create.call_args[1]
            assert "tools" in call_args
            assert call_args["tools"] == [{"type": "web_search"}]

    def test_generate_text_web_search_disabled(self) -> None:
        """Test text generation with web search disabled (default)."""
        mock_response = Mock()
        mock_response.output_text = "Generated response without web search"
        mock_response.usage = None

        with patch("mlb_watchability.llm_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_client.responses.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            client = OpenAIClient(api_key="test-key")
            response = client.generate_text("Test prompt", include_web_search=False)

            assert response.content == "Generated response without web search"
            assert response.web_sources == []

            # Verify the API call does not include tools
            mock_client.responses.create.assert_called_once()
            call_args = mock_client.responses.create.call_args[1]
            assert "tools" not in call_args

    def test_generate_text_no_tool_calls(self) -> None:
        """Test text generation when response has no tool_calls attribute."""
        mock_usage = Mock()
        mock_usage.input_tokens = 30
        mock_usage.output_tokens = 45

        mock_response = Mock()
        mock_response.output_text = "Generated response"
        mock_response.usage = mock_usage
        # Remove tool_calls attribute to simulate no tool calls
        if hasattr(mock_response, "tool_calls"):
            delattr(mock_response, "tool_calls")

        with patch("mlb_watchability.llm_client.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_client.responses.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            client = OpenAIClient(api_key="test-key")
            response = client.generate_text("Test prompt", include_web_search=True)

            assert response.content == "Generated response"
            assert response.web_sources == []
            assert response.usage is not None
            assert response.usage["web_search_requests"] == 0


class TestCreateLLMClient:
    """Test LLM client factory function."""

    def test_create_anthropic_client(self) -> None:
        """Test creating Anthropic client."""
        with patch("mlb_watchability.llm_client.AnthropicClient") as mock_anthropic:
            mock_instance = Mock()
            mock_anthropic.return_value = mock_instance

            client = create_llm_client(provider="anthropic", model=MODEL_STRING_FULL)

            assert client == mock_instance
            mock_anthropic.assert_called_once_with(default_model=MODEL_STRING_FULL)

    def test_create_anthropic_client_default_model(self) -> None:
        """Test creating Anthropic client with default model."""
        with patch("mlb_watchability.llm_client.AnthropicClient") as mock_anthropic:
            mock_instance = Mock()
            mock_anthropic.return_value = mock_instance

            client = create_llm_client(provider="anthropic")

            assert client == mock_instance
            mock_anthropic.assert_called_once_with(default_model=MODEL_STRING_FULL)

    def test_create_anthropic_client_case_insensitive(self) -> None:
        """Test provider name is case insensitive."""
        with patch("mlb_watchability.llm_client.AnthropicClient") as mock_anthropic:
            mock_instance = Mock()
            mock_anthropic.return_value = mock_instance

            client = create_llm_client(provider="ANTHROPIC")

            assert client == mock_instance
            mock_anthropic.assert_called_once()

    def test_unsupported_provider(self) -> None:
        """Test error for unsupported provider."""
        with pytest.raises(LLMClientError, match="Unsupported LLM provider: unknown"):
            create_llm_client(provider="unknown")

    def test_create_with_additional_kwargs(self) -> None:
        """Test passing additional kwargs to client."""
        with patch("mlb_watchability.llm_client.AnthropicClient") as mock_anthropic:
            mock_instance = Mock()
            mock_anthropic.return_value = mock_instance

            client = create_llm_client(
                provider="anthropic",
                model=MODEL_STRING_CHEAP,
                api_key="custom-key",
            )

            assert client == mock_instance
            mock_anthropic.assert_called_once_with(
                default_model=MODEL_STRING_CHEAP,
                api_key="custom-key",
            )

    def test_create_openai_client(self) -> None:
        """Test creating OpenAI client."""
        with patch("mlb_watchability.llm_client.OpenAIClient") as mock_openai:
            mock_instance = Mock()
            mock_openai.return_value = mock_instance

            client = create_llm_client(provider="openai", model=OPENAI_MODEL_FULL)

            assert client == mock_instance
            mock_openai.assert_called_once_with(default_model=OPENAI_MODEL_FULL)

    def test_create_openai_client_default_model(self) -> None:
        """Test creating OpenAI client with default model."""
        with patch("mlb_watchability.llm_client.OpenAIClient") as mock_openai:
            mock_instance = Mock()
            mock_openai.return_value = mock_instance

            client = create_llm_client(provider="openai")

            assert client == mock_instance
            mock_openai.assert_called_once_with(default_model=OPENAI_MODEL_FULL)

    def test_create_openai_client_case_insensitive(self) -> None:
        """Test provider name is case insensitive for OpenAI."""
        with patch("mlb_watchability.llm_client.OpenAIClient") as mock_openai:
            mock_instance = Mock()
            mock_openai.return_value = mock_instance

            client = create_llm_client(provider="OPENAI")

            assert client == mock_instance
            mock_openai.assert_called_once()

    def test_create_openai_with_additional_kwargs(self) -> None:
        """Test passing additional kwargs to OpenAI client."""
        with patch("mlb_watchability.llm_client.OpenAIClient") as mock_openai:
            mock_instance = Mock()
            mock_openai.return_value = mock_instance

            client = create_llm_client(
                provider="openai",
                model=OPENAI_MODEL_CHEAP,
                api_key="custom-openai-key",
            )

            assert client == mock_instance
            mock_openai.assert_called_once_with(
                default_model=OPENAI_MODEL_CHEAP,
                api_key="custom-openai-key",
            )

    def test_generic_model_mapping_anthropic(self) -> None:
        """Test generic model name mapping for Anthropic."""
        with patch("mlb_watchability.llm_client.AnthropicClient") as mock_anthropic:
            mock_instance = Mock()
            mock_anthropic.return_value = mock_instance

            # Test "normal" mapping
            create_llm_client(provider="anthropic", model="normal")
            mock_anthropic.assert_called_with(default_model=MODEL_STRING_FULL)

            mock_anthropic.reset_mock()

            # Test "cheap" mapping
            create_llm_client(provider="anthropic", model="cheap")
            mock_anthropic.assert_called_with(default_model=MODEL_STRING_CHEAP)

            mock_anthropic.reset_mock()

            # Test "full" mapping
            create_llm_client(provider="anthropic", model="full")
            mock_anthropic.assert_called_with(default_model=MODEL_STRING_FULL)

    def test_generic_model_mapping_openai(self) -> None:
        """Test generic model name mapping for OpenAI."""
        with patch("mlb_watchability.llm_client.OpenAIClient") as mock_openai:
            mock_instance = Mock()
            mock_openai.return_value = mock_instance

            # Test "normal" mapping
            create_llm_client(provider="openai", model="normal")
            mock_openai.assert_called_with(default_model=OPENAI_MODEL_FULL)

            mock_openai.reset_mock()

            # Test "cheap" mapping
            create_llm_client(provider="openai", model="cheap")
            mock_openai.assert_called_with(default_model=OPENAI_MODEL_CHEAP)

            mock_openai.reset_mock()

            # Test "full" mapping
            create_llm_client(provider="openai", model="full")
            mock_openai.assert_called_with(default_model=OPENAI_MODEL_FULL)

    def test_custom_model_string_passthrough(self) -> None:
        """Test that custom model strings are passed through unchanged."""
        with patch("mlb_watchability.llm_client.OpenAIClient") as mock_openai:
            mock_instance = Mock()
            mock_openai.return_value = mock_instance

            # Test custom model string
            custom_model = "gpt-4o-custom"
            create_llm_client(provider="openai", model=custom_model)
            mock_openai.assert_called_with(default_model=custom_model)


class TestGenerateTextFromLLM:
    """Test convenience function."""

    def test_generate_text_from_llm_success(self) -> None:
        """Test successful text generation."""
        mock_response = LLMResponse(
            content="Generated summary", model=MODEL_STRING_FULL, web_sources=[]
        )

        with patch("mlb_watchability.llm_client.create_llm_client") as mock_create:
            mock_client = Mock()
            mock_client.generate_text.return_value = mock_response
            mock_create.return_value = mock_client

            text, sources = generate_text_from_llm(
                "Test prompt", temperature=0.3, max_tokens=200
            )

            assert text == "Generated summary"
            assert sources == []
            mock_create.assert_called_once_with(model=MODEL_STRING_FULL)
            mock_client.generate_text.assert_called_once_with(
                prompt="Test prompt",
                max_tokens=200,
                temperature=0.3,
                include_web_search=False,
            )

    def test_generate_text_from_llm_with_custom_model(self) -> None:
        """Test text generation with custom model."""
        mock_response = LLMResponse(
            content="Summary", model=MODEL_STRING_CHEAP, web_sources=[]
        )

        with patch("mlb_watchability.llm_client.create_llm_client") as mock_create:
            mock_client = Mock()
            mock_client.generate_text.return_value = mock_response
            mock_create.return_value = mock_client

            text, sources = generate_text_from_llm(
                "Test prompt", model=MODEL_STRING_CHEAP
            )

            assert text == "Summary"
            assert sources == []
            mock_create.assert_called_once_with(model=MODEL_STRING_CHEAP)

    def test_generate_text_from_llm_with_web_search(self) -> None:
        """Test text generation with web search enabled."""
        web_sources = [
            {"url": "https://example.com", "title": "Test", "page_age": None}
        ]
        mock_response = LLMResponse(
            content="Summary with web search",
            model=MODEL_STRING_FULL,
            web_sources=web_sources,
        )

        with patch("mlb_watchability.llm_client.create_llm_client") as mock_create:
            mock_client = Mock()
            mock_client.generate_text.return_value = mock_response
            mock_create.return_value = mock_client

            text, sources = generate_text_from_llm(
                "Test prompt", include_web_search=True
            )

            assert text == "Summary with web search"
            assert sources == web_sources
            mock_client.generate_text.assert_called_once_with(
                prompt="Test prompt",
                max_tokens=None,
                temperature=0.7,
                include_web_search=True,
            )


class TestIntegrationScenarios:
    """Integration test scenarios without real API calls."""

    def test_end_to_end_mock_workflow(self) -> None:
        """Test complete workflow with mocked components."""
        # Mock Anthropic response
        mock_content_block = Mock()
        mock_content_block.text = "This is a comprehensive game summary with analysis."

        mock_usage = Mock()
        mock_usage.input_tokens = 25
        mock_usage.output_tokens = 50
        mock_usage.server_tool_use = None

        mock_response = Mock()
        mock_response.content = [mock_content_block]
        mock_response.usage = mock_usage

        with patch("mlb_watchability.llm_client.Anthropic") as mock_anthropic_class:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic_class.return_value = mock_client

            # Test the full workflow
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-api-key"}):
                client = create_llm_client("anthropic", MODEL_STRING_CHEAP)

                prompt = "Analyze this baseball game: Team A vs Team B"
                response = client.generate_text(prompt, max_tokens=100, temperature=0.8)

                assert (
                    response.content
                    == "This is a comprehensive game summary with analysis."
                )
                assert response.model == MODEL_STRING_CHEAP
                assert response.usage == {
                    "input_tokens": 25,
                    "output_tokens": 50,
                    "web_search_requests": 0,
                }

                # Verify the API was called correctly
                expected_call = {
                    "model": MODEL_STRING_CHEAP,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.8,
                    "max_tokens": 100,
                }
                mock_client.messages.create.assert_called_once_with(**expected_call)


class TestCallActualAPI:
    """Test with actual calls to the LLM API."""

    @pytest.mark.costly
    def test_generate_text_from_llm_real_api_call_no_web_search(self) -> None:
        """Test convenience function (and thereby also client.generate_text) with real API calls without web search."""
        text, sources = generate_text_from_llm(
            prompt=TEST_PROMPT_MARINERS_GAME,
            model=MODEL_STRING_CHEAP,
            max_tokens=100,
            temperature=0.0,
            include_web_search=False,
        )

        assert len(text) > 0
        assert sources == []

    @pytest.mark.costly
    def test_generate_text_from_llm_real_api_call_with_web_search(self) -> None:
        """Test convenience function (and thereby also client.generate_text) with real API calls with a web search."""
        text_with_search, sources_with_search = generate_text_from_llm(
            prompt=TEST_PROMPT_MARINERS_GAME_WITH_SEARCH,
            model=MODEL_STRING_CHEAP,
            max_tokens=100,
            temperature=0.0,
            include_web_search=True,
        )

        assert len(text_with_search) > 0
        assert isinstance(sources_with_search, list) and len(sources_with_search) > 0

    # to save run time and a bit of money, I'll just text client.generate_text via
    # the convenience function tests above (which call it immediately) - not ideal, but ok
    # @pytest.mark.costly
    # def test_real_api_call_without_web_search() -> None:
    #     """Test actual API call without web search using the cheap model."""
    #     client = AnthropicClient(default_model=MODEL_STRING_CHEAP)

    #     response = client.generate_text(
    #         prompt=TEST_PROMPT_MARINERS_GAME,
    #         max_tokens=100,
    #         temperature=0.0,
    #         include_web_search=False,
    #     )

    #     # Basic validation - don't test specific content as it's brittle
    #     assert isinstance(response, LLMResponse)
    #     assert response.model == MODEL_STRING_CHEAP
    #     assert response.usage is not None
    #     assert response.usage["input_tokens"] > 0
    #     assert len(response.content) > 0
    #     assert response.web_sources == []

    # @pytest.mark.costly
    # def test_real_api_call_with_web_search() -> None:
    #     """Test actual API call with web search using the cheap model."""
    #     client = AnthropicClient(default_model=MODEL_STRING_CHEAP)

    #     response = client.generate_text(
    #         prompt=TEST_PROMPT_MARINERS_GAME_WITH_SEARCH,
    #         max_tokens=100,
    #         temperature=0.0,
    #         include_web_search=True,
    #     )

    #     # Basic validation - don't test specific content as it's brittle
    #     assert isinstance(response, LLMResponse)
    #     assert response.model == MODEL_STRING_CHEAP
    #     assert response.usage is not None
    #     assert response.usage["input_tokens"] > 0
    #     assert len(response.content) > 0
    #     # I'm going to test for web results even though I don't know 100% since the model decides when to search
    #     assert isinstance(response.web_sources, list) and len(response.web_sources) > 0

    @pytest.mark.costly
    def test_openai_real_api_call_no_web_search(self) -> None:
        """Test OpenAI client with real API calls without web search."""
        client = create_llm_client(provider="openai", model="cheap")

        response = client.generate_text(
            prompt=TEST_PROMPT_MARINERS_GAME,
            max_tokens=100,
            temperature=0.0,
            include_web_search=False,
        )

        # Basic validation - don't test specific content as it's brittle
        assert isinstance(response, LLMResponse)
        assert response.model == OPENAI_MODEL_CHEAP
        assert len(response.content) > 0
        assert response.web_sources == []

    @pytest.mark.costly
    def test_openai_real_api_call_with_web_search(self) -> None:
        """Test OpenAI client with real API calls with web search."""
        client = create_llm_client(provider="openai", model="cheap")

        response = client.generate_text(
            prompt=TEST_PROMPT_MARINERS_GAME_WITH_SEARCH,
            max_tokens=100,
            temperature=0.0,
            include_web_search=True,
        )

        # Basic validation - don't test specific content as it's brittle
        assert isinstance(response, LLMResponse)
        assert response.model == OPENAI_MODEL_CHEAP
        assert len(response.content) > 0

        # OpenAI Responses API provides web search through annotations
        assert response.usage is not None
        assert response.usage["web_search_requests"] > 0

        # Should have structured web sources from annotations (url_citation type)
        assert isinstance(response.web_sources, list)
        assert (
            len(response.web_sources) > 0
        ), "Should extract web sources from annotations"

        # Verify structure of web sources
        for source in response.web_sources:
            assert "url" in source
            assert "title" in source
            assert source["url"]  # URL should not be empty
            assert source["title"]  # Title should not be empty
