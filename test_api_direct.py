#!/usr/bin/env python3
"""Test what we're actually getting from the API."""

import requests
import json

# Make a simple API call
url = "https://api.openalex.org/works"
params = {
    "search": '(police OR "law enforcement") AND (strategic OR strategy)',
    "filter": "is_oa:true",
    "per-page": 200,
    "cursor": "*",
    "mailto": "sdspieg@gmail.com"
}

print("Making API request...")
response = requests.get(url, params=params)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Total results available: {data.get('meta', {}).get('count', 0)}")
    
    results = data.get('results', [])
    print(f"Results in this page: {len(results)}")
    
    # Check what percentage have titles
    with_title = 0
    without_title = 0
    
    for work in results:
        if work and isinstance(work, dict) and (work.get('title') or work.get('display_name')):
            with_title += 1
        else:
            without_title += 1
            print(f"No title: {work.get('id') if work else 'Work is None'}")
    
    print(f"\nResults with title: {with_title}")
    print(f"Results without title: {without_title}")
    print(f"Percentage with titles: {with_title/len(results)*100:.1f}%")
    
    # Show some examples with titles
    print("\nExamples of good results:")
    count = 0
    for work in results:
        if work and (work.get('title') or work.get('display_name')):
            title = work.get('title') or work.get('display_name')
            print(f"- {title[:80]}...")
            count += 1
            if count >= 5:
                break
else:
    print(f"API Error: {response.text}")