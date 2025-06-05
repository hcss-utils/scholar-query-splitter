#!/usr/bin/env python3
"""Test full run with detailed debugging."""

import sys
sys.path.insert(0, '.')

from pipeline.openalex_direct import OpenAlexDownloader
import logging

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# But set requests to WARNING to reduce noise
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

print("Starting test run...")
downloader = OpenAlexDownloader(email='sdspieg@gmail.com')

# Download just 500 to see what happens
results = downloader.download_metadata(
    '(police OR "law enforcement") AND (strategic OR strategy)', 
    max_results=500
)

print(f"\nFinal results: {len(results)}")
print(f"All have titles: {all(r.get('title') for r in results)}")

# Check the saved file
import json
import glob
latest_file = sorted(glob.glob('json/openalex_*.json'))[-1]
with open(latest_file) as f:
    saved_data = json.load(f)
    print(f"\nSaved file has {saved_data['total_results']} results")
    print(f"Query was: {saved_data['query']}")