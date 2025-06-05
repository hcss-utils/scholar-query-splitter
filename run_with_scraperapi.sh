#!/bin/bash
# Run exhaustive mode with ScraperAPI already configured in .env

echo "🚀 Running with ScraperAPI proxy..."
echo "📋 Checking environment..."

# Source the .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Loaded .env file"
    echo "✅ SCRAPERAPI_KEY: ${SCRAPERAPI_KEY:0:8}..."
else
    echo "❌ No .env file found!"
    exit 1
fi

# Run the exhaustive mode with proxy
echo ""
echo "🔄 Starting exhaustive query splitting..."
echo ""

python main_exhaustive.py '(police OR "law enforcement") AND (strategic OR strategy)' \
    --start-year 2023 \
    --end-year 2023 \
    --max-metadata 1000 \
    --top-keywords 50 \
    --top-entities 50 \
    --use-gpu \
    --use-proxy \
    --proxy-type scraperapi

echo ""
echo "✅ Complete! Check outputs/exhaustive/ for results."