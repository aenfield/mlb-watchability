"""
Tests for the LLM client module.
"""

import os
from unittest.mock import Mock, patch

import pytest

from mlb_watchability.llm_client import (
    LLMClientError,
    LLMResponse,
    OpenAIClient,
    create_llm_client,
    generate_summary,
)


class TestLLMResponse:
    """Test LLMResponse dataclass."""

    def test_basic_response(self) -> None:
        """Test basic response creation."""
        response = LLMResponse(content="test content", model="gpt-4o")
        assert response.content == "test content"
        assert response.model == "gpt-4o"
        assert response.usage_tokens is None
        assert response.cost_estimate is None

    def test_response_with_metadata(self) -> None:
        """Test response with optional metadata."""
        response = LLMResponse(
            content="test content",
            model="gpt-4o",
            usage_tokens=150,
            cost_estimate=0.003,
        )
        assert response.usage_tokens == 150
        assert response.cost_estimate == 0.003


class TestOpenAIClient:
    """Test OpenAI client implementation."""

    def test_init_with_api_key(self) -> None:
        """Test initialization with explicit API key."""
        with patch("openai.OpenAI") as mock_openai:
            client = OpenAIClient(api_key="test-key", default_model="gpt-3.5-turbo")
            assert client.api_key == "test-key"
            assert client.default_model == "gpt-3.5-turbo"
            mock_openai.assert_called_once_with(api_key="test-key", base_url=None)

    def test_init_with_env_var(self) -> None:
        """Test initialization with environment variable."""
        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}),
            patch("openai.OpenAI") as mock_openai,
        ):
            client = OpenAIClient()
            assert client.api_key == "env-key"
            assert client.default_model == "gpt-4o"
            mock_openai.assert_called_once_with(api_key="env-key", base_url=None)

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
            patch("mlb_watchability.llm_client.openai", None),
            pytest.raises(LLMClientError, match="OpenAI package not installed"),
        ):
            OpenAIClient(api_key="test-key")

    def test_generate_text_success(self) -> None:
        """Test successful text generation."""
        # Mock the OpenAI response
        mock_choice = Mock()
        mock_choice.message.content = "Generated response text"

        mock_usage = Mock()
        mock_usage.total_tokens = 100

        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        with patch("openai.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            client = OpenAIClient(api_key="test-key")
            response = client.generate_text(
                "Test prompt", max_tokens=150, temperature=0.5
            )

            assert isinstance(response, LLMResponse)
            assert response.content == "Generated response text"
            assert response.model == "gpt-4o"
            assert response.usage_tokens == 100

            # Verify the API call
            mock_client.chat.completions.create.assert_called_once_with(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Test prompt"}],
                temperature=0.5,
                max_tokens=150,
            )

    def test_generate_text_with_custom_model(self) -> None:
        """Test text generation with custom model."""
        mock_choice = Mock()
        mock_choice.message.content = "Generated response"

        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None

        with patch("openai.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            client = OpenAIClient(api_key="test-key")
            response = client.generate_text("Test prompt", model="gpt-3.5-turbo")

            assert response.model == "gpt-3.5-turbo"
            assert response.usage_tokens is None

            mock_client.chat.completions.create.assert_called_once_with(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test prompt"}],
                temperature=0.7,
            )

    def test_generate_text_empty_response(self) -> None:
        """Test handling of empty response."""
        mock_choice = Mock()
        mock_choice.message.content = None

        mock_response = Mock()
        mock_response.choices = [mock_choice]

        with patch("openai.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            client = OpenAIClient(api_key="test-key")

            with pytest.raises(LLMClientError, match="Received empty response"):
                client.generate_text("Test prompt")

    def test_generate_text_api_error(self) -> None:
        """Test handling of OpenAI API errors."""
        with patch("openai.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception(
                "API rate limit exceeded"
            )
            mock_openai_class.return_value = mock_client

            client = OpenAIClient(api_key="test-key")

            with pytest.raises(LLMClientError, match="Unexpected error"):
                client.generate_text("Test prompt")


class TestCreateLLMClient:
    """Test LLM client factory function."""

    def test_create_openai_client(self) -> None:
        """Test creating OpenAI client."""
        with patch("mlb_watchability.llm_client.OpenAIClient") as mock_openai:
            mock_instance = Mock()
            mock_openai.return_value = mock_instance

            client = create_llm_client(provider="openai", model="gpt-3.5-turbo")

            assert client == mock_instance
            mock_openai.assert_called_once_with(default_model="gpt-3.5-turbo")

    def test_create_openai_client_default_model(self) -> None:
        """Test creating OpenAI client with default model."""
        with patch("mlb_watchability.llm_client.OpenAIClient") as mock_openai:
            mock_instance = Mock()
            mock_openai.return_value = mock_instance

            client = create_llm_client(provider="openai")

            assert client == mock_instance
            mock_openai.assert_called_once_with(default_model="gpt-4o")

    def test_create_openai_client_case_insensitive(self) -> None:
        """Test provider name is case insensitive."""
        with patch("mlb_watchability.llm_client.OpenAIClient") as mock_openai:
            mock_instance = Mock()
            mock_openai.return_value = mock_instance

            client = create_llm_client(provider="OPENAI")

            assert client == mock_instance
            mock_openai.assert_called_once()

    def test_unsupported_provider(self) -> None:
        """Test error for unsupported provider."""
        with pytest.raises(LLMClientError, match="Unsupported LLM provider: anthropic"):
            create_llm_client(provider="anthropic")

    def test_create_with_additional_kwargs(self) -> None:
        """Test passing additional kwargs to client."""
        with patch("mlb_watchability.llm_client.OpenAIClient") as mock_openai:
            mock_instance = Mock()
            mock_openai.return_value = mock_instance

            client = create_llm_client(
                provider="openai",
                model="gpt-4",
                api_key="custom-key",
                base_url="https://custom.api.com",
            )

            assert client == mock_instance
            mock_openai.assert_called_once_with(
                default_model="gpt-4",
                api_key="custom-key",
                base_url="https://custom.api.com",
            )


class TestGenerateSummary:
    """Test convenience function."""

    def test_generate_summary_success(self) -> None:
        """Test successful summary generation."""
        mock_response = LLMResponse(content="Generated summary", model="gpt-4o")

        with patch("mlb_watchability.llm_client.create_llm_client") as mock_create:
            mock_client = Mock()
            mock_client.generate_text.return_value = mock_response
            mock_create.return_value = mock_client

            result = generate_summary("Test prompt", temperature=0.3, max_tokens=200)

            assert result == "Generated summary"
            mock_create.assert_called_once_with(model="gpt-4o")
            mock_client.generate_text.assert_called_once_with(
                prompt="Test prompt", max_tokens=200, temperature=0.3
            )

    def test_generate_summary_with_custom_model(self) -> None:
        """Test summary generation with custom model."""
        mock_response = LLMResponse(content="Summary", model="gpt-3.5-turbo")

        with patch("mlb_watchability.llm_client.create_llm_client") as mock_create:
            mock_client = Mock()
            mock_client.generate_text.return_value = mock_response
            mock_create.return_value = mock_client

            result = generate_summary("Test prompt", model="gpt-3.5-turbo")

            assert result == "Summary"
            mock_create.assert_called_once_with(model="gpt-3.5-turbo")


class TestIntegrationScenarios:
    """Integration test scenarios without real API calls."""

    def test_end_to_end_mock_workflow(self) -> None:
        """Test complete workflow with mocked components."""
        # Mock OpenAI response
        mock_choice = Mock()
        mock_choice.message.content = (
            "This is a comprehensive game summary with analysis."
        )

        mock_usage = Mock()
        mock_usage.total_tokens = 75

        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        with patch("openai.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            # Test the full workflow
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-api-key"}):
                client = create_llm_client("openai", "gpt-4o")

                prompt = "Analyze this baseball game: Team A vs Team B"
                response = client.generate_text(prompt, max_tokens=100, temperature=0.8)

                assert (
                    response.content
                    == "This is a comprehensive game summary with analysis."
                )
                assert response.model == "gpt-4o"
                assert response.usage_tokens == 75

                # Verify the API was called correctly
                expected_call = {
                    "model": "gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.8,
                    "max_tokens": 100,
                }
                mock_client.chat.completions.create.assert_called_once_with(
                    **expected_call
                )
