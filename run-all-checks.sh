#!/bin/bash

# Pre-commit check script for MLB Watchability
# Run all quality checks before committing

set -e  # Exit on any error

echo "🔍 Running pre-commit checks..."
echo

# Format code with black
echo "📝 Formatting code with black..."
uv run black .
echo "✅ Code formatted"
echo

# Check and fix linting issues
echo "🔧 Running ruff linting..."
uv run ruff check --fix
echo "✅ Linting complete"
echo

# Type checking
echo "🔎 Running mypy type checking..."
uv run mypy .
echo "✅ Type checking passed"
echo

# Run tests with coverage
echo "🧪 Running tests with coverage..."
uv run pytest --cov=mlb_watchability --cov-report=term-missing
echo "✅ Tests passed"
echo

echo "🎉 All checks passed! Ready to commit."