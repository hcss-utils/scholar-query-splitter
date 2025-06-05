"""
Query generation module.

This module generates modified subqueries by combining the base query
with extracted modifiers and time ranges.
"""

import logging
from typing import List, Dict, Tuple, Optional, Any
from itertools import combinations
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class QueryGenerator:
    """Generates modified subqueries from base query and modifiers."""
    
    def __init__(self, max_modifier_combinations: int = 2):
        """
        Initialize the query generator.
        
        Args:
            max_modifier_combinations: Maximum number of modifiers to combine
        """
        self.max_modifier_combinations = max_modifier_combinations
        
        # Special characters that need escaping in queries
        self.special_chars = r'[+\-&|!(){}[\]^"~*?:\\]'
    
    def generate_subqueries(self, 
                           base_query: str,
                           modifiers: Dict[str, List[Tuple[str, float]]],
                           start_year: Optional[int] = None,
                           end_year: Optional[int] = None,
                           year_ranges: Optional[List[Tuple[int, int]]] = None,
                           max_queries: int = 100) -> List[Dict[str, Any]]:
        """
        Generate subqueries from base query and modifiers.
        
        Args:
            base_query: The base search query
            modifiers: Dictionary with 'keywords' and 'entities' lists
            start_year: Start year for time-based splitting
            end_year: End year for time-based splitting
            year_ranges: Predefined year ranges to use
            max_queries: Maximum number of queries to generate
            
        Returns:
            List of query dictionaries with metadata
        """
        logger.info(f"Generating subqueries from base: {base_query}")
        
        queries = []
        
        # Prepare modifiers
        all_modifiers = self._prepare_modifiers(modifiers)
        
        # Generate year ranges if not provided
        if year_ranges is None and start_year and end_year:
            year_ranges = self._generate_year_ranges(start_year, end_year)
        elif year_ranges is None:
            year_ranges = [None]  # No year restriction
        
        # Generate combinations of modifiers
        modifier_combinations = self._generate_modifier_combinations(all_modifiers)
        
        query_count = 0
        
        # Generate queries for each combination and year range
        for year_range in year_ranges:
            for modifier_combo in modifier_combinations:
                if query_count >= max_queries:
                    break
                
                query_dict = self._create_query_dict(
                    base_query, modifier_combo, year_range
                )
                queries.append(query_dict)
                query_count += 1
            
            if query_count >= max_queries:
                break
        
        # Add base query without modifiers for each year range
        if query_count < max_queries:
            for year_range in year_ranges:
                if query_count >= max_queries:
                    break
                
                query_dict = self._create_query_dict(
                    base_query, [], year_range
                )
                queries.append(query_dict)
                query_count += 1
        
        logger.info(f"Generated {len(queries)} subqueries")
        return queries
    
    def _prepare_modifiers(self, modifiers: Dict[str, List[Tuple[str, float]]]) -> List[Tuple[str, float, str]]:
        """
        Prepare and combine modifiers from different sources.
        
        Args:
            modifiers: Dictionary with modifier lists
            
        Returns:
            Combined list of (modifier, score, type) tuples
        """
        all_modifiers = []
        
        # Add keywords
        for keyword, score in modifiers.get('keywords', []):
            cleaned = self._clean_modifier(keyword)
            if cleaned:
                all_modifiers.append((cleaned, score, 'keyword'))
        
        # Add entities
        for entity, score in modifiers.get('entities', []):
            cleaned = self._clean_modifier(entity)
            if cleaned:
                all_modifiers.append((cleaned, score, 'entity'))
        
        # Sort by score (descending)
        all_modifiers.sort(key=lambda x: x[1], reverse=True)
        
        return all_modifiers
    
    def _clean_modifier(self, modifier: str) -> str:
        """
        Clean and prepare a modifier for use in queries.
        
        Args:
            modifier: Raw modifier string
            
        Returns:
            Cleaned modifier string
        """
        # Remove extra whitespace
        modifier = ' '.join(modifier.split())
        
        # Check if modifier needs quotes (contains spaces or special chars)
        if ' ' in modifier or re.search(self.special_chars, modifier):
            # Escape quotes in the modifier
            modifier = modifier.replace('"', '\\"')
            # Wrap in quotes
            modifier = f'"{modifier}"'
        
        return modifier
    
    def _generate_modifier_combinations(self, modifiers: List[Tuple[str, float, str]]) -> List[List[Tuple[str, float, str]]]:
        """
        Generate combinations of modifiers up to max_modifier_combinations.
        
        Args:
            modifiers: List of modifier tuples
            
        Returns:
            List of modifier combinations
        """
        combinations_list = []
        
        # Single modifiers
        for modifier in modifiers:
            combinations_list.append([modifier])
        
        # Multiple modifier combinations
        for r in range(2, self.max_modifier_combinations + 1):
            for combo in combinations(modifiers, r):
                # Skip if combining too many entities (can be too specific)
                entity_count = sum(1 for m in combo if m[2] == 'entity')
                if entity_count <= 2:
                    combinations_list.append(list(combo))
        
        return combinations_list
    
    def _generate_year_ranges(self, start_year: int, end_year: int) -> List[Tuple[int, int]]:
        """
        Generate year ranges for temporal splitting.
        
        Args:
            start_year: Start year
            end_year: End year
            
        Returns:
            List of (start, end) year tuples
        """
        year_ranges = []
        total_years = end_year - start_year + 1
        
        if total_years <= 5:
            # Single year ranges
            for year in range(start_year, end_year + 1):
                year_ranges.append((year, year))
        elif total_years <= 10:
            # 2-year ranges
            for year in range(start_year, end_year, 2):
                end = min(year + 1, end_year)
                year_ranges.append((year, end))
        elif total_years <= 20:
            # 3-year ranges
            for year in range(start_year, end_year, 3):
                end = min(year + 2, end_year)
                year_ranges.append((year, end))
        else:
            # 5-year ranges
            for year in range(start_year, end_year, 5):
                end = min(year + 4, end_year)
                year_ranges.append((year, end))
        
        return year_ranges
    
    def _create_query_dict(self, base_query: str, 
                          modifiers: List[Tuple[str, float, str]], 
                          year_range: Optional[Tuple[int, int]]) -> Dict[str, Any]:
        """
        Create a query dictionary with metadata.
        
        Args:
            base_query: Base query string
            modifiers: List of modifier tuples
            year_range: Optional (start, end) year tuple
            
        Returns:
            Query dictionary
        """
        # Build the query string
        query_parts = [f"({base_query})"]
        
        # Add modifiers
        for modifier, score, mod_type in modifiers:
            query_parts.append(modifier)
        
        query_string = ' '.join(query_parts)
        
        # Add year constraints
        if year_range:
            start_year, end_year = year_range
            if start_year == end_year:
                query_string += f" after:{start_year-1} before:{start_year+1}"
            else:
                query_string += f" after:{start_year-1} before:{end_year+1}"
        
        # Create metadata
        query_dict = {
            'query': query_string,
            'base_query': base_query,
            'modifiers': [{'text': m[0], 'score': m[1], 'type': m[2]} for m in modifiers],
            'year_range': year_range,
            'modifier_count': len(modifiers)
        }
        
        return query_dict
    
    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a query string.
        
        Args:
            query: Query string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for empty query
        if not query or not query.strip():
            return False, "Query is empty"
        
        # Check for balanced parentheses
        paren_count = 0
        for char in query:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            if paren_count < 0:
                return False, "Unbalanced parentheses"
        
        if paren_count != 0:
            return False, "Unbalanced parentheses"
        
        # Check for balanced quotes
        quote_count = query.count('"') - query.count('\\"')
        if quote_count % 2 != 0:
            return False, "Unbalanced quotes"
        
        # Check query length
        if len(query) > 1000:
            return False, "Query too long (max 1000 characters)"
        
        return True, None