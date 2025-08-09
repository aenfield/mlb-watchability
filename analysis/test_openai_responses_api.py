#!/usr/bin/env python3
"""
Quick script to test OpenAI Responses API with gpt-5-mini and web search.
Prints out the full JSON response to see the structure.
"""

import json
import os
from typing import Any
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()


def test_openai_responses_api() -> None:
    """Test the OpenAI Responses API with web search enabled."""

    # Initialize the OpenAI client
    client = OpenAI()

    print("Testing OpenAI Responses API with gpt-5-mini and web search...")
    print("=" * 60)

    try:
        # Make the API call using the Responses API
        response = client.responses.create(
            model="gpt-5-mini",
            tools=[{"type": "web_search_preview"}],
            input="What's the latest news about MLB today?",
        )

        print("Full response object:")
        print("-" * 40)

        # Convert response to dict if it's not already
        response_dict: dict[str, Any]
        if hasattr(response, "model_dump"):
            response_dict = response.model_dump()
        elif hasattr(response, "__dict__"):
            response_dict = response.__dict__
        else:
            response_dict = dict(response)

        # Pretty print the full JSON response
        print(json.dumps(response_dict, indent=2, default=str))

        print("\n" + "=" * 60)
        print("Response output_text:")
        print("-" * 40)

        # Also print just the output text for easier reading
        if hasattr(response, "output_text"):
            print(response.output_text)
        else:
            print("No output_text attribute found")

    except Exception as e:
        print(f"Error occurred: {e}")
        print(f"Error type: {type(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        exit(1)

    test_openai_responses_api()
