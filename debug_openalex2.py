#!/usr/bin/env python3
"""Debug script to check proper pyalex usage."""

from pyalex import Works, config
import json

# Set email
config.email = "sdspieg@gmail.com"

# Test query
query = '(police OR "law enforcement") AND (strategic OR strategy)'

# Get works with filter
works = Works().search(query).filter(is_oa=True).get()

print(f"Got {len(works)} works")

# Check first work
if works:
    first_work = works[0]
    print(f"\nFirst work type: {type(first_work)}")
    
    # Try different ways to access data
    print("\nTrying different access methods:")
    
    # Method 1: Direct attribute access
    try:
        print(f"1. Direct: Title = {first_work.title}")
    except:
        print("1. Direct access failed")
    
    # Method 2: Dictionary access
    try:
        print(f"2. Dict: Title = {first_work['title']}")
    except:
        print("2. Dict access failed")
    
    # Method 3: Check what attributes/methods are available
    print(f"\n3. Available attributes: {[attr for attr in dir(first_work) if not attr.startswith('_')][:10]}")
    
    # Try to convert to dict
    try:
        if hasattr(first_work, 'to_dict'):
            work_dict = first_work.to_dict()
            print(f"\n4. to_dict() worked! Keys: {list(work_dict.keys())[:5]}")
        elif hasattr(first_work, '__dict__'):
            work_dict = first_work.__dict__
            print(f"\n4. __dict__ worked! Keys: {list(work_dict.keys())[:5]}")
    except Exception as e:
        print(f"\n4. Conversion failed: {e}")

# Alternative: Use paginate with smaller batches
print("\n\nTesting paginate method:")
for i, page in enumerate(Works().search(query).filter(is_oa=True).paginate(per_page=2, n_max=4)):
    print(f"\nPage {i+1}: {len(page)} items")
    if page:
        first = page[0]
        print(f"  Type: {type(first)}")
        if hasattr(first, 'title'):
            print(f"  Title: {first.title}")
        elif isinstance(first, dict):
            print(f"  Title: {first.get('title', 'NO TITLE')}")