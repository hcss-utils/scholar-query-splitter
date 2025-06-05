#!/usr/bin/env python3
"""
Run Scholar Query Splitter for all years with no maximum limit.
Configured for sdspieg@gmail.com
"""

import subprocess
import sys

def main():
    """Run the scholar query splitter with specific configuration."""
    
    # Base query
    base_query = '(police OR "law enforcement") AND (strategic OR strategy)'
    
    # Command with all parameters
    cmd = [
        sys.executable,
        'main.py',
        base_query,
        '--openalex-email', 'sdspieg@gmail.com',
        '--max-results', '10000',  # High limit to get all available results
        '--max-queries', '200',     # Generate many subqueries for comprehensive coverage
        '--top-keywords', '30',     # Extract more keywords for better coverage
        '--top-entities', '30',     # Extract more entities
        '--output-csv', 'police_strategy_all_years_results.csv'
    ]
    
    print("Starting Scholar Query Splitter with configuration:")
    print(f"  Email: sdspieg@gmail.com")
    print(f"  Max Results: 10,000 (no practical limit)")
    print(f"  Year Range: All years")
    print(f"  Base Query: {base_query}")
    print("-" * 60)
    
    # Run the command
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(1)

if __name__ == "__main__":
    main()