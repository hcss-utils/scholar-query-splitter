#!/usr/bin/env python3
"""Debug what's in the API response."""

import requests
import json

# Direct API call
url = "https://api.openalex.org/works"
params = {
    "search": '(police OR "law enforcement") AND (strategic OR strategy)',
    "filter": "is_oa:true,has_fulltext:true",
    "per-page": 10,
    "mailto": "sdspieg@gmail.com"
}

response = requests.get(url, params=params)
data = response.json()

print(f"Response status: {response.status_code}")
print(f"Total count: {data.get('meta', {}).get('count', 0)}")
print(f"Results in page: {len(data.get('results', []))}")

# Check each result
for i, work in enumerate(data.get('results', [])[:5]):
    print(f"\n--- Work {i+1} ---")
    print(f"Has title: {'title' in work}")
    print(f"Title: {work.get('title', 'NO TITLE')}")
    print(f"Display name: {work.get('display_name', 'NO DISPLAY NAME')}")
    print(f"Type: {work.get('type', 'NO TYPE')}")
    print(f"ID: {work.get('id', 'NO ID')}")
    print(f"Keys: {list(work.keys())[:10]}")

# Save full response for inspection
with open('debug_response.json', 'w') as f:
    json.dump(data, f, indent=2)
    
print("\nFull response saved to debug_response.json")