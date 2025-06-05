"""
Modifier extraction module using KeyBERT and spaCy.

This module extracts key phrases and named entities from metadata titles
and abstracts to use as query modifiers.
"""

import logging
from typing import List, Dict, Any, Set, Tuple
from collections import Counter
import re

import spacy
from keybert import KeyBERT
from sklearn.feature_extraction.text import CountVectorizer
from tqdm import tqdm

logger = logging.getLogger(__name__)


class ModifierExtractor:
    """Extracts key phrases and named entities from text metadata."""
    
    def __init__(self, spacy_model: str = "en_core_web_sm"):
        """
        Initialize the modifier extractor.
        
        Args:
            spacy_model: Name of the spaCy model to use
        """
        logger.info(f"Loading spaCy model: {spacy_model}")
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            logger.warning(f"Model {spacy_model} not found. Downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", spacy_model])
            self.nlp = spacy.load(spacy_model)
        
        logger.info("Initializing KeyBERT")
        self.kw_model = KeyBERT()
        
        # Entity types to extract
        self.entity_types = {'ORG', 'GPE', 'PERSON', 'FAC', 'LOC', 'EVENT'}
        
        # Stop phrases to filter out
        self.stop_phrases = {
            'case study', 'literature review', 'systematic review',
            'meta analysis', 'research paper', 'conference paper',
            'journal article', 'working paper', 'technical report'
        }
    
    def extract_modifiers(self, metadata_list: List[Dict[str, Any]], 
                         top_k_keywords: int = 20,
                         top_k_entities: int = 20) -> Dict[str, List[Tuple[str, float]]]:
        """
        Extract modifiers from a list of metadata.
        
        Args:
            metadata_list: List of metadata dictionaries
            top_k_keywords: Number of top keywords to extract
            top_k_entities: Number of top entities to extract
            
        Returns:
            Dictionary with 'keywords' and 'entities' lists
        """
        logger.info(f"Extracting modifiers from {len(metadata_list)} documents")
        
        # Collect all text
        all_texts = []
        for metadata in tqdm(metadata_list, desc="Processing documents"):
            text = self._prepare_text(metadata)
            if text:
                all_texts.append(text)
        
        logger.info(f"Prepared {len(all_texts)} text documents")
        
        # Extract keywords using KeyBERT
        print(f"\n--- Keyword Extraction Phase ---")
        keywords = self._extract_keywords(all_texts, top_k_keywords)
        print(f"✓ Extracted {len(keywords)} keywords")
        
        # Extract named entities using spaCy
        print(f"\n--- Named Entity Extraction Phase ---")
        entities = self._extract_entities(all_texts, top_k_entities)
        print(f"✓ Extracted {len(entities)} entities")
        
        return {
            'keywords': keywords,
            'entities': entities
        }
    
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
        
        # Combine all texts with progress bar
        print("Combining texts for keyword extraction...")
        combined_text = ' '.join(tqdm(texts, desc="Combining texts", unit="docs"))
        
        # Use n-gram range to capture phrases
        print("Creating vectorizer...")
        vectorizer = CountVectorizer(ngram_range=(1, 3), stop_words='english')
        
        try:
            # Extract keywords
            print(f"Extracting top {top_k * 2} keywords (will filter to {top_k})...")
            keywords = self.kw_model.extract_keywords(
                combined_text,
                vectorizer=vectorizer,
                top_n=top_k * 2,  # Extract more initially for filtering
                use_mmr=True,  # Use Maximal Marginal Relevance for diversity
                diversity=0.5
            )
            
            # Filter out stop phrases
            filtered_keywords = []
            for keyword, score in keywords:
                if not any(stop in keyword.lower() for stop in self.stop_phrases):
                    filtered_keywords.append((keyword, score))
            
            # Return top k
            return filtered_keywords[:top_k]
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def _extract_entities(self, texts: List[str], top_k: int) -> List[Tuple[str, float]]:
        """
        Extract named entities from texts using spaCy.
        
        Args:
            texts: List of text documents
            top_k: Number of entities to extract
            
        Returns:
            List of (entity, frequency) tuples
        """
        logger.info("Extracting named entities with spaCy")
        
        entity_counter = Counter()
        
        # Process texts in batches
        batch_size = 100
        n_batches = (len(texts) + batch_size - 1) // batch_size
        print(f"Processing {len(texts)} texts in {n_batches} batches...")
        
        for i in tqdm(range(0, len(texts), batch_size), desc="Extracting entities", total=n_batches):
            batch = texts[i:i + batch_size]
            docs = self.nlp.pipe(batch, disable=['parser', 'lemmatizer'])
            
            for doc in docs:
                for ent in doc.ents:
                    if ent.label_ in self.entity_types:
                        # Normalize entity text
                        entity_text = ent.text.strip()
                        if len(entity_text) > 2:  # Filter very short entities
                            entity_counter[entity_text] += 1
        
        # Convert to list with normalized scores
        total = sum(entity_counter.values())
        entities = []
        for entity, count in entity_counter.most_common(top_k):
            score = count / total if total > 0 else 0
            entities.append((entity, score))
        
        return entities
    
    def filter_modifiers(self, modifiers: Dict[str, List[Tuple[str, float]]],
                        base_query: str) -> Dict[str, List[Tuple[str, float]]]:
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
        
        # Filter keywords
        for keyword, score in modifiers.get('keywords', []):
            if keyword.lower() not in base_query_lower:
                filtered['keywords'].append((keyword, score))
        
        # Filter entities
        for entity, score in modifiers.get('entities', []):
            if entity.lower() not in base_query_lower:
                filtered['entities'].append((entity, score))
        
        return filtered