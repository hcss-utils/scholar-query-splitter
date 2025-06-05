#!/usr/bin/env python3
"""
Example script showing how to run the Scholar Query Splitter with GPU optimization.
This example is optimized for RTX 4090 with 90GB RAM.
"""

import subprocess
import sys

def main():
    # Example query
    base_query = '(police OR "law enforcement") AND (strategic OR strategy)'
    
    # Build command with optimal settings for RTX 4090
    cmd = [
        sys.executable, 'main.py',
        base_query,
        '--use-gpu',                    # Enable GPU acceleration
        '--max-results', '2000',        # Fetch more results (you have plenty of RAM)
        '--top-keywords', '50',         # Extract more keywords
        '--top-entities', '50',         # Extract more entities
        '--spacy-model', 'en_core_web_sm',  # Use small model (fast) or en_core_web_lg (better)
        '--output-csv', 'police_strategy_gpu_results.csv',
        '--start-year', '2010',         # Optional: time-based splitting
        '--end-year', '2024'
    ]
    
    print("🚀 Running Scholar Query Splitter with GPU optimization...")
    print(f"📝 Query: {base_query}")
    print(f"🖥️  GPU: Enabled (RTX 4090)")
    print(f"💾 RAM: 90GB available")
    print("-" * 60)
    
    # Run the command
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Completed successfully!")
        print("📊 Check the following files for results:")
        print("   - police_strategy_gpu_results.csv (query results)")
        print("   - police_strategy_gpu_results_analysis.json (analysis)")
        print("   - outputs/keywords_*.json (extracted keywords)")
        print("   - outputs/entities_*.json (extracted entities with types)")
        print("   - outputs/log.txt (detailed log)")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()