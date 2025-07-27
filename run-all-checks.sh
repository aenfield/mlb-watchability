#!/bin/bash

# Pre-commit check script for MLB Watchability
# Run all quality checks before committing
# Usage: ./run-all-checks.sh [--include-costly]

set -e  # Exit on any error

# Parse command line arguments
INCLUDE_COSTLY=false
if [ "$1" = "--include-costly" ]; then
    INCLUDE_COSTLY=true
fi

echo "🔍 Running pre-commit checks..."
if [ "$INCLUDE_COSTLY" = true ]; then
    echo "   (including costly tests)"
fi
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
if [ "$INCLUDE_COSTLY" = true ]; then
    echo "🧪 Running all tests (including costly) with coverage..."
    uv run pytest -m "" --cov=mlb_watchability --cov-report=term-missing
else
    echo "🧪 Running normal tests with coverage..."
    uv run pytest --cov=mlb_watchability --cov-report=term-missing
fi
echo "✅ Tests passed"
echo

echo "🎉 All checks passed! Ready to commit."