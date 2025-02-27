#!/bin/bash
# Script to run tests locally before pushing to GitHub

echo "Running basic tests..."
pytest tests/test_basic.py -v

if [ $? -eq 0 ]; then
    echo "✅ Tests passed! You can safely push your changes."
else
    echo "❌ Tests failed. Please fix the issues before pushing."
    exit 1
fi
