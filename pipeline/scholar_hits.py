"""
Google Scholar hits counter module.

This module uses the scholarly library to count the number of hits
for each generated query.
"""

import logging
import time
from typing import Dict, List, Any, Optional
import random
from datetime import datetime

from scholarly import scholarly, ProxyGenerator
from tqdm import tqdm
import pandas as pd

logger = logging.getLogger(__name__)


class ScholarHitsCounter:
    """Counts Google Scholar hits for queries using the scholarly library."""
    
    def __init__(self, use_proxy: bool = False, proxy_type: str = 'free'):
        """
        Initialize the Scholar hits counter.
        
        Args:
            use_proxy: Whether to use proxy for requests
            proxy_type: Type of proxy ('free', 'luminati', 'scraperapi')
        """
        self.use_proxy = use_proxy
        self.proxy_type = proxy_type
        
        if use_proxy:
            self._setup_proxy()
        
        # Rate limiting parameters
        self.min_delay = 5  # Minimum seconds between requests
        self.max_delay = 15  # Maximum seconds between requests
        self.error_delay = 60  # Delay after error
        
        # Results storage
        self.results = []
    
    def _setup_proxy(self):
        """Set up proxy for scholarly requests."""
        pg = ProxyGenerator()
        
        try:
            if self.proxy_type == 'free':
                logger.info("Setting up free proxy...")
                success = pg.FreeProxies()
            elif self.proxy_type == 'luminati':
                logger.info("Setting up Luminati proxy...")
                # Note: Requires credentials
                success = pg.Luminati(usr='', passwd='', proxy_port='')
            elif self.proxy_type == 'scraperapi':
                logger.info("Setting up ScraperAPI proxy...")
                # Note: Requires API key
                success = pg.ScraperAPI('')
            else:
                logger.warning(f"Unknown proxy type: {self.proxy_type}")
                return
            
            if success:
                scholarly.use_proxy(pg)
                logger.info("Proxy setup successful")
            else:
                logger.warning("Proxy setup failed")
                
        except Exception as e:
            logger.error(f"Error setting up proxy: {e}")
    
    def count_hits(self, queries: List[Dict[str, Any]], 
                   save_csv: str = "query_results.csv") -> pd.DataFrame:
        """
        Count hits for a list of queries.
        
        Args:
            queries: List of query dictionaries
            save_csv: Path to save results CSV
            
        Returns:
            DataFrame with results
        """
        logger.info(f"Counting hits for {len(queries)} queries")
        
        # Reset results
        self.results = []
        
        # Process queries with progress bar
        for i, query_dict in enumerate(tqdm(queries, desc="Counting hits")):
            result = self._count_single_query(query_dict, i)
            self.results.append(result)
            
            # Save intermediate results
            if (i + 1) % 10 == 0:
                self._save_results(save_csv)
            
            # Rate limiting
            if i < len(queries) - 1:
                delay = random.uniform(self.min_delay, self.max_delay)
                time.sleep(delay)
        
        # Save final results
        df = self._save_results(save_csv)
        
        # Log summary statistics
        self._log_summary(df)
        
        return df
    
    def _count_single_query(self, query_dict: Dict[str, Any], 
                           index: int) -> Dict[str, Any]:
        """
        Count hits for a single query.
        
        Args:
            query_dict: Query dictionary
            index: Query index
            
        Returns:
            Result dictionary
        """
        query_string = query_dict['query']
        
        result = {
            'index': index,
            'query': query_string,
            'base_query': query_dict.get('base_query', ''),
            'modifiers': ', '.join([m['text'] for m in query_dict.get('modifiers', [])]),
            'modifier_count': query_dict.get('modifier_count', 0),
            'year_range': str(query_dict.get('year_range', '')),
            'hit_count': 0,
            'status': 'pending',
            'error': None,
            'timestamp': datetime.now().isoformat()
        }
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Perform search
                search_query = scholarly.search_pubs(query_string)
                
                # Get total results count
                # Note: scholarly doesn't directly provide total count,
                # so we need to access the first result and check
                first_result = next(search_query, None)
                
                if first_result:
                    # Try to get total results from the search
                    # This is a workaround as scholarly doesn't expose total directly
                    total_results = self._estimate_total_results(query_string)
                    result['hit_count'] = total_results
                else:
                    total_results = 0
                    result['hit_count'] = 0
                
                result['status'] = 'success'
                logger.debug(f"Query {index}: {total_results} hits")
                break
                
            except StopIteration:
                # No results found
                result['hit_count'] = 0
                result['status'] = 'success'
                break
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                logger.warning(f"Error on query {index} (attempt {retry_count}): {error_msg}")
                
                if retry_count >= max_retries:
                    result['status'] = 'error'
                    result['error'] = error_msg
                else:
                    time.sleep(self.error_delay)
        
        return result
    
    def _estimate_total_results(self, query: str) -> int:
        """
        Estimate total results for a query.
        
        Since scholarly doesn't directly provide total count,
        this is a workaround that may need adjustment.
        
        Args:
            query: Query string
            
        Returns:
            Estimated total results
        """
        try:
            # Perform a new search to count results
            search_query = scholarly.search_pubs(query)
            
            # Count up to 1000 results (Google Scholar limit)
            count = 0
            for _ in search_query:
                count += 1
                if count >= 1000:
                    # Assume there are more than 1000
                    return 1000
            
            return count
            
        except Exception as e:
            logger.error(f"Error estimating results: {e}")
            return 0
    
    def _save_results(self, filepath: str) -> pd.DataFrame:
        """
        Save results to CSV file.
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            Results DataFrame
        """
        df = pd.DataFrame(self.results)
        
        # Sort by index
        df = df.sort_values('index')
        
        # Save to CSV
        df.to_csv(filepath, index=False)
        logger.info(f"Saved {len(df)} results to {filepath}")
        
        return df
    
    def _log_summary(self, df: pd.DataFrame):
        """
        Log summary statistics of the results.
        
        Args:
            df: Results DataFrame
        """
        total_queries = len(df)
        successful = len(df[df['status'] == 'success'])
        errors = len(df[df['status'] == 'error'])
        
        logger.info("=" * 50)
        logger.info("SUMMARY STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Total queries: {total_queries}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Errors: {errors}")
        
        if successful > 0:
            hit_counts = df[df['status'] == 'success']['hit_count']
            logger.info(f"Average hits: {hit_counts.mean():.1f}")
            logger.info(f"Median hits: {hit_counts.median():.1f}")
            logger.info(f"Min hits: {hit_counts.min()}")
            logger.info(f"Max hits: {hit_counts.max()}")
            
            # Queries with manageable hits (< 1000)
            manageable = len(df[(df['status'] == 'success') & (df['hit_count'] < 1000)])
            logger.info(f"Queries with < 1000 hits: {manageable}")
        
        logger.info("=" * 50)
    
    def analyze_results(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze query results to find optimal splitting strategy.
        
        Args:
            df: Results DataFrame
            
        Returns:
            Analysis dictionary
        """
        analysis = {
            'total_queries': len(df),
            'successful_queries': len(df[df['status'] == 'success']),
            'failed_queries': len(df[df['status'] == 'error']),
            'queries_under_1000': len(df[(df['status'] == 'success') & (df['hit_count'] < 1000)]),
            'best_modifiers': [],
            'best_year_ranges': []
        }
        
        # Find best performing modifiers
        if 'modifiers' in df.columns:
            modifier_performance = []
            for modifier in df['modifiers'].unique():
                if modifier and modifier != '':
                    queries_with_modifier = df[df['modifiers'] == modifier]
                    avg_hits = queries_with_modifier['hit_count'].mean()
                    under_1000 = len(queries_with_modifier[queries_with_modifier['hit_count'] < 1000])
                    modifier_performance.append({
                        'modifier': modifier,
                        'avg_hits': avg_hits,
                        'queries_under_1000': under_1000
                    })
            
            # Sort by queries under 1000 (descending)
            modifier_performance.sort(key=lambda x: x['queries_under_1000'], reverse=True)
            analysis['best_modifiers'] = modifier_performance[:10]
        
        # Find best year ranges
        if 'year_range' in df.columns:
            year_performance = []
            for year_range in df['year_range'].unique():
                if year_range and year_range != '':
                    queries_with_year = df[df['year_range'] == year_range]
                    avg_hits = queries_with_year['hit_count'].mean()
                    under_1000 = len(queries_with_year[queries_with_year['hit_count'] < 1000])
                    year_performance.append({
                        'year_range': year_range,
                        'avg_hits': avg_hits,
                        'queries_under_1000': under_1000
                    })
            
            year_performance.sort(key=lambda x: x['queries_under_1000'], reverse=True)
            analysis['best_year_ranges'] = year_performance[:10]
        
        return analysis