#!/usr/bin/env python3
"""
Quickie script to experiment with Claude API including web search functionality.
"""

import os
import sys
from anthropic import Anthropic
from dotenv import load_dotenv


def get_prompt_text(filename: str | None = None) -> str:
    """Get the prompt text for the Claude API call.
    
    Args:
        filename: Optional filename to load prompt from. If None, uses default game prompt.
                 If file doesn't exist, falls back to hardcoded prompt.
    
    Returns:
        The prompt text to send to Claude.
    """
    # filename = "game_prompt_2025-07-27_game_0.md"

    prompt = """
        Search the web for information about today's upcoming Mariners-Angels game. 
        The game hasn't happened yet - you're looking for interesting things to generate a preview. 
        """

    if filename is None:
        return prompt
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            prompt = f.read().strip()
            print(f"Loaded prompt from: {filename}")
            return prompt
    except FileNotFoundError:
        print(f"File {filename} not found, using fallback prompt")
        return prompt


def main(max_web_searches: int = 1, prompt_filename: str | None = None):
    """Main function to test Claude API with web search."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Initialize the Anthropic client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment variables")
        print("Please set it in your .env file or as an environment variable")
        return
        
    client = Anthropic(api_key=api_key)
    
    # Get the prompt
    prompt = get_prompt_text(prompt_filename)
    print(f"Prompt: {prompt}")
    print(f"Max web searches: {max_web_searches}")
    
    # Make the API call with web search enabled
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",  
            max_tokens=1000,
            messages=[
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            tools=[
                {
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": max_web_searches
                }
            ]
        )
        
        print("\nClaude's response:")
        print("="*50)
        
        # Display all content blocks in the response
        combined_text = ""
        for i, content_block in enumerate(message.content):
            print(f"\nContent Block {i + 1}:")
            print(f"Type: {content_block.type}")
            
            if content_block.type == "text":
                print(f"Text: {content_block.text}")
                combined_text += content_block.text
            elif content_block.type == "tool_use":
                print(f"Tool Name: {content_block.name}")
                print(f"Tool ID: {content_block.id}")
                print(f"Tool Input: {content_block.input}")
            else:
                print(f"Content: {content_block}")
        
        print("\n" + "="*50)
        print(f"Total content blocks: {len(message.content)}")
        print(f"Model used: {message.model}")
        print(f"Usage: {message.usage}")
        print(f"Stop reason: {message.stop_reason}")
        
        # Calculate and display costs
        if hasattr(message.usage, 'input_tokens') and hasattr(message.usage, 'output_tokens'):
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            
            # Count successful web searches (web_search_tool_result blocks without errors)
            web_searches_used = 0
            for block in message.content:
                if hasattr(block, 'type') and block.type == "web_search_tool_result":
                    # Check if this is an error result by examining the content
                    is_error = False
                    if hasattr(block, 'content'):
                        content_str = str(block.content)
                        # Look for error indicators
                        if ('WebSearchToolResultError' in content_str or 
                            'error_code' in content_str or
                            'max_uses_exceeded' in content_str):
                            is_error = True
                    
                    # Only count successful searches, not errors
                    if not is_error:
                        web_searches_used += 1
            
            # Calculate costs
            input_cost = (input_tokens / 1_000_000) * 3.00  # $3 per million input tokens
            output_cost = (output_tokens / 1_000_000) * 15.00  # $15 per million output tokens
            search_cost = (web_searches_used / 1000) * 10.00  # $10 per 1000 searches
            total_cost = input_cost + output_cost + search_cost
            
            print("\n" + "="*50)
            print("TOKEN USAGE & COST BREAKDOWN:")
            print(f"Input tokens: {input_tokens:,}")
            print(f"Output tokens: {output_tokens:,}")
            print(f"Web searches used: {web_searches_used}")
            print(f"Input cost: ${input_cost:.4f}")
            print(f"Output cost: ${output_cost:.4f}")
            print(f"Search cost: ${search_cost:.4f}")
            print(f"Total estimated cost: ${total_cost:.4f}")
        else:
            print("\nCould not calculate costs - usage information not available")
        
        # Display combined text from all text blocks
        if combined_text.strip():
            print("\n" + "="*50)
            print("COMBINED TEXT OUTPUT:")
            print("="*50)
            print(combined_text)
        else:
            print("\nNo text content found in response")
        
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        print("Make sure ANTHROPIC_API_KEY is properly set in your .env file")


if __name__ == "__main__":
    # Parse command line arguments: [filename] [max_searches]
    max_searches = 1  # default
    filename = None   # default
    
    if len(sys.argv) > 1:
        # First arg is filename
        filename = sys.argv[1]
    
    if len(sys.argv) > 2:
        # Second arg is max_searches
        try:
            max_searches = int(sys.argv[2])
        except ValueError:
            print(f"Invalid max_searches value: {sys.argv[2]}. Using default of 1.")
    
    main(max_searches, filename)