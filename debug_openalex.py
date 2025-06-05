#!/usr/bin/env python3
"""Debug script to check OpenAlex API responses."""

import json
from pyalex import Works, config

# Set email
config.email = "sdspieg@gmail.com"

# Test query
query = '(police OR "law enforcement") AND (strategic OR strategy)'
print(f"Testing query: {query}")

# Get a small sample
works_query = Works().search(query).filter(is_oa=True)

# Get first page
print("\nFetching first page of results...")
page_results = list(works_query.paginate(per_page=10, n_max=10))

print(f"\nGot {len(page_results)} pages")

if page_results:
    # Check first page
    first_page = page_results[0]
    print(f"First page has {len(first_page)} items")
    
    # Examine first few items
    for i, work in enumerate(first_page[:3]):
        print(f"\n--- Work {i+1} ---")
        print(f"Type: {type(work)}")
        
        if work is None:
            print("Work is None!")
        elif isinstance(work, dict):
            print(f"Keys: {list(work.keys())[:10]}...")  # First 10 keys
            print(f"Title: {work.get('title', 'NO TITLE')}")
            print(f"ID: {work.get('id', 'NO ID')}")
            print(f"Is OA: {work.get('is_oa', 'NO OA INFO')}")
        else:
            print(f"Unexpected type: {work}")

# Also try direct API call
print("\n\n--- Testing direct API ---")
import requests

url = "https://api.openalex.org/works"
params = {
    "search": query,
    "filter": "is_oa:true",
    "per_page": 5,
    "mailto": "sdspieg@gmail.com"
}

response = requests.get(url, params=params)
print(f"Status code: {response.status_code}")

if response.ok:
    data = response.json()
    print(f"Total results: {data.get('meta', {}).get('count', 'Unknown')}")
    results = data.get('results', [])
    print(f"Got {len(results)} results")
    
    for i, work in enumerate(results[:2]):
        print(f"\n--- Direct API Work {i+1} ---")
        print(f"Title: {work.get('title', 'NO TITLE')}")
        print(f"ID: {work.get('id', 'NO ID')}")
        print(f"Type: {work.get('type', 'NO TYPE')}")