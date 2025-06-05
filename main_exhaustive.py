#!/usr/bin/env python3
"""
Scholar Query Splitter - Exhaustive Coverage Mode

This script ensures complete coverage by splitting large queries into
manageable chunks (<1000 hits each) using systematic decomposition.
"""

import argparse
import logging
import os
import sys
from datetime import datetime
import json
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# Import pipeline modules
from pipeline.openalex_direct import OpenAlexDownloader
from pipeline.modifier_extraction import ModifierExtractor
from pipeline.exhaustive_splitter import ExhaustiveQuerySplitter
from pipeline.scholar_hits import ScholarHitsCounter


def setup_logging(log_file: str = "outputs/exhaustive_log.txt"):
    """Set up logging configuration."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    os.makedirs("outputs/exhaustive", exist_ok=True)  # Ensure exhaustive output dir exists
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('scholarly').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Split large Google Scholar queries for complete coverage"
    )
    
    # Required arguments
    parser.add_argument(
        "base_query",
        help='Base query string (e.g., \'(police OR "law enforcement") AND (strategic OR strategy)\')'
    )
    
    # Year range (highly recommended for exhaustive splitting)
    parser.add_argument(
        "--start-year",
        type=int,
        required=True,
        help="Start year (REQUIRED for exhaustive splitting)"
    )
    
    parser.add_argument(
        "--end-year",
        type=int,
        required=True,
        help="End year (REQUIRED for exhaustive splitting)"
    )
    
    # Optional arguments
    parser.add_argument(
        "--target-size",
        type=int,
        default=900,
        help="Target maximum hits per query (default: 900)"
    )
    
    parser.add_argument(
        "--openalex-email",
        help="Email for OpenAlex polite pool",
        default=None
    )
    
    parser.add_argument(
        "--max-metadata",
        type=int,
        default=5000,
        help="Maximum metadata to fetch from OpenAlex (default: 5000)"
    )
    
    parser.add_argument(
        "--top-keywords",
        type=int,
        default=100,
        help="Number of keywords to extract (default: 100)"
    )
    
    parser.add_argument(
        "--top-entities",
        type=int,
        default=100,
        help="Number of entities to extract (default: 100)"
    )
    
    parser.add_argument(
        "--use-gpu",
        action="store_true",
        help="Use GPU acceleration if available"
    )
    
    parser.add_argument(
        "--spacy-model",
        default="en_core_web_sm",
        help="spaCy model to use (default: en_core_web_sm)"
    )
    
    parser.add_argument(
        "--skip-openalex",
        action="store_true",
        help="Skip OpenAlex download and use existing metadata"
    )
    
    parser.add_argument(
        "--metadata-file",
        help="Path to existing OpenAlex metadata JSON file"
    )
    
    parser.add_argument(
        "--use-proxy",
        action="store_true",
        help="Use proxy for Google Scholar requests"
    )
    
    parser.add_argument(
        "--proxy-type",
        choices=['free', 'luminati', 'scraperapi'],
        default='scraperapi',
        help="Type of proxy to use (default: scraperapi)"
    )
    
    return parser.parse_args()


def main():
    """Main orchestrator for exhaustive splitting."""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("SCHOLAR QUERY SPLITTER - EXHAUSTIVE MODE")
    logger.info("=" * 60)
    logger.info(f"Base query: {args.base_query}")
    logger.info(f"Year range: {args.start_year} - {args.end_year}")
    logger.info(f"Target size: < {args.target_size} hits per query")
    logger.info(f"Start time: {datetime.now()}")
    
    try:
        # Step 1: Download OpenAlex metadata for the full year range
        if not args.skip_openalex:
            logger.info("\n--- Step 1: Downloading OpenAlex metadata ---")
            
            # Create OpenAlex query with proper filter syntax
            year_query = args.base_query
            
            downloader = OpenAlexDownloader(
                email=args.openalex_email or os.getenv('OPENALEX_EMAIL'),
                json_dir="json"
            )
            
            metadata_list = downloader.download_metadata(
                query=year_query,
                max_results=args.max_metadata,
                year_range=(args.start_year, args.end_year)
            )
            
            metadata_file = sorted(Path("json").glob("openalex_*.json"))[-1]
            logger.info(f"Metadata saved to: {metadata_file}")
        else:
            # Load existing metadata
            if not args.metadata_file:
                metadata_files = sorted(Path("json").glob("openalex_*.json"))
                if not metadata_files:
                    logger.error("No metadata files found")
                    sys.exit(1)
                metadata_file = metadata_files[-1]
            else:
                metadata_file = Path(args.metadata_file)
            
            logger.info(f"Loading metadata from: {metadata_file}")
            downloader = OpenAlexDownloader(json_dir="json")
            metadata_list = downloader.load_existing_metadata(str(metadata_file))
        
        logger.info(f"Loaded {len(metadata_list)} metadata records")
        
        # Step 2: Extract modifiers (uni/bi-grams only)
        logger.info("\n--- Step 2: Extracting modifiers (uni/bi-grams) ---")
        extractor = ModifierExtractor(
            spacy_model=args.spacy_model,
            use_gpu=args.use_gpu
        )
        
        modifiers = extractor.extract_modifiers(
            metadata_list,
            top_k_keywords=args.top_keywords,
            top_k_entities=args.top_entities
        )
        
        # Filter out modifiers already in base query
        modifiers = extractor.filter_modifiers(modifiers, args.base_query)
        
        logger.info(f"Extracted {len(modifiers['keywords'])} keywords")
        logger.info(f"Extracted {len(modifiers['entities'])} entities")
        
        # Step 3: Initialize Google Scholar counter
        logger.info("\n--- Step 3: Initializing Google Scholar counter ---")
        counter = ScholarHitsCounter(
            use_proxy=args.use_proxy,
            proxy_type=args.proxy_type
        )
        
        # Step 4: Perform exhaustive splitting
        logger.info("\n--- Step 4: Performing exhaustive query splitting ---")
        splitter = ExhaustiveQuerySplitter(
            scholar_counter=counter,
            target_size=args.target_size
        )
        
        # Process each year separately for better control
        all_results = []
        for year in range(args.start_year, args.end_year + 1):
            logger.info(f"\n📅 Processing year {year}...")
            
            year_results = splitter.split_exhaustively(
                base_query=args.base_query,
                modifiers=modifiers,
                year_range=(year, year),
                output_dir="outputs/exhaustive"
            )
            
            all_results.append({
                'year': year,
                'results': year_results
            })
            
            # Save intermediate results
            intermediate_file = f"outputs/exhaustive/year_{year}_results.json"
            with open(intermediate_file, 'w') as f:
                json.dump(year_results, f, indent=2)
        
        # Step 5: Generate final report
        logger.info("\n--- Step 5: Generating final coverage report ---")
        
        total_queries = sum(len(r['results']['final_queries']) for r in all_results if 'final_queries' in r['results'])
        total_coverage = sum(r['results']['coverage_stats']['total_coverage'] for r in all_results if 'coverage_stats' in r['results'])
        
        final_report = {
            'timestamp': datetime.now().isoformat(),
            'base_query': args.base_query,
            'year_range': f"{args.start_year}-{args.end_year}",
            'target_size': args.target_size,
            'total_queries_generated': total_queries,
            'total_coverage': total_coverage,
            'yearly_results': all_results
        }
        
        report_file = f"outputs/exhaustive/final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        # Generate CSV for easy import
        csv_data = []
        for year_data in all_results:
            year = year_data['year']
            if 'final_queries' in year_data['results']:
                for query in year_data['results']['final_queries']:
                    csv_data.append({
                        'year': year,
                        'query_id': query['id'],
                        'query': query['query'],
                        'modifiers': '|'.join(query['modifiers']),
                        'type': query['type'],
                        'hits': query['actual_hits']
                    })
        
        csv_file = f"outputs/exhaustive/all_queries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        pd.DataFrame(csv_data).to_csv(csv_file, index=False)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("EXHAUSTIVE SPLITTING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total queries generated: {total_queries}")
        logger.info(f"Total coverage: {total_coverage:,} hits")
        logger.info(f"Final report: {report_file}")
        logger.info(f"Query CSV: {csv_file}")
        logger.info(f"End time: {datetime.now()}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()