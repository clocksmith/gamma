"""Enhanced vocabulary alignment with multiple strategies for Mind Meld"""

import sys
import re
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict
import difflib


class AlignmentStrategy(Enum):
    """Available vocabulary alignment strategies"""
    INTERSECTION = "intersection"  # Only common tokens
    SEMANTIC = "semantic"  # Use embeddings for similarity
    SUBWORD = "subword"  # Break down into subwords
    FUZZY = "fuzzy"  # Fuzzy string matching
    HYBRID = "hybrid"  # Combination of strategies


@dataclass
class AlignmentConfig:
    """Configuration for vocabulary alignment"""
    strategy: AlignmentStrategy = AlignmentStrategy.INTERSECTION
    min_overlap: float = 0.5
    use_cache: bool = True
    fuzzy_threshold: float = 0.8
    semantic_threshold: float = 0.7
    subword_fallback: bool = True
    confidence_weighting: bool = False
    max_candidates: int = 5


@dataclass
class TokenMapping:
    """Detailed mapping for a single token"""
    source_id: int
    target_id: int
    source_text: str
    target_text: str
    confidence: float
    strategy_used: str
    
    
@dataclass
class VocabularyAlignment:
    """Complete alignment between two vocabularies"""
    mappings: List[TokenMapping]
    source_to_target: Dict[int, List[Tuple[int, float]]]  # id -> [(id, confidence), ...]
    target_to_source: Dict[int, List[Tuple[int, float]]]
    common_tokens: Set[str]
    source_only: Set[str]
    target_only: Set[str]
    overlap_ratio: float
    alignment_quality: float
    strategy_stats: Dict[str, int]
    
    def get_best_mapping(self, source_id: int) -> Optional[int]:
        """Get the best target token for a source token"""
        if source_id in self.source_to_target:
            candidates = self.source_to_target[source_id]
            if candidates:
                return candidates[0][0]  # Return highest confidence match
        return None
    
    def get_confidence(self, source_id: int, target_id: int) -> float:
        """Get confidence score for a specific mapping"""
        if source_id in self.source_to_target:
            for tid, conf in self.source_to_target[source_id]:
                if tid == target_id:
                    return conf
        return 0.0


class EnhancedVocabularyAligner:
    """Advanced vocabulary alignment with multiple strategies"""
    
    def __init__(self, config: Optional[AlignmentConfig] = None):
        self.config = config or AlignmentConfig()
        self.alignment_cache: Dict[Tuple[str, str], VocabularyAlignment] = {}
        self._embedding_cache: Dict[str, np.ndarray] = {}
        
    def align_vocabularies(
        self,
        source_tokenizer: Any,
        target_tokenizer: Any,
        source_name: str = "source",
        target_name: str = "target"
    ) -> VocabularyAlignment:
        """Align two vocabularies using configured strategy"""
        
        cache_key = (source_name, target_name)
        if self.config.use_cache and cache_key in self.alignment_cache:
            print(f"Using cached alignment for {source_name} → {target_name}")
            return self.alignment_cache[cache_key]
        
        print(f"Aligning vocabularies: {source_name} → {target_name}")
        print(f"Strategy: {self.config.strategy.value}")
        
        # Extract vocabularies
        source_vocab = self._extract_vocabulary(source_tokenizer)
        target_vocab = self._extract_vocabulary(target_tokenizer)
        
        # Choose alignment strategy
        if self.config.strategy == AlignmentStrategy.INTERSECTION:
            alignment = self._align_intersection(source_vocab, target_vocab)
        elif self.config.strategy == AlignmentStrategy.FUZZY:
            alignment = self._align_fuzzy(source_vocab, target_vocab)
        elif self.config.strategy == AlignmentStrategy.SUBWORD:
            alignment = self._align_subword(source_vocab, target_vocab)
        elif self.config.strategy == AlignmentStrategy.SEMANTIC:
            alignment = self._align_semantic(source_vocab, target_vocab, source_tokenizer, target_tokenizer)
        else:  # HYBRID
            alignment = self._align_hybrid(source_vocab, target_vocab, source_tokenizer, target_tokenizer)
        
        # Calculate statistics
        alignment = self._calculate_statistics(alignment, source_vocab, target_vocab)
        
        # Cache the result
        if self.config.use_cache:
            self.alignment_cache[cache_key] = alignment
        
        # Print summary
        self._print_summary(alignment)
        
        return alignment
    
    def _extract_vocabulary(self, tokenizer: Any) -> Dict[int, str]:
        """Extract vocabulary from tokenizer"""
        vocab = {}
        try:
            if hasattr(tokenizer, 'get_vocab'):
                raw_vocab = tokenizer.get_vocab()
                vocab = {v: k for k, v in raw_vocab.items()}  # token_text -> token_id
            elif hasattr(tokenizer, 'vocab'):
                vocab = {v: k for k, v in tokenizer.vocab.items()}
        except Exception as e:
            print(f"Warning: Could not extract vocabulary: {e}")
        return vocab
    
    def _align_intersection(
        self,
        source_vocab: Dict[int, str],
        target_vocab: Dict[int, str]
    ) -> VocabularyAlignment:
        """Simple intersection-based alignment"""
        mappings = []
        source_to_target = defaultdict(list)
        target_to_source = defaultdict(list)
        strategy_stats = defaultdict(int)
        
        # Create reverse lookup for target
        target_text_to_id = {text: tid for tid, text in target_vocab.items()}
        
        for source_id, source_text in source_vocab.items():
            if source_text in target_text_to_id:
                target_id = target_text_to_id[source_text]
                mapping = TokenMapping(
                    source_id=source_id,
                    target_id=target_id,
                    source_text=source_text,
                    target_text=source_text,
                    confidence=1.0,
                    strategy_used="intersection"
                )
                mappings.append(mapping)
                source_to_target[source_id].append((target_id, 1.0))
                target_to_source[target_id].append((source_id, 1.0))
                strategy_stats["intersection"] += 1
        
        return VocabularyAlignment(
            mappings=mappings,
            source_to_target=dict(source_to_target),
            target_to_source=dict(target_to_source),
            common_tokens=set(),
            source_only=set(),
            target_only=set(),
            overlap_ratio=0.0,
            alignment_quality=0.0,
            strategy_stats=dict(strategy_stats)
        )
    
    def _align_fuzzy(
        self,
        source_vocab: Dict[int, str],
        target_vocab: Dict[int, str]
    ) -> VocabularyAlignment:
        """Fuzzy string matching alignment"""
        mappings = []
        source_to_target = defaultdict(list)
        target_to_source = defaultdict(list)
        strategy_stats = defaultdict(int)
        
        target_texts = list(target_vocab.values())
        target_ids = list(target_vocab.keys())
        
        for source_id, source_text in source_vocab.items():
            # First try exact match
            if source_text in target_vocab.values():
                target_id = [tid for tid, text in target_vocab.items() if text == source_text][0]
                confidence = 1.0
                strategy = "exact"
            else:
                # Try fuzzy matching
                matches = difflib.get_close_matches(
                    source_text,
                    target_texts,
                    n=self.config.max_candidates,
                    cutoff=self.config.fuzzy_threshold
                )
                
                if matches:
                    # Get the best match
                    best_match = matches[0]
                    target_idx = target_texts.index(best_match)
                    target_id = target_ids[target_idx]
                    confidence = difflib.SequenceMatcher(None, source_text, best_match).ratio()
                    strategy = "fuzzy"
                else:
                    continue
            
            mapping = TokenMapping(
                source_id=source_id,
                target_id=target_id,
                source_text=source_text,
                target_text=target_vocab[target_id],
                confidence=confidence,
                strategy_used=strategy
            )
            mappings.append(mapping)
            source_to_target[source_id].append((target_id, confidence))
            target_to_source[target_id].append((source_id, confidence))
            strategy_stats[strategy] += 1
        
        # Sort by confidence
        for sid in source_to_target:
            source_to_target[sid].sort(key=lambda x: x[1], reverse=True)
        for tid in target_to_source:
            target_to_source[tid].sort(key=lambda x: x[1], reverse=True)
        
        return VocabularyAlignment(
            mappings=mappings,
            source_to_target=dict(source_to_target),
            target_to_source=dict(target_to_source),
            common_tokens=set(),
            source_only=set(),
            target_only=set(),
            overlap_ratio=0.0,
            alignment_quality=0.0,
            strategy_stats=dict(strategy_stats)
        )
    
    def _align_subword(
        self,
        source_vocab: Dict[int, str],
        target_vocab: Dict[int, str]
    ) -> VocabularyAlignment:
        """Subword decomposition alignment"""
        mappings = []
        source_to_target = defaultdict(list)
        target_to_source = defaultdict(list)
        strategy_stats = defaultdict(int)
        
        # Build subword index for target vocabulary
        target_subwords = defaultdict(list)
        for target_id, target_text in target_vocab.items():
            # Extract subwords (simple approach - can be enhanced)
            subwords = self._extract_subwords(target_text)
            for subword in subwords:
                target_subwords[subword].append((target_id, target_text))
        
        for source_id, source_text in source_vocab.items():
            # First try exact match
            exact_matches = [(tid, text) for tid, text in target_vocab.items() if text == source_text]
            if exact_matches:
                target_id, target_text = exact_matches[0]
                confidence = 1.0
                strategy = "exact"
            else:
                # Try subword matching
                source_subwords = self._extract_subwords(source_text)
                best_match = None
                best_score = 0
                
                for target_id, target_text in target_vocab.items():
                    target_subs = self._extract_subwords(target_text)
                    score = self._subword_similarity(source_subwords, target_subs)
                    if score > best_score and score >= 0.5:
                        best_score = score
                        best_match = (target_id, target_text)
                
                if best_match:
                    target_id, target_text = best_match
                    confidence = best_score
                    strategy = "subword"
                else:
                    continue
            
            mapping = TokenMapping(
                source_id=source_id,
                target_id=target_id,
                source_text=source_text,
                target_text=target_text,
                confidence=confidence,
                strategy_used=strategy
            )
            mappings.append(mapping)
            source_to_target[source_id].append((target_id, confidence))
            target_to_source[target_id].append((source_id, confidence))
            strategy_stats[strategy] += 1
        
        return VocabularyAlignment(
            mappings=mappings,
            source_to_target=dict(source_to_target),
            target_to_source=dict(target_to_source),
            common_tokens=set(),
            source_only=set(),
            target_only=set(),
            overlap_ratio=0.0,
            alignment_quality=0.0,
            strategy_stats=dict(strategy_stats)
        )
    
    def _align_semantic(
        self,
        source_vocab: Dict[int, str],
        target_vocab: Dict[int, str],
        source_tokenizer: Any,
        target_tokenizer: Any
    ) -> VocabularyAlignment:
        """Semantic similarity-based alignment using embeddings"""
        # For now, fallback to fuzzy matching
        # In a full implementation, this would use embeddings
        print("Note: Semantic alignment using fuzzy matching as fallback")
        return self._align_fuzzy(source_vocab, target_vocab)
    
    def _align_hybrid(
        self,
        source_vocab: Dict[int, str],
        target_vocab: Dict[int, str],
        source_tokenizer: Any,
        target_tokenizer: Any
    ) -> VocabularyAlignment:
        """Hybrid approach combining multiple strategies"""
        mappings = []
        source_to_target = defaultdict(list)
        target_to_source = defaultdict(list)
        strategy_stats = defaultdict(int)
        
        # Try strategies in order of preference
        for source_id, source_text in source_vocab.items():
            matched = False
            
            # 1. Try exact match
            exact_matches = [(tid, text) for tid, text in target_vocab.items() if text == source_text]
            if exact_matches:
                target_id, target_text = exact_matches[0]
                mapping = TokenMapping(
                    source_id=source_id,
                    target_id=target_id,
                    source_text=source_text,
                    target_text=target_text,
                    confidence=1.0,
                    strategy_used="exact"
                )
                mappings.append(mapping)
                source_to_target[source_id].append((target_id, 1.0))
                target_to_source[target_id].append((source_id, 1.0))
                strategy_stats["exact"] += 1
                continue
            
            # 2. Try fuzzy match
            target_texts = list(target_vocab.values())
            matches = difflib.get_close_matches(
                source_text,
                target_texts,
                n=1,
                cutoff=self.config.fuzzy_threshold
            )
            
            if matches:
                best_match = matches[0]
                target_id = [tid for tid, text in target_vocab.items() if text == best_match][0]
                confidence = difflib.SequenceMatcher(None, source_text, best_match).ratio()
                
                mapping = TokenMapping(
                    source_id=source_id,
                    target_id=target_id,
                    source_text=source_text,
                    target_text=best_match,
                    confidence=confidence,
                    strategy_used="fuzzy"
                )
                mappings.append(mapping)
                source_to_target[source_id].append((target_id, confidence))
                target_to_source[target_id].append((source_id, confidence))
                strategy_stats["fuzzy"] += 1
                continue
            
            # 3. Try subword matching as fallback
            if self.config.subword_fallback:
                source_subwords = self._extract_subwords(source_text)
                best_match = None
                best_score = 0
                
                for target_id, target_text in target_vocab.items():
                    target_subs = self._extract_subwords(target_text)
                    score = self._subword_similarity(source_subwords, target_subs)
                    if score > best_score and score >= 0.3:
                        best_score = score
                        best_match = (target_id, target_text)
                
                if best_match:
                    target_id, target_text = best_match
                    mapping = TokenMapping(
                        source_id=source_id,
                        target_id=target_id,
                        source_text=source_text,
                        target_text=target_text,
                        confidence=best_score,
                        strategy_used="subword"
                    )
                    mappings.append(mapping)
                    source_to_target[source_id].append((target_id, best_score))
                    target_to_source[target_id].append((source_id, best_score))
                    strategy_stats["subword"] += 1
        
        return VocabularyAlignment(
            mappings=mappings,
            source_to_target=dict(source_to_target),
            target_to_source=dict(target_to_source),
            common_tokens=set(),
            source_only=set(),
            target_only=set(),
            overlap_ratio=0.0,
            alignment_quality=0.0,
            strategy_stats=dict(strategy_stats)
        )
    
    def _extract_subwords(self, text: str) -> List[str]:
        """Extract subwords from a token text"""
        # Remove special token markers
        text = text.replace("▁", "").replace("##", "").replace("Ġ", "")
        
        # Split by common delimiters
        subwords = []
        
        # Split camelCase
        parts = re.findall(r'[A-Z][a-z]+|[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', text)
        subwords.extend([p.lower() for p in parts])
        
        # Split by underscores and hyphens
        for delimiter in ['_', '-']:
            if delimiter in text:
                subwords.extend(text.split(delimiter))
        
        # Add the original text too
        subwords.append(text.lower())
        
        return list(set(subwords))
    
    def _subword_similarity(self, subwords1: List[str], subwords2: List[str]) -> float:
        """Calculate similarity between two sets of subwords"""
        if not subwords1 or not subwords2:
            return 0.0
        
        set1 = set(subwords1)
        set2 = set(subwords2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_statistics(
        self,
        alignment: VocabularyAlignment,
        source_vocab: Dict[int, str],
        target_vocab: Dict[int, str]
    ) -> VocabularyAlignment:
        """Calculate alignment statistics"""
        source_texts = set(source_vocab.values())
        target_texts = set(target_vocab.values())
        
        alignment.common_tokens = source_texts & target_texts
        alignment.source_only = source_texts - target_texts
        alignment.target_only = target_texts - source_texts
        
        total_source = len(source_texts)
        if total_source > 0:
            alignment.overlap_ratio = len(alignment.common_tokens) / total_source
        
        # Calculate alignment quality based on confidence scores
        if alignment.mappings:
            avg_confidence = sum(m.confidence for m in alignment.mappings) / len(alignment.mappings)
            coverage = len(alignment.mappings) / len(source_vocab)
            alignment.alignment_quality = avg_confidence * coverage
        
        return alignment
    
    def _print_summary(self, alignment: VocabularyAlignment):
        """Print alignment summary"""
        print("\n" + "="*60)
        print("Vocabulary Alignment Summary")
        print("="*60)
        print(f"Total mappings: {len(alignment.mappings)}")
        print(f"Overlap ratio: {alignment.overlap_ratio:.2%}")
        print(f"Alignment quality: {alignment.alignment_quality:.2%}")
        print(f"Common tokens: {len(alignment.common_tokens)}")
        print(f"Source-only tokens: {len(alignment.source_only)}")
        print(f"Target-only tokens: {len(alignment.target_only)}")
        
        if alignment.strategy_stats:
            print("\nStrategies used:")
            for strategy, count in alignment.strategy_stats.items():
                print(f"  {strategy}: {count}")
        
        if alignment.mappings:
            # Show some example mappings
            print("\nExample mappings (top 5 by confidence):")
            sorted_mappings = sorted(alignment.mappings, key=lambda m: m.confidence, reverse=True)[:5]
            for m in sorted_mappings:
                print(f"  '{m.source_text}' -> '{m.target_text}' "
                      f"(conf: {m.confidence:.2f}, strategy: {m.strategy_used})")
        print("="*60)
    
    def translate_logits(
        self,
        source_logits: np.ndarray,
        alignment: VocabularyAlignment,
        fallback_value: float = -100.0,
        temperature: float = 1.0
    ) -> np.ndarray:
        """Translate logits from source to target vocabulary"""
        vocab_size = max(alignment.target_to_source.keys()) + 1 if alignment.target_to_source else len(source_logits)
        target_logits = np.full(vocab_size, fallback_value, dtype=np.float32)
        
        for source_id, logit_value in enumerate(source_logits):
            if source_id in alignment.source_to_target:
                # Get all possible target mappings
                for target_id, confidence in alignment.source_to_target[source_id]:
                    # Weight the logit by confidence
                    weighted_logit = logit_value
                    if self.config.confidence_weighting:
                        weighted_logit *= confidence
                    
                    # Take the maximum if multiple sources map to same target
                    target_logits[target_id] = max(target_logits[target_id], weighted_logit)
        
        # Apply temperature
        if temperature != 1.0:
            target_logits = target_logits / temperature
        
        return target_logits