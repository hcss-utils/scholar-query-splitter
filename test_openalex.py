#!/usr/bin/env python3
"""
Test OpenAlex API to debug query issues
"""

import requests
import json
from datetime import datetime

def test_openalex_query():
    """Test different query formats to see what works"""
    
    base_url = "https://api.openalex.org/works"
    email = "sdspieg@gmail.com"  # Your email from .env
    
    # Test queries
    queries = [
        {
            "name": "Basic query without year",
            "params": {
                "search": '(police OR "law enforcement") AND (strategic OR strategy)',
                "mailto": email,
                "per-page": 10
            }
        },
        {
            "name": "Query with year filter",
            "params": {
                "search": '(police OR "law enforcement") AND (strategic OR strategy)',
                "filter": "from_publication_date:2020-01-01,to_publication_date:2024-12-31",
                "mailto": email,
                "per-page": 10
            }
        },
        {
            "name": "Simpler query",
            "params": {
                "search": 'police strategic',
                "filter": "from_publication_date:2020-01-01,to_publication_date:2024-12-31",
                "mailto": email,
                "per-page": 10
            }
        },
        {
            "name": "Query with default_search",
            "params": {
                "default_search": 'police law enforcement strategic strategy',
                "filter": "from_publication_date:2020-01-01,to_publication_date:2024-12-31",
                "mailto": email,
                "per-page": 10
            }
        }
    ]
    
    print("Testing OpenAlex API queries...")
    print("=" * 60)
    
    for test in queries:
        print(f"\nTest: {test['name']}")
        print(f"Params: {json.dumps(test['params'], indent=2)}")
        
        try:
            response = requests.get(base_url, params=test['params'])
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                count = data.get('meta', {}).get('count', 0)
                print(f"Results found: {count}")
                
                if count > 0 and 'results' in data and data['results']:
                    print(f"First result:")
                    first = data['results'][0]
                    print(f"  Title: {first.get('title', 'N/A')}")
                    print(f"  Year: {first.get('publication_year', 'N/A')}")
            else:
                print(f"Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"Exception: {e}")
        
        print("-" * 40)

if __name__ == "__main__":
    test_openalex_query()