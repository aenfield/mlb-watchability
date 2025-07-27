"""
Tests for the LLM client module.
"""

import os
from unittest.mock import Mock, patch

import pytest

from mlb_watchability.llm_client import (
    AnthropicClient,
    LLMClientError,
    LLMResponse,
    create_llm_client,
    generate_text_from_llm,
)


class TestLLMResponse:
    """Test LLMResponse dataclass."""

    def test_basic_response(self) -> None:
        """Test basic response creation."""
        response = LLMResponse(content="test content", model="claude-sonnet-4-20250514")
        assert response.content == "test content"
        assert response.model == "claude-sonnet-4-20250514"
        assert response.usage_tokens is None
        assert response.cost_estimate is None

    def test_response_with_metadata(self) -> None:
        """Test response with optional metadata."""
        response = LLMResponse(
            content="test content",
            model="claude-sonnet-4-20250514",
            usage_tokens=150,
            cost_estimate=0.003,
        )
        assert response.usage_tokens == 150
        assert response.cost_estimate == 0.003


class TestAnthropicClient:
    """Test Anthropic client implementation."""

    def test_init_with_api_key(self) -> None:
        """Test initialization with explicit API key."""
        with patch("mlb_watchability.llm_client.Anthropic") as mock_anthropic:
            client = AnthropicClient(
                api_key="test-key", default_model="claude-3-sonnet-20240229"
            )
            assert client.api_key == "test-key"
            assert client.default_model == "claude-3-sonnet-20240229"
            mock_anthropic.assert_called_once_with(api_key="test-key")

    def test_init_with_env_var(self) -> None:
        """Test initialization with environment variable."""
        with (
            patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}),
            patch("mlb_watchability.llm_client.Anthropic") as mock_anthropic,
        ):
            client = AnthropicClient()
            assert client.api_key == "env-key"
            assert client.default_model == "claude-sonnet-4-20250514"
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

        mock_response = Mock()
        mock_response.content = [mock_content_block]
        mock_response.usage = mock_usage

        with patch("mlb_watchability.llm_client.Anthropic") as mock_anthropic_class:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic_class.return_value = mock_client

            client = AnthropicClient(api_key="test-key")
            response = client.generate_text(
                "Test prompt", max_tokens=150, temperature=0.5
            )

            assert isinstance(response, LLMResponse)
            assert response.content == "Generated response text"
            assert response.model == "claude-sonnet-4-20250514"
            assert response.usage_tokens == 100

            # Verify the API call
            mock_client.messages.create.assert_called_once_with(
                model="claude-sonnet-4-20250514",
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
            response = client.generate_text(
                "Test prompt", model="claude-3-sonnet-20240229"
            )

            assert response.model == "claude-3-sonnet-20240229"
            assert response.usage_tokens is None

            mock_client.messages.create.assert_called_once_with(
                model="claude-3-sonnet-20240229",
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


class TestCreateLLMClient:
    """Test LLM client factory function."""

    def test_create_anthropic_client(self) -> None:
        """Test creating Anthropic client."""
        with patch("mlb_watchability.llm_client.AnthropicClient") as mock_anthropic:
            mock_instance = Mock()
            mock_anthropic.return_value = mock_instance

            client = create_llm_client(
                provider="anthropic", model="claude-3-sonnet-20240229"
            )

            assert client == mock_instance
            mock_anthropic.assert_called_once_with(
                default_model="claude-3-sonnet-20240229"
            )

    def test_create_anthropic_client_default_model(self) -> None:
        """Test creating Anthropic client with default model."""
        with patch("mlb_watchability.llm_client.AnthropicClient") as mock_anthropic:
            mock_instance = Mock()
            mock_anthropic.return_value = mock_instance

            client = create_llm_client(provider="anthropic")

            assert client == mock_instance
            mock_anthropic.assert_called_once_with(
                default_model="claude-sonnet-4-20250514"
            )

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
        with pytest.raises(LLMClientError, match="Unsupported LLM provider: openai"):
            create_llm_client(provider="openai")

    def test_create_with_additional_kwargs(self) -> None:
        """Test passing additional kwargs to client."""
        with patch("mlb_watchability.llm_client.AnthropicClient") as mock_anthropic:
            mock_instance = Mock()
            mock_anthropic.return_value = mock_instance

            client = create_llm_client(
                provider="anthropic",
                model="claude-3-sonnet-20240229",
                api_key="custom-key",
            )

            assert client == mock_instance
            mock_anthropic.assert_called_once_with(
                default_model="claude-3-sonnet-20240229",
                api_key="custom-key",
            )


class TestGenerateTextFromLLM:
    """Test convenience function."""

    def test_generate_text_from_llm_success(self) -> None:
        """Test successful text generation."""
        mock_response = LLMResponse(
            content="Generated summary", model="claude-sonnet-4-20250514"
        )

        with patch("mlb_watchability.llm_client.create_llm_client") as mock_create:
            mock_client = Mock()
            mock_client.generate_text.return_value = mock_response
            mock_create.return_value = mock_client

            result = generate_text_from_llm(
                "Test prompt", temperature=0.3, max_tokens=200
            )

            assert result == "Generated summary"
            mock_create.assert_called_once_with(model="claude-sonnet-4-20250514")
            mock_client.generate_text.assert_called_once_with(
                prompt="Test prompt", max_tokens=200, temperature=0.3
            )

    def test_generate_text_from_llm_with_custom_model(self) -> None:
        """Test text generation with custom model."""
        mock_response = LLMResponse(content="Summary", model="claude-3-sonnet-20240229")

        with patch("mlb_watchability.llm_client.create_llm_client") as mock_create:
            mock_client = Mock()
            mock_client.generate_text.return_value = mock_response
            mock_create.return_value = mock_client

            result = generate_text_from_llm(
                "Test prompt", model="claude-3-sonnet-20240229"
            )

            assert result == "Summary"
            mock_create.assert_called_once_with(model="claude-3-sonnet-20240229")


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

        mock_response = Mock()
        mock_response.content = [mock_content_block]
        mock_response.usage = mock_usage

        with patch("mlb_watchability.llm_client.Anthropic") as mock_anthropic_class:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic_class.return_value = mock_client

            # Test the full workflow
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-api-key"}):
                client = create_llm_client("anthropic", "claude-sonnet-4-20250514")

                prompt = "Analyze this baseball game: Team A vs Team B"
                response = client.generate_text(prompt, max_tokens=100, temperature=0.8)

                assert (
                    response.content
                    == "This is a comprehensive game summary with analysis."
                )
                assert response.model == "claude-sonnet-4-20250514"
                assert response.usage_tokens == 75

                # Verify the API was called correctly
                expected_call = {
                    "model": "claude-sonnet-4-20250514",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.8,
                    "max_tokens": 100,
                }
                mock_client.messages.create.assert_called_once_with(**expected_call)


@pytest.mark.costly
def test_real_api_call() -> None:
    """Test actual API call with Haiku model - no mocks."""
    # Use the cheapest model for this test
    client = AnthropicClient(default_model="claude-3-haiku-20240307")

    # Send a very simple prompt to minimize cost
    response = client.generate_text(
        prompt="Say 'hello'", max_tokens=10, temperature=0.0
    )

    # Basic validation
    assert isinstance(response, LLMResponse)
    assert response.model == "claude-3-haiku-20240307"
    assert response.usage_tokens is not None
    assert response.usage_tokens > 0
