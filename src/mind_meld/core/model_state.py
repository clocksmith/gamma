"""Model state management for Mind Meld"""

from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict, Tuple
import time
import copy


@dataclass
class StateSnapshot:
    """Snapshot of a model's state at a specific point"""
    timestamp: float
    token_position: int
    kv_cache: Optional[Any] = None
    hidden_states: Optional[Any] = None
    attention_weights: Optional[Any] = None
    logits: Optional[Any] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def clone(self) -> 'StateSnapshot':
        """Create a deep copy of the snapshot"""
        return StateSnapshot(
            timestamp=self.timestamp,
            token_position=self.token_position,
            kv_cache=copy.deepcopy(self.kv_cache) if self.kv_cache is not None else None,
            hidden_states=copy.deepcopy(self.hidden_states) if self.hidden_states is not None else None,
            attention_weights=copy.deepcopy(self.attention_weights) if self.attention_weights is not None else None,
            logits=copy.deepcopy(self.logits) if self.logits is not None else None,
            confidence=self.confidence,
            metadata=copy.deepcopy(self.metadata)
        )


@dataclass
class ModelState:
    """Track state for a single model in the meld system"""
    engine: Any  # LLMEngine instance
    name: str
    model_id: str
    
    # Current state
    input_ids: Any = None
    attention_mask: Optional[Any] = None
    position_ids: Optional[Any] = None
    
    # Cache and hidden states
    kv_cache: Optional[Any] = None
    last_hidden_states: Optional[Any] = None
    last_attention: Optional[Any] = None
    last_logits: Optional[Any] = None
    
    # Vocabulary information
    vocab_size: int = 0
    vocab_mapping: Optional[Dict[int, int]] = None  # Mapping to common vocabulary
    special_tokens: Dict[str, int] = field(default_factory=dict)
    
    # Statistics and history
    token_count: int = 0
    confidence_history: List[float] = field(default_factory=list)
    perplexity_history: List[float] = field(default_factory=list)
    attention_entropy_history: List[float] = field(default_factory=list)
    
    # State snapshots for rollback
    snapshots: List[StateSnapshot] = field(default_factory=list)
    max_snapshots: int = 10
    
    # Model-specific metadata
    hidden_size: Optional[int] = None
    num_layers: Optional[int] = None
    num_heads: Optional[int] = None
    head_dim: Optional[int] = None
    context_length: Optional[int] = None
    
    def __post_init__(self):
        """Initialize model-specific information"""
        if self.engine:
            self.vocab_size = self.engine.get_vocabulary_size()
            self._extract_model_metadata()
    
    def _extract_model_metadata(self):
        """Extract metadata from the model"""
        try:
            if hasattr(self.engine, 'model') and self.engine.model:
                model = self.engine.model
                config = getattr(model, 'config', None)
                
                if config:
                    self.hidden_size = getattr(config, 'hidden_size', None)
                    self.num_layers = getattr(config, 'num_layers', 
                                            getattr(config, 'n_layers', None))
                    self.num_heads = getattr(config, 'num_attention_heads',
                                           getattr(config, 'n_heads', None))
                    if self.hidden_size and self.num_heads:
                        self.head_dim = self.hidden_size // self.num_heads
                    self.context_length = getattr(config, 'max_position_embeddings',
                                                 getattr(config, 'n_positions', None))
        except Exception:
            pass  # Silently ignore if metadata extraction fails
    
    def save_snapshot(self, include_cache: bool = True, include_hidden: bool = True):
        """Save current state as a snapshot"""
        snapshot = StateSnapshot(
            timestamp=time.time(),
            token_position=self.token_count,
            kv_cache=copy.deepcopy(self.kv_cache) if include_cache and self.kv_cache else None,
            hidden_states=copy.deepcopy(self.last_hidden_states) if include_hidden and self.last_hidden_states else None,
            attention_weights=copy.deepcopy(self.last_attention) if self.last_attention else None,
            logits=copy.deepcopy(self.last_logits) if self.last_logits else None,
            confidence=self.confidence_history[-1] if self.confidence_history else 0.0,
            metadata={
                'input_length': len(self.input_ids) if self.input_ids is not None else 0,
                'perplexity': self.perplexity_history[-1] if self.perplexity_history else 0.0,
            }
        )
        
        self.snapshots.append(snapshot)
        
        # Limit snapshot history
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots.pop(0)
    
    def restore_snapshot(self, snapshot_idx: int = -1) -> bool:
        """Restore state from a snapshot"""
        if not self.snapshots:
            return False
        
        try:
            snapshot = self.snapshots[snapshot_idx]
            
            if snapshot.kv_cache is not None:
                self.kv_cache = copy.deepcopy(snapshot.kv_cache)
                self.engine._kv_cache = self.kv_cache
            
            if snapshot.hidden_states is not None:
                self.last_hidden_states = copy.deepcopy(snapshot.hidden_states)
            
            if snapshot.attention_weights is not None:
                self.last_attention = copy.deepcopy(snapshot.attention_weights)
            
            if snapshot.logits is not None:
                self.last_logits = copy.deepcopy(snapshot.logits)
            
            return True
        except Exception:
            return False
    
    def reset(self):
        """Reset the model state"""
        self.input_ids = None
        self.attention_mask = None
        self.position_ids = None
        self.kv_cache = None
        self.last_hidden_states = None
        self.last_attention = None
        self.last_logits = None
        self.token_count = 0
        self.confidence_history.clear()
        self.perplexity_history.clear()
        self.attention_entropy_history.clear()
        self.snapshots.clear()
        
        if self.engine:
            self.engine.reset_kv_cache()
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of the current state"""
        return {
            'name': self.name,
            'model_id': self.model_id,
            'token_count': self.token_count,
            'vocab_size': self.vocab_size,
            'has_kv_cache': self.kv_cache is not None,
            'has_hidden_states': self.last_hidden_states is not None,
            'avg_confidence': sum(self.confidence_history) / len(self.confidence_history) if self.confidence_history else 0.0,
            'avg_perplexity': sum(self.perplexity_history) / len(self.perplexity_history) if self.perplexity_history else 0.0,
            'num_snapshots': len(self.snapshots),
            'context_used': len(self.input_ids) if self.input_ids is not None else 0,
            'metadata': {
                'hidden_size': self.hidden_size,
                'num_layers': self.num_layers,
                'num_heads': self.num_heads,
                'context_length': self.context_length,
            }
        }