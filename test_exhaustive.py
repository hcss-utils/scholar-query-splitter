#!/usr/bin/env python3
"""
Test script for exhaustive mode - demonstrates the concept without heavy API usage.
"""

import subprocess
import sys

def main():
    # Test with a single year first
    base_query = '(police OR "law enforcement") AND (strategic OR strategy)'
    
    cmd = [
        sys.executable, 'main_exhaustive.py',
        base_query,
        '--start-year', '2023',
        '--end-year', '2023',      # Just one year for testing
        '--max-metadata', '500',    # Less metadata for faster testing
        '--top-keywords', '50',     # Fewer keywords
        '--top-entities', '50',     # Fewer entities
        '--target-size', '500',     # Smaller chunks
        '--use-gpu'
    ]
    
    print("🧪 Running Scholar Query Splitter - Exhaustive Mode (Test)")
    print(f"📝 Query: {base_query}")
    print(f"📅 Year: 2023 only (for testing)")
    print(f"🎯 Target: < 500 hits per chunk")
    print("-" * 60)
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Test completed!")
        print("\n📊 Check these files:")
        print("   - outputs/exhaustive/year_2023_results.json")
        print("   - outputs/exhaustive/coverage_map_*.json")
        print("   - outputs/exhaustive/exhaustive_split_*.json")
        print("\n💡 If this worked, run the full version with:")
        print("   python main_exhaustive.py 'your query' --start-year 2020 --end-year 2024 --use-gpu")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()