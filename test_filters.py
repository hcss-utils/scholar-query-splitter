#!/usr/bin/env python3
"""Test different filter combinations."""

import requests

base_url = "https://api.openalex.org/works"
query = '(police OR "law enforcement") AND (strategic OR strategy)'

filters = [
    "is_oa:true",
    "is_oa:true,has_fulltext:true", 
    None
]

for filter_str in filters:
    params = {
        "search": query,
        "per-page": 1,
        "mailto": "sdspieg@gmail.com"
    }
    if filter_str:
        params["filter"] = filter_str
    
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        count = data.get('meta', {}).get('count', 0)
        print(f"Filter '{filter_str}': {count:,} results")
    else:
        print(f"Filter '{filter_str}': ERROR {response.status_code}")