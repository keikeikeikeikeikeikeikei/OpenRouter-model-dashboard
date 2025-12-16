#!/bin/bash
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Starting OpenRouter Pricing Update..."

# 1. Fetch ALL data
echo "📥 Fetching and consolidating data..."
uv run python scripts/fetch.py

# 2. Generate Dashboard
echo "📊 Generating Main Dashboard..."
uv run python scripts/build.py

echo "✅ Update Complete! Open docs/index.html to view."
