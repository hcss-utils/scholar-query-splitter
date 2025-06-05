#!/usr/bin/env python3
"""
Quick test script to verify the system works without counting all results.
"""

import subprocess
import sys

def main():
    """Run a quick test of the scholar query splitter."""
    
    # Base query
    base_query = '(police OR "law enforcement") AND (strategic OR strategy)'
    
    # Command for quick test - skip counting all results
    cmd = [
        sys.executable,
        'main.py',
        base_query,
        '--openalex-email', 'sdspieg@gmail.com',
        '--max-results', '500',     # Get more metadata for better modifier extraction
        '--max-queries', '50',      # Generate 50 subqueries
        '--top-keywords', '30',     
        '--top-entities', '30',     
        '--output-csv', 'quick_test_results.csv',
        '--skip-openalex'  # Use existing metadata if available
    ]
    
    print("Running quick test of Scholar Query Splitter")
    print(f"  Base Query: {base_query}")
    print("  This test will generate subqueries but won't count all results")
    print("-" * 60)
    
    # Run the command
    try:
        subprocess.run(cmd, check=True)
        print("\nTest completed! Check quick_test_results.csv for results.")
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)

if __name__ == "__main__":
    main()