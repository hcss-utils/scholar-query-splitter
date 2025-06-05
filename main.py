#!/usr/bin/env python3
"""
Scholar Query Splitter - Main Orchestrator Script

This script automates the process of splitting large Google Scholar queries
into smaller, manageable subqueries using semantic keyword and entity extraction.
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
from pipeline.query_generation import QueryGenerator
from pipeline.scholar_hits import ScholarHitsCounter


def setup_logging(log_file: str = "outputs/log.txt"):
    """Set up logging configuration."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers to WARNING to reduce noise
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('scholarly').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Split large Google Scholar queries into manageable subqueries"
    )
    
    # Required arguments
    parser.add_argument(
        "base_query",
        help='Base query string (e.g., \'(police OR "law enforcement") AND (strategic OR strategy)\')'
    )
    
    # Optional arguments
    parser.add_argument(
        "--openalex-email",
        help="Email for OpenAlex polite pool (recommended)",
        default=None
    )
    
    parser.add_argument(
        "--max-results",
        type=int,
        default=1000,
        help="Maximum results to fetch from OpenAlex (default: 1000)"
    )
    
    parser.add_argument(
        "--start-year",
        type=int,
        help="Start year for temporal splitting"
    )
    
    parser.add_argument(
        "--end-year",
        type=int,
        help="End year for temporal splitting"
    )
    
    parser.add_argument(
        "--max-queries",
        type=int,
        default=100,
        help="Maximum number of subqueries to generate (default: 100)"
    )
    
    parser.add_argument(
        "--top-keywords",
        type=int,
        default=20,
        help="Number of top keywords to extract (default: 20)"
    )
    
    parser.add_argument(
        "--top-entities",
        type=int,
        default=20,
        help="Number of top entities to extract (default: 20)"
    )
    
    parser.add_argument(
        "--use-proxy",
        action="store_true",
        help="Use proxy for Google Scholar requests"
    )
    
    parser.add_argument(
        "--proxy-type",
        choices=['free', 'luminati', 'scraperapi'],
        default='free',
        help="Type of proxy to use (default: free)"
    )
    
    parser.add_argument(
        "--spacy-model",
        default="en_core_web_sm",
        help="spaCy model to use for NER (default: en_core_web_sm)"
    )
    
    parser.add_argument(
        "--use-gpu",
        action="store_true",
        help="Use GPU acceleration if available (recommended for RTX 4090)"
    )
    
    parser.add_argument(
        "--output-csv",
        default="query_results.csv",
        help="Output CSV file name (default: query_results.csv)"
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
        "--force-regenerate",
        action="store_true",
        help="Force regeneration of keywords/entities even if files exist"
    )
    
    return parser.parse_args()


def main():
    """Main orchestrator function."""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("SCHOLAR QUERY SPLITTER")
    logger.info("=" * 60)
    logger.info(f"Base query: {args.base_query}")
    logger.info(f"Start time: {datetime.now()}")
    
    try:
        # Step 1: Download OpenAlex metadata
        if not args.skip_openalex:
            logger.info("\n--- Step 1: Downloading OpenAlex metadata ---")
            downloader = OpenAlexDownloader(
                email=args.openalex_email or os.getenv('OPENALEX_EMAIL'),
                json_dir="json"
            )
            
            metadata_list = downloader.download_metadata(
                query=args.base_query,
                max_results=args.max_results
            )
            
            # Save metadata file path for reference
            metadata_file = sorted(Path("json").glob("openalex_*.json"))[-1]
            logger.info(f"Metadata saved to: {metadata_file}")
        else:
            # Load existing metadata
            if not args.metadata_file:
                # Find most recent metadata file
                metadata_files = sorted(Path("json").glob("openalex_*.json"))
                if not metadata_files:
                    logger.error("No metadata files found in json/ directory")
                    sys.exit(1)
                metadata_file = metadata_files[-1]
            else:
                metadata_file = Path(args.metadata_file)
            
            logger.info(f"Loading metadata from: {metadata_file}")
            downloader = OpenAlexDownloader(json_dir="json")
            metadata_list = downloader.load_existing_metadata(str(metadata_file))
        
        logger.info(f"Loaded {len(metadata_list)} metadata records")
        
        # Step 2: Extract modifiers
        logger.info("\n--- Step 2: Extracting modifiers ---")
        extractor = ModifierExtractor(
            spacy_model=args.spacy_model,
            use_gpu=args.use_gpu
        )
        
        modifiers = extractor.extract_modifiers(
            metadata_list,
            top_k_keywords=args.top_keywords,
            top_k_entities=args.top_entities,
            force_regenerate=args.force_regenerate
        )
        
        # Filter out modifiers already in base query
        modifiers = extractor.filter_modifiers(modifiers, args.base_query)
        
        logger.info(f"Extracted {len(modifiers['keywords'])} keywords")
        logger.info(f"Extracted {len(modifiers['entities'])} entities")
        
        # Log top modifiers
        logger.info("\nTop Keywords:")
        for keyword, score in modifiers['keywords'][:5]:
            logger.info(f"  - {keyword}: {score:.3f}")
        
        logger.info("\nTop Entities:")
        for item in modifiers['entities'][:5]:
            if len(item) == 3:  # New format with entity type
                entity, ent_type, score = item
                logger.info(f"  - {entity} [{ent_type}]: {score:.3f}")
            else:  # Old format
                entity, score = item
                logger.info(f"  - {entity}: {score:.3f}")
        
        # Step 3: Generate subqueries
        logger.info("\n--- Step 3: Generating subqueries ---")
        generator = QueryGenerator(max_modifier_combinations=2)
        
        queries = generator.generate_subqueries(
            base_query=args.base_query,
            modifiers=modifiers,
            start_year=args.start_year,
            end_year=args.end_year,
            max_queries=args.max_queries
        )
        
        logger.info(f"Generated {len(queries)} subqueries")
        
        # Validate queries
        valid_queries = []
        for query_dict in queries:
            is_valid, error = generator.validate_query(query_dict['query'])
            if is_valid:
                valid_queries.append(query_dict)
            else:
                logger.warning(f"Invalid query skipped: {error}")
        
        logger.info(f"Valid queries: {len(valid_queries)}")
        
        # Step 4: Count Google Scholar hits
        logger.info("\n--- Step 4: Counting Google Scholar hits ---")
        counter = ScholarHitsCounter(
            use_proxy=args.use_proxy,
            proxy_type=args.proxy_type
        )
        
        results_df = counter.count_hits(
            queries=valid_queries,
            save_csv=args.output_csv
        )
        
        # Step 5: Analyze results
        logger.info("\n--- Step 5: Analyzing results ---")
        analysis = counter.analyze_results(results_df)
        
        # Save analysis
        analysis_file = args.output_csv.replace('.csv', '_analysis.json')
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        logger.info(f"Analysis saved to: {analysis_file}")
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("EXECUTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total queries generated: {analysis['total_queries']}")
        logger.info(f"Successful queries: {analysis['successful_queries']}")
        logger.info(f"Failed queries: {analysis['failed_queries']}")
        logger.info(f"Queries with < 1000 hits: {analysis['queries_under_1000']}")
        logger.info(f"Results saved to: {args.output_csv}")
        logger.info(f"End time: {datetime.now()}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()