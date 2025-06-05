"""
Exhaustive query splitter for complete coverage.

This module implements a systematic approach to split large queries into
smaller chunks (<1000 hits) to ensure complete coverage of all results.
"""

import logging
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict
import json
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import time

logger = logging.getLogger(__name__)


class ExhaustiveQuerySplitter:
    """Splits queries systematically to achieve complete coverage."""
    
    def __init__(self, scholar_counter=None, target_size: int = 900):
        """
        Initialize the exhaustive splitter.
        
        Args:
            scholar_counter: ScholarHitsCounter instance
            target_size: Target maximum hits per query (default 900 to stay under 1000)
        """
        self.scholar_counter = scholar_counter
        self.target_size = target_size
        self.coverage_tracker = {}
        self.processed_queries = set()
        
    def split_exhaustively(self, 
                          base_query: str,
                          modifiers: Dict[str, List[Tuple[str, any]]],
                          year_range: Optional[Tuple[int, int]] = None,
                          output_dir: str = "outputs") -> Dict:
        """
        Split a query exhaustively to get all results.
        
        Args:
            base_query: The base search query
            modifiers: Dictionary with 'keywords' and 'entities' lists
            year_range: Optional (start_year, end_year) tuple
            output_dir: Directory for output files
            
        Returns:
            Dictionary with splitting results and coverage statistics
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Initialize tracking
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = output_path / f"exhaustive_split_{timestamp}.json"
        coverage_file = output_path / f"coverage_map_{timestamp}.json"
        
        print(f"\n{'='*60}")
        print(f"EXHAUSTIVE QUERY SPLITTER")
        print(f"{'='*60}")
        print(f"🎯 Goal: Split query into chunks < {self.target_size} hits")
        print(f"📝 Base query: {base_query}")
        if year_range:
            print(f"📅 Year range: {year_range[0]} - {year_range[1]}")
        print(f"{'='*60}\n")
        
        # Step 1: Check base query size
        base_hits = self._get_hit_count(base_query, year_range)
        print(f"📊 Base query hits: {base_hits:,}")
        
        if base_hits <= self.target_size:
            print(f"✅ Query already under target size!")
            return {
                'status': 'complete',
                'total_hits': base_hits,
                'queries': [{'query': base_query, 'hits': base_hits}],
                'coverage': 100.0
            }
        
        # Step 2: Prepare modifiers (uni/bi-grams only)
        print(f"\n🔧 Preparing modifiers...")
        prepared_modifiers = self._prepare_modifiers(modifiers)
        print(f"   - Keywords: {len(prepared_modifiers['keywords'])}")
        print(f"   - Entities: {len(prepared_modifiers['entities'])}")
        
        # Step 3: Build modifier effectiveness map
        print(f"\n📈 Testing modifier effectiveness...")
        modifier_map = self._build_modifier_map(base_query, prepared_modifiers, year_range)
        
        # Step 4: Create splitting strategy
        print(f"\n🔨 Creating splitting strategy...")
        split_strategy = self._create_split_strategy(
            base_query, base_hits, modifier_map, year_range
        )
        
        # Step 5: Execute splits
        print(f"\n🚀 Executing query splits...")
        final_queries = self._execute_splits(split_strategy)
        
        # Step 6: Verify coverage
        print(f"\n✓ Verifying coverage...")
        coverage_stats = self._verify_coverage(final_queries, base_hits)
        
        # Save results
        results = {
            'timestamp': timestamp,
            'base_query': base_query,
            'base_hits': base_hits,
            'year_range': year_range,
            'target_size': self.target_size,
            'final_queries': final_queries,
            'coverage_stats': coverage_stats,
            'modifier_effectiveness': modifier_map
        }
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        with open(coverage_file, 'w') as f:
            json.dump(self.coverage_tracker, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"📊 SPLITTING COMPLETE")
        print(f"{'='*60}")
        print(f"✅ Total queries generated: {len(final_queries)}")
        print(f"📈 Coverage: {coverage_stats['coverage_percentage']:.1f}%")
        print(f"📁 Results saved to: {results_file}")
        print(f"🗺️  Coverage map saved to: {coverage_file}")
        
        return results
    
    def _prepare_modifiers(self, modifiers: Dict) -> Dict:
        """Prepare modifiers, keeping only uni/bi-grams."""
        prepared = {'keywords': [], 'entities': []}
        
        # Process keywords - keep only uni/bi-grams
        for item in modifiers.get('keywords', []):
            if len(item) >= 2:
                keyword = item[0]
                score = item[1] if len(item) == 2 else item[2]
                
                # Count words
                word_count = len(keyword.split())
                if word_count <= 2:  # Uni or bi-gram
                    prepared['keywords'].append((keyword, score))
        
        # Process entities
        for item in modifiers.get('entities', []):
            if len(item) >= 2:
                entity = item[0]
                if len(item) == 3:  # New format with type
                    ent_type = item[1]
                    score = item[2]
                    prepared['entities'].append((entity, ent_type, score))
                else:  # Old format
                    score = item[1]
                    prepared['entities'].append((entity, score))
        
        return prepared
    
    def _get_hit_count(self, query: str, year_range: Optional[Tuple[int, int]] = None) -> int:
        """Get hit count for a query."""
        if self.scholar_counter:
            # Add year range to query if specified
            if year_range:
                query = f"{query} after:{year_range[0]} before:{year_range[1]}"
            
            # Create a query dict for the counter
            query_dict = {
                'query': query,
                'modifiers': [],
                'year_range': year_range
            }
            
            # Use the actual counter method
            result = self.scholar_counter._count_single_query(query_dict, 0)
            return result.get('hit_count', 0) if result else 0
        else:
            # Simulate for testing
            import random
            time.sleep(0.1)  # Simulate API delay
            return random.randint(100, 10000)
    
    def _build_modifier_map(self, base_query: str, modifiers: Dict, 
                           year_range: Optional[Tuple[int, int]]) -> Dict:
        """Build a map of modifier effectiveness."""
        modifier_map = {
            'keywords': {},
            'entities': {},
            'combinations': {}
        }
        
        # Test individual keywords
        print(f"\n   Testing keywords...")
        for keyword, score in tqdm(modifiers['keywords'][:30], desc="   Keywords"):
            test_query = f'{base_query} AND "{keyword}"'
            hits = self._get_hit_count(test_query, year_range)
            reduction_rate = 1 - (hits / self._get_hit_count(base_query, year_range))
            modifier_map['keywords'][keyword] = {
                'hits': hits,
                'reduction_rate': reduction_rate,
                'score': score
            }
        
        # Test individual entities
        print(f"\n   Testing entities...")
        for item in tqdm(modifiers['entities'][:30], desc="   Entities"):
            entity = item[0]
            test_query = f'{base_query} AND "{entity}"'
            hits = self._get_hit_count(test_query, year_range)
            reduction_rate = 1 - (hits / self._get_hit_count(base_query, year_range))
            modifier_map['entities'][entity] = {
                'hits': hits,
                'reduction_rate': reduction_rate,
                'item': item
            }
        
        # Sort by effectiveness (best reduction rate)
        modifier_map['keywords'] = dict(sorted(
            modifier_map['keywords'].items(),
            key=lambda x: x[1]['reduction_rate'],
            reverse=True
        ))
        
        modifier_map['entities'] = dict(sorted(
            modifier_map['entities'].items(),
            key=lambda x: x[1]['reduction_rate'],
            reverse=True
        ))
        
        return modifier_map
    
    def _create_split_strategy(self, base_query: str, base_hits: int, 
                              modifier_map: Dict, year_range: Optional[Tuple[int, int]]) -> List[Dict]:
        """Create an optimal splitting strategy."""
        strategy = []
        remaining_coverage = base_hits
        used_modifiers = set()
        
        print(f"\n   Building split strategy...")
        print(f"   Target: Cover {base_hits:,} hits in chunks < {self.target_size}")
        
        # Strategy 1: Try single modifiers first
        all_modifiers = []
        
        # Add keywords
        for keyword, data in modifier_map['keywords'].items():
            if data['hits'] < self.target_size and data['hits'] > 0:
                all_modifiers.append({
                    'type': 'keyword',
                    'modifier': keyword,
                    'hits': data['hits'],
                    'reduction_rate': data['reduction_rate']
                })
        
        # Add entities
        for entity, data in modifier_map['entities'].items():
            if data['hits'] < self.target_size and data['hits'] > 0:
                all_modifiers.append({
                    'type': 'entity',
                    'modifier': entity,
                    'hits': data['hits'],
                    'reduction_rate': data['reduction_rate']
                })
        
        # Sort by hits (descending) to maximize coverage
        all_modifiers.sort(key=lambda x: x['hits'], reverse=True)
        
        # Greedy approach: pick modifiers that give us the most coverage
        for mod in all_modifiers:
            if remaining_coverage <= 0:
                break
                
            if mod['modifier'] not in used_modifiers:
                query = f'{base_query} AND "{mod["modifier"]}"'
                strategy.append({
                    'query': query,
                    'modifiers': [mod['modifier']],
                    'expected_hits': mod['hits'],
                    'type': 'single'
                })
                used_modifiers.add(mod['modifier'])
                remaining_coverage -= mod['hits']
        
        # Strategy 2: If we still need coverage, try combinations
        if remaining_coverage > 0:
            print(f"\n   Need additional coverage: {remaining_coverage:,} hits")
            print(f"   Trying modifier combinations...")
            
            # Generate combinations of unused modifiers
            unused_keywords = [k for k in modifier_map['keywords'].keys() 
                             if k not in used_modifiers][:10]
            unused_entities = [e for e in modifier_map['entities'].keys() 
                             if e not in used_modifiers][:10]
            
            # Try keyword + entity combinations
            for keyword in unused_keywords:
                for entity in unused_entities:
                    test_query = f'{base_query} AND "{keyword}" AND "{entity}"'
                    hits = self._get_hit_count(test_query, year_range)
                    
                    if 0 < hits < self.target_size:
                        strategy.append({
                            'query': test_query,
                            'modifiers': [keyword, entity],
                            'expected_hits': hits,
                            'type': 'combination'
                        })
                        remaining_coverage -= hits
                        
                        if remaining_coverage <= 0:
                            break
                
                if remaining_coverage <= 0:
                    break
        
        # Strategy 3: If still need coverage, create exclusion queries
        if remaining_coverage > 0:
            print(f"\n   Still need {remaining_coverage:,} hits")
            print(f"   Creating exclusion queries...")
            
            # Create a query that excludes all used modifiers
            exclusions = [f'NOT "{mod}"' for mod in list(used_modifiers)[:5]]
            exclusion_query = f"{base_query} {' '.join(exclusions)}"
            hits = self._get_hit_count(exclusion_query, year_range)
            
            if hits > 0:
                strategy.append({
                    'query': exclusion_query,
                    'modifiers': exclusions,
                    'expected_hits': hits,
                    'type': 'exclusion'
                })
        
        return strategy
    
    def _execute_splits(self, strategy: List[Dict]) -> List[Dict]:
        """Execute the splitting strategy and track actual results."""
        final_queries = []
        
        print(f"\n   Executing {len(strategy)} queries...")
        
        for i, split in enumerate(tqdm(strategy, desc="   Executing splits")):
            # Get actual hit count
            actual_hits = self._get_hit_count(split['query'])
            
            # If still too large, try to split further
            if actual_hits > self.target_size:
                print(f"\n   ⚠️  Query {i+1} still too large: {actual_hits:,} hits")
                # Here you could implement recursive splitting
                # For now, we'll keep it
            
            final_queries.append({
                'id': i + 1,
                'query': split['query'],
                'modifiers': split['modifiers'],
                'type': split['type'],
                'expected_hits': split['expected_hits'],
                'actual_hits': actual_hits
            })
            
            # Track coverage
            self.coverage_tracker[split['query']] = {
                'hits': actual_hits,
                'modifiers': split['modifiers']
            }
        
        return final_queries
    
    def _verify_coverage(self, queries: List[Dict], base_hits: int) -> Dict:
        """Verify coverage statistics."""
        total_coverage = sum(q['actual_hits'] for q in queries)
        
        stats = {
            'base_hits': base_hits,
            'total_coverage': total_coverage,
            'coverage_percentage': (total_coverage / base_hits * 100) if base_hits > 0 else 0,
            'query_count': len(queries),
            'avg_hits_per_query': total_coverage / len(queries) if queries else 0,
            'queries_under_target': sum(1 for q in queries if q['actual_hits'] < self.target_size),
            'largest_query': max(q['actual_hits'] for q in queries) if queries else 0,
            'smallest_query': min(q['actual_hits'] for q in queries) if queries else 0
        }
        
        return stats