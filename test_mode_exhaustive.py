#!/usr/bin/env python3
"""
Test mode for exhaustive splitter - simulates Google Scholar results to avoid rate limits.
Use this to test the splitting algorithm without hitting the API.
"""

import subprocess
import sys
import os

def main():
    # Set environment variable to use simulation mode
    os.environ['SIMULATE_SCHOLAR'] = '1'
    
    base_query = '(police OR "law enforcement") AND (strategic OR strategy)'
    
    cmd = [
        sys.executable, 'main_exhaustive.py',
        base_query,
        '--start-year', '2023',
        '--end-year', '2023',
        '--max-metadata', '500',
        '--top-keywords', '50',
        '--top-entities', '50',
        '--target-size', '900',
        '--use-gpu',
        '--skip-openalex'  # Use existing metadata if available
    ]
    
    print("🧪 Running Exhaustive Splitter in TEST MODE")
    print("📊 This simulates Google Scholar results to avoid rate limits")
    print(f"📝 Query: {base_query}")
    print("-" * 60)
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Test completed!")
        print("\n⚠️  Note: Hit counts are SIMULATED, not real Google Scholar data")
        print("📋 Use the generated query structure for real runs with ScraperAPI")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()