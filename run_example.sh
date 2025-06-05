#!/bin/bash
# Example usage script for Scholar Query Splitter
# This script runs the query splitter with all years and no result limit

# Run with your specific requirements
python main.py '(police OR "law enforcement") AND (strategic OR strategy)' \
    --openalex-email sdspieg@gmail.com \
    --max-results 10000 \
    --max-queries 200 \
    --top-keywords 30 \
    --top-entities 30 \
    --output-csv police_strategy_results.csv