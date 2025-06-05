"""
Modifier extraction module using KeyBERT and spaCy.

This module extracts key phrases and named entities from metadata titles
and abstracts to use as query modifiers.
"""

import logging
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import Counter
import re
import json
from pathlib import Path
from datetime import datetime
import os

import spacy
from keybert import KeyBERT
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from tqdm import tqdm
import torch

logger = logging.getLogger(__name__)


class ModifierExtractor:
    """Extracts key phrases and named entities from text metadata."""
    
    def __init__(self, spacy_model: str = "en_core_web_sm", 
                 use_gpu: bool = True,
                 output_dir: str = "outputs"):
        """
        Initialize the modifier extractor.
        
        Args:
            spacy_model: Name of the spaCy model to use
            use_gpu: Whether to use GPU if available
            output_dir: Directory for intermediate outputs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Check GPU availability
        self.use_gpu = use_gpu and torch.cuda.is_available()
        if self.use_gpu:
            logger.info(f"🚀 GPU detected: {torch.cuda.get_device_name(0)}")
            logger.info(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        else:
            logger.info("Running on CPU")
        
        logger.info(f"Loading spaCy model: {spacy_model}")
        try:
            # Enable GPU for spaCy if available
            if self.use_gpu:
                try:
                    spacy.require_gpu()
                    logger.info("✓ spaCy GPU acceleration enabled")
                except ValueError as e:
                    logger.warning(f"spaCy GPU acceleration not available: {e}")
                    logger.warning("Continuing with CPU for spaCy. Install cupy-cuda12x for GPU support.")
            self.nlp = spacy.load(spacy_model)
        except OSError:
            logger.warning(f"Model {spacy_model} not found. Downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", spacy_model])
            self.nlp = spacy.load(spacy_model)
        
        logger.info("Initializing KeyBERT")
        # Use GPU-accelerated BERT model if available
        if self.use_gpu:
            # Use a model that works well with GPU
            self.kw_model = KeyBERT(model='all-MiniLM-L12-v2')
            logger.info("✓ KeyBERT initialized with GPU-accelerated model")
        else:
            self.kw_model = KeyBERT()
        
        # Entity types to extract
        self.entity_types = {'ORG', 'GPE', 'PERSON', 'FAC', 'LOC', 'EVENT'}
        
        # Stop phrases to filter out
        self.stop_phrases = {
            'case study', 'literature review', 'systematic review',
            'meta analysis', 'research paper', 'conference paper',
            'journal article', 'working paper', 'technical report',
            'empirical study', 'theoretical framework', 'research methodology'
        }
        
        # Additional stopwords beyond sklearn's default
        self.custom_stopwords = {
            'approach', 'analysis', 'study', 'research', 'paper',
            'article', 'review', 'using', 'based', 'towards'
        }
        
        # Combine all stopwords
        self.all_stopwords = set(ENGLISH_STOP_WORDS) | self.custom_stopwords
    
    def extract_modifiers(self, metadata_list: List[Dict[str, Any]], 
                         top_k_keywords: int = 20,
                         top_k_entities: int = 20,
                         force_regenerate: bool = False) -> Dict[str, List[Tuple[str, Any]]]:
        """
        Extract modifiers from a list of metadata.
        
        Args:
            metadata_list: List of metadata dictionaries
            top_k_keywords: Number of top keywords to extract
            top_k_entities: Number of top entities to extract
            force_regenerate: Force regeneration even if files exist
            
        Returns:
            Dictionary with 'keywords' and 'entities' lists
        """
        # Check for existing modifier files first
        if not force_regenerate:
            existing_modifiers = self._load_existing_modifiers()
            if existing_modifiers:
                logger.info("✅ Found existing keyword and entity files - reusing them!")
                print(f"\n{'='*60}")
                print(f"♻️  REUSING EXISTING MODIFIERS")
                print(f"{'='*60}")
                print(f"📁 Keywords: {existing_modifiers['keywords_file']}")
                print(f"📁 Entities: {existing_modifiers['entities_file']}")
                print(f"🔑 Keywords loaded: {len(existing_modifiers['keywords'])}")
                print(f"🏷️  Entities loaded: {len(existing_modifiers['entities'])}")
                print(f"{'='*60}\n")
                
                # Return existing modifiers
                return {
                    'keywords': existing_modifiers['keywords'][:top_k_keywords],
                    'entities': existing_modifiers['entities'][:top_k_entities]
                }
        
        logger.info(f"Extracting modifiers from {len(metadata_list)} documents")
        print(f"\n{'='*60}")
        print(f"MODIFIER EXTRACTION PIPELINE")
        print(f"{'='*60}")
        print(f"📊 Documents to process: {len(metadata_list)}")
        print(f"🖥️  Hardware: {'GPU (' + torch.cuda.get_device_name(0) + ')' if self.use_gpu else 'CPU'}")
        print(f"💾 RAM Available: {self._get_memory_info()}")
        print(f"{'='*60}\n")
        
        # Collect all text
        all_texts = []
        for metadata in tqdm(metadata_list, desc="📝 Processing documents"):
            text = self._prepare_text(metadata)
            if text:
                all_texts.append(text)
        
        logger.info(f"Prepared {len(all_texts)} text documents")
        
        # Extract keywords using KeyBERT
        print(f"\n{'='*50}")
        print(f"🔑 KEYWORD EXTRACTION PHASE")
        print(f"{'='*50}")
        keywords = self._extract_keywords(all_texts, top_k_keywords)
        print(f"✅ Extracted {len(keywords)} keywords")
        
        # Save keywords incrementally
        keywords_file = self.output_dir / f"keywords_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(keywords_file, 'w') as f:
            json.dump(keywords, f, indent=2)
        print(f"💾 Keywords saved to: {keywords_file}")
        
        # Extract named entities using spaCy
        print(f"\n{'='*50}")
        print(f"🏷️  NAMED ENTITY EXTRACTION PHASE")
        print(f"{'='*50}")
        entities = self._extract_entities(all_texts, top_k_entities)
        print(f"✅ Extracted {len(entities)} unique entities")
        
        # Save entities incrementally
        entities_file = self.output_dir / f"entities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(entities_file, 'w') as f:
            json.dump(entities, f, indent=2)
        print(f"💾 Entities saved to: {entities_file}")
        
        return {
            'keywords': keywords,
            'entities': entities
        }
    
    def _get_memory_info(self) -> str:
        """Get memory information."""
        import psutil
        mem = psutil.virtual_memory()
        return f"{mem.available / 1e9:.1f} GB / {mem.total / 1e9:.1f} GB"
    
    def _prepare_text(self, metadata: Dict[str, Any]) -> str:
        """
        Prepare text from metadata for processing.
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            Concatenated and cleaned text
        """
        parts = []
        
        # Add title
        title = metadata.get('title', '')
        if title:
            parts.append(title)
        
        # Add abstract
        abstract = metadata.get('abstract', '')
        if abstract:
            # Handle inverted index format if present
            if isinstance(abstract, dict):
                abstract = self._reconstruct_abstract(abstract)
            parts.append(abstract)
        
        # Add high-scoring concepts
        concepts = metadata.get('concepts', [])
        for concept in concepts:
            if concept.get('score', 0) > 0.5:
                parts.append(concept.get('display_name', ''))
        
        # Join and clean
        text = ' '.join(parts)
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = text.strip()
        
        return text
    
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
    
    def _extract_keywords(self, texts: List[str], top_k: int) -> List[Tuple[str, float]]:
        """
        Extract keywords from texts using KeyBERT.
        
        Args:
            texts: List of text documents
            top_k: Number of keywords to extract
            
        Returns:
            List of (keyword, score) tuples
        """
        logger.info("Extracting keywords with KeyBERT")
        print(f"📋 Configuration:")
        print(f"   - N-gram range: (1, 2) - Uni/Bi-grams only")
        print(f"   - Diversity: 0.5 (MMR)")
        print(f"   - Stopword filtering: Enabled")
        print(f"   - Custom stopwords: {len(self.all_stopwords)} words")
        
        # Process in batches for better memory usage
        batch_size = 100 if self.use_gpu else 50
        all_keywords = []
        
        print(f"\n🔄 Processing in batches of {batch_size} documents...")
        
        for i in tqdm(range(0, len(texts), batch_size), desc="🔑 Extracting keywords"):
            batch_texts = texts[i:i + batch_size]
            combined_batch = ' '.join(batch_texts)
            
            # Create custom vectorizer with stopwords - ONLY UNI/BI-GRAMS
            vectorizer = CountVectorizer(
                ngram_range=(1, 2),  # Changed from (1,3) to (1,2) for uni/bi-grams only
                stop_words=list(self.all_stopwords),
                max_features=10000  # Limit features for memory efficiency
            )
            
            try:
                # Extract keywords
                batch_keywords = self.kw_model.extract_keywords(
                    combined_batch,
                    vectorizer=vectorizer,
                    top_n=top_k * 3,  # Extract more for better filtering
                    use_mmr=True,  # Use Maximal Marginal Relevance for diversity
                    diversity=0.5,
                    nr_candidates=50  # Increase candidate pool
                )
                
                # Filter and add to results
                for keyword, score in batch_keywords:
                    # Additional filtering
                    if (not any(stop in keyword.lower() for stop in self.stop_phrases) and
                        len(keyword) > 3 and  # Minimum length
                        not keyword.isdigit()):  # No pure numbers
                        all_keywords.append((keyword, score))
                
                # Log progress
                if (i + batch_size) % 500 == 0:
                    print(f"   ✓ Processed {min(i + batch_size, len(texts))} / {len(texts)} documents")
                    
            except Exception as e:
                logger.error(f"Error in batch {i}: {e}")
                continue
        
        # Aggregate and sort keywords
        keyword_scores = Counter()
        for keyword, score in all_keywords:
            keyword_scores[keyword] += score
        
        # Normalize scores and get top k
        total_score = sum(keyword_scores.values())
        final_keywords = []
        
        print(f"\n📊 Keyword statistics:")
        print(f"   - Total unique keywords found: {len(keyword_scores)}")
        
        for keyword, score in keyword_scores.most_common(top_k):
            normalized_score = score / total_score if total_score > 0 else 0
            final_keywords.append((keyword, normalized_score))
        
        # Print top 10 keywords
        print(f"\n🏆 Top 10 keywords:")
        for i, (keyword, score) in enumerate(final_keywords[:10], 1):
            print(f"   {i:2d}. {keyword:<30} (score: {score:.4f})")
        
        return final_keywords
    
    def _extract_entities(self, texts: List[str], top_k: int) -> List[Tuple[str, str, float]]:
        """
        Extract named entities from texts using spaCy.
        
        Args:
            texts: List of text documents
            top_k: Number of entities to extract
            
        Returns:
            List of (entity, entity_type, frequency) tuples
        """
        logger.info("Extracting named entities with spaCy")
        print(f"📋 Configuration:")
        print(f"   - Entity types: {', '.join(sorted(self.entity_types))}")
        print(f"   - Min entity length: 3 characters")
        print(f"   - Batch processing: Enabled")
        
        entity_counter = Counter()
        entity_types = {}  # Store entity types
        
        # Optimize batch size based on available memory
        batch_size = 200 if self.use_gpu else 100
        n_batches = (len(texts) + batch_size - 1) // batch_size
        
        print(f"\n🔄 Processing {len(texts)} texts in {n_batches} batches...")
        
        # Process texts in batches
        for i in tqdm(range(0, len(texts), batch_size), desc="🏷️  Extracting entities", total=n_batches):
            batch = texts[i:i + batch_size]
            
            # Use pipe for batch processing with optimal settings
            docs = self.nlp.pipe(
                batch, 
                disable=['parser', 'lemmatizer', 'textcat'],  # Only keep NER
                batch_size=batch_size,
                n_process=4 if not self.use_gpu else 1  # Multi-processing on CPU
            )
            
            for doc in docs:
                for ent in doc.ents:
                    if ent.label_ in self.entity_types:
                        # Normalize entity text
                        entity_text = ent.text.strip()
                        
                        # Apply filters
                        if (len(entity_text) > 2 and  # Min length
                            not entity_text.lower() in self.all_stopwords and  # Not a stopword
                            not entity_text.isdigit() and  # Not pure numbers
                            not all(c in '.-_' for c in entity_text)):  # Not just punctuation
                            
                            entity_counter[entity_text] += 1
                            entity_types[entity_text] = ent.label_  # Store entity type
            
            # Log progress
            if (i + batch_size) % 1000 == 0:
                print(f"   ✓ Processed {min(i + batch_size, len(texts))} / {len(texts)} texts")
                print(f"   📊 Unique entities so far: {len(entity_counter)}")
        
        # Convert to list with normalized scores and entity types
        total = sum(entity_counter.values())
        entities = []
        
        print(f"\n📊 Entity statistics:")
        print(f"   - Total entities found: {total}")
        print(f"   - Unique entities: {len(entity_counter)}")
        
        # Count by type
        type_counts = Counter()
        for entity, count in entity_counter.most_common():
            type_counts[entity_types[entity]] += count
        
        print(f"\n📈 Entities by type:")
        for ent_type, count in sorted(type_counts.items()):
            print(f"   - {ent_type:<8}: {count:5d} ({count/total*100:5.1f}%)")
        
        # Create final list with entity types
        for entity, count in entity_counter.most_common(top_k):
            score = count / total if total > 0 else 0
            entities.append((entity, entity_types[entity], score))
        
        # Print top 10 entities
        print(f"\n🏆 Top 10 entities:")
        for i, (entity, ent_type, score) in enumerate(entities[:10], 1):
            print(f"   {i:2d}. {entity:<25} [{ent_type:<7}] (freq: {score:.4f})")
        
        return entities
    
    def filter_modifiers(self, modifiers: Dict[str, List[Tuple[str, Any]]],
                        base_query: str) -> Dict[str, List[Tuple[str, Any]]]:
        """
        Filter modifiers to remove those already in the base query.
        
        Args:
            modifiers: Dictionary of modifier lists
            base_query: The base query string
            
        Returns:
            Filtered modifiers dictionary
        """
        base_query_lower = base_query.lower()
        filtered = {'keywords': [], 'entities': []}
        
        print(f"\n🔍 Filtering modifiers...")
        initial_keywords = len(modifiers.get('keywords', []))
        initial_entities = len(modifiers.get('entities', []))
        
        # Filter keywords
        for item in modifiers.get('keywords', []):
            keyword, score = item
            if keyword.lower() not in base_query_lower:
                filtered['keywords'].append((keyword, score))
        
        # Filter entities (handle both old and new format)
        for item in modifiers.get('entities', []):
            if len(item) == 3:  # New format with entity type
                entity, ent_type, score = item
                if entity.lower() not in base_query_lower:
                    filtered['entities'].append((entity, ent_type, score))
            else:  # Old format without entity type
                entity, score = item
                if entity.lower() not in base_query_lower:
                    filtered['entities'].append((entity, score))
        
        print(f"   - Keywords: {initial_keywords} → {len(filtered['keywords'])} (filtered {initial_keywords - len(filtered['keywords'])})")
        print(f"   - Entities: {initial_entities} → {len(filtered['entities'])} (filtered {initial_entities - len(filtered['entities'])})")
        
        return filtered
    
    def _load_existing_modifiers(self) -> Optional[Dict]:
        """
        Load existing keyword and entity files if they exist.
        
        Returns:
            Dictionary with loaded modifiers or None if not found
        """
        # Find most recent keyword and entity files
        keyword_files = sorted(self.output_dir.glob("keywords_*.json"), reverse=True)
        entity_files = sorted(self.output_dir.glob("entities_*.json"), reverse=True)
        
        if not keyword_files or not entity_files:
            return None
        
        # Use the most recent files
        keywords_file = keyword_files[0]
        entities_file = entity_files[0]
        
        try:
            # Load keywords
            with open(keywords_file, 'r') as f:
                keywords = json.load(f)
            
            # Load entities
            with open(entities_file, 'r') as f:
                entities = json.load(f)
            
            # Convert to expected format
            # Keywords should be list of (keyword, score) tuples
            if keywords and isinstance(keywords[0], list) and len(keywords[0]) == 2:
                keywords_formatted = [(k[0], k[1]) for k in keywords]
            else:
                keywords_formatted = keywords
            
            # Entities might be in old format (entity, score) or new format (entity, type, score)
            entities_formatted = []
            if entities and isinstance(entities[0], list):
                if len(entities[0]) == 2:  # Old format
                    entities_formatted = [(e[0], e[1]) for e in entities]
                elif len(entities[0]) == 3:  # New format
                    entities_formatted = [(e[0], e[1], e[2]) for e in entities]
            else:
                entities_formatted = entities
            
            logger.info(f"Loaded {len(keywords_formatted)} keywords from {keywords_file.name}")
            logger.info(f"Loaded {len(entities_formatted)} entities from {entities_file.name}")
            
            return {
                'keywords': keywords_formatted,
                'entities': entities_formatted,
                'keywords_file': keywords_file.name,
                'entities_file': entities_file.name
            }
            
        except Exception as e:
            logger.warning(f"Error loading existing modifiers: {e}")
            return None