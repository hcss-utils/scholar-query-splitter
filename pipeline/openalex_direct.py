"""
OpenAlex metadata downloader using direct REST API.

This module handles downloading open access full-text metadata from OpenAlex
using direct REST API calls instead of the pyalex wrapper.
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)


class OpenAlexDownloader:
    """Downloads metadata from OpenAlex API using direct REST calls."""
    
    def __init__(self, email: Optional[str] = None, json_dir: str = "json"):
        """
        Initialize the OpenAlex downloader.
        
        Args:
            email: Email for polite pool access (recommended)
            json_dir: Directory to save JSON files
        """
        self.json_dir = json_dir
        os.makedirs(json_dir, exist_ok=True)
        
        self.base_url = "https://api.openalex.org/works"
        self.email = email
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Scholar-Query-Splitter/1.0'
        })
    
    def download_metadata(self, query: str, max_results: int = 1000, 
                         per_page: int = 200) -> List[Dict[str, Any]]:
        """
        Download metadata from OpenAlex for a given query.
        
        Args:
            query: The search query
            max_results: Maximum number of results to fetch
            per_page: Results per page (max 200)
            
        Returns:
            List of work metadata dictionaries
        """
        logger.info(f"Starting OpenAlex download for query: {query}")
        
        all_results = []
        cursor = "*"  # Start cursor
        
        # Parameters for the API
        params = {
            "search": query,
            "filter": "is_oa:true,has_fulltext:true",
            "per-page": per_page,
            "cursor": cursor
        }
        
        # Add email if provided (for polite pool)
        if self.email:
            params["mailto"] = self.email
        
        # Create progress bar
        pbar = tqdm(total=max_results, desc="Downloading metadata", unit="works")
        
        try:
            while len(all_results) < max_results:
                # Make API request
                response = self.session.get(self.base_url, params=params)
                
                if response.status_code != 200:
                    logger.error(f"API request failed: {response.status_code} - {response.text}")
                    break
                
                data = response.json()
                
                # Extract results
                results = data.get('results', [])
                if not results:
                    logger.info("No more results available")
                    break
                
                # Process each work
                for work in results:
                    if work is None:
                        logger.debug("Skipping None work")
                        continue
                        
                    metadata = self._extract_metadata(work)
                    if metadata:
                        all_results.append(metadata)
                        pbar.update(1)
                        
                        if len(all_results) >= max_results:
                            break
                
                # Get next cursor
                meta = data.get('meta', {})
                next_cursor = meta.get('next_cursor')
                
                if not next_cursor:
                    logger.info("No more pages available")
                    break
                
                params['cursor'] = next_cursor
                
                # Be polite to the API
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error downloading metadata: {e}")
            raise
        finally:
            pbar.close()
        
        # Trim to exact max_results if we got more
        all_results = all_results[:max_results]
        
        # Save results to JSON
        self._save_results(all_results, query)
        
        logger.info(f"Downloaded {len(all_results)} results")
        return all_results
    
    def _extract_metadata(self, work: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract relevant metadata from an OpenAlex work object.
        
        Args:
            work: OpenAlex work object (dictionary)
            
        Returns:
            Extracted metadata dictionary or None if essential fields missing
        """
        try:
            # Check if work is valid
            if not work or not isinstance(work, dict):
                return None
                
            # Extract basic metadata
            metadata = {
                'id': work.get('id', ''),
                'doi': work.get('doi', ''),
                'title': work.get('title', '') or work.get('display_name', ''),
                'publication_year': work.get('publication_year'),
                'publication_date': work.get('publication_date'),
                'type': work.get('type', ''),
                'is_oa': work.get('is_oa', False),
                'cited_by_count': work.get('cited_by_count', 0),
                'has_fulltext': work.get('has_fulltext', False),
            }
            
            # Extract abstract if available
            abstract_inverted_index = work.get('abstract_inverted_index')
            if abstract_inverted_index:
                metadata['abstract'] = self._reconstruct_abstract(abstract_inverted_index)
            else:
                metadata['abstract'] = ''
            
            # Extract authors
            authors = []
            for authorship in work.get('authorships', []):
                author = authorship.get('author', {})
                authors.append({
                    'name': author.get('display_name', ''),
                    'orcid': author.get('orcid', '')
                })
            metadata['authors'] = authors
            
            # Extract concepts/keywords
            concepts = []
            for concept in work.get('concepts', []):
                concepts.append({
                    'display_name': concept.get('display_name', ''),
                    'score': concept.get('score', 0)
                })
            metadata['concepts'] = concepts
            
            # Extract venue information
            primary_location = work.get('primary_location', {})
            source = primary_location.get('source', {})
            metadata['venue'] = {
                'display_name': source.get('display_name', ''),
                'type': source.get('type', ''),
                'issn': source.get('issn_l', '')
            }
            
            # Extract open access URL if available
            metadata['oa_url'] = work.get('open_access', {}).get('oa_url', '')
            
            # Only return if we have at least a title
            if metadata['title']:
                return metadata
            else:
                return None
                
        except Exception as e:
            logger.debug(f"Error extracting metadata: {e}")
            # Only log details if it's not a simple missing field
            if "NoneType" not in str(e):
                logger.warning(f"Unexpected error extracting metadata: {e}")
            return None
    
    def _reconstruct_abstract(self, inverted_index: Dict[str, List[int]]) -> str:
        """
        Reconstruct abstract from OpenAlex inverted index format.
        
        Args:
            inverted_index: Dictionary mapping words to positions
            
        Returns:
            Reconstructed abstract text
        """
        if not inverted_index:
            return ""
        
        # Create position to word mapping
        position_word = []
        for word, positions in inverted_index.items():
            for pos in positions:
                position_word.append((pos, word))
        
        # Sort by position and reconstruct
        position_word.sort()
        abstract = ' '.join(word for _, word in position_word)
        
        return abstract
    
    def _save_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """
        Save results to a JSON file.
        
        Args:
            results: List of metadata dictionaries
            query: The original query
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"openalex_{timestamp}_{len(results)}_results.json"
        filepath = os.path.join(self.json_dir, filename)
        
        output_data = {
            'query': query,
            'timestamp': timestamp,
            'total_results': len(results),
            'results': results
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved results to: {filepath}")
        return filepath
    
    def load_existing_metadata(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Load previously downloaded metadata from a JSON file.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            List of metadata dictionaries
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get('results', [])