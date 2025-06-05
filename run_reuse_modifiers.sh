#!/bin/bash
# Demonstrates reusing existing keyword/entity files

echo "🔄 Scholar Query Splitter - Modifier Reuse Demo"
echo "=============================================="
echo ""

# First check if modifier files exist
if ls outputs/keywords_*.json 1> /dev/null 2>&1 && ls outputs/entities_*.json 1> /dev/null 2>&1; then
    echo "✅ Found existing modifier files:"
    echo "   Keywords: $(ls -t outputs/keywords_*.json | head -1)"
    echo "   Entities: $(ls -t outputs/entities_*.json | head -1)"
    echo ""
    echo "🔄 Running WITH reuse (default behavior)..."
    echo ""
    
    # Run without force-regenerate (will reuse)
    python main_exhaustive.py '(police OR "law enforcement") AND (strategic OR strategy)' \
        --start-year 2023 \
        --end-year 2023 \
        --use-gpu \
        --skip-openalex \
        --use-proxy \
        --proxy-type scraperapi
    
    echo ""
    echo "💡 To force regeneration, add: --force-regenerate"
    
else
    echo "⚠️  No existing modifier files found."
    echo "   First run will generate them."
    echo ""
    
    # First run to generate modifiers
    python main.py '(police OR "law enforcement") AND (strategic OR strategy)' \
        --use-gpu \
        --max-results 1000 \
        --top-keywords 50 \
        --top-entities 50
fi

echo ""
echo "✅ Complete!"