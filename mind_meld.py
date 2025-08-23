#!/usr/bin/env python3
"""
Mind Meld - Neural State Swapping Between Multiple LLMs
Generates text by swapping internal states (KV cache, attention, hidden states) between models
"""

import argparse
import sys
import time
import copy
from typing import List, Tuple, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

# Add v2 directory to path
sys.path.insert(0, 'v2')

from v2.core import config as cfg
from v2.core import ui
from v2.engines.engine_factory import get_engine, SUPPORTED_ENGINES
from v2.core.engine_interface import LLMEngine


class SwapStrategy(Enum):
    """Different strategies for swapping model states"""
    FIXED_INTERVAL = "fixed_interval"  # Swap every N tokens
    PATTERN_BASED = "pattern"  # Swap on patterns (punctuation, etc)
    CONFIDENCE_BASED = "confidence"  # Swap when confidence drops
    ROUND_ROBIN = "round_robin"  # Rotate through models
    WEIGHTED_BLEND = "weighted"  # Blend states with weights
    RANDOM = "random"  # Random swapping


@dataclass
class SwapConfig:
    """Configuration for state swapping"""
    strategy: SwapStrategy
    interval: int = 2  # For fixed interval
    min_confidence: float = 0.7  # For confidence-based
    blend_weights: List[float] = None  # For weighted blending
    swap_components: List[str] = None  # Which components to swap
    pattern: str = "punctuation"  # For pattern-based
    temperature_sync: bool = True  # Sync sampling parameters
    verbose: bool = True


@dataclass
class ModelState:
    """Track state for a single model"""
    engine: LLMEngine
    name: str
    input_ids: Any
    attention_mask: Optional[Any]
    kv_cache: Optional[Any]
    last_hidden_states: Optional[Any]
    last_attention: Optional[Any]
    token_count: int = 0
    confidence_history: List[float] = None
    
    def __post_init__(self):
        if self.confidence_history is None:
            self.confidence_history = []


class MindMeldEngine:
    """Manages multiple LLMs and swaps their internal states during generation"""
    
    def __init__(self, model_configs: List[Tuple[str, str]], swap_config: SwapConfig):
        """
        Initialize with multiple models
        
        Args:
            model_configs: List of (engine_type, model_name) tuples
            swap_config: Configuration for state swapping
        """
        self.model_configs = model_configs
        self.swap_config = swap_config
        self.model_states: List[ModelState] = []
        self.swap_history: List[Dict[str, Any]] = []
        self.current_model_idx = 0
        self.token_counter = 0
        self.generated_tokens: List[Tuple[str, int]] = []  # (token, model_idx)
        self.tokenizers_compatible = True  # Track if tokenizers are compatible
        
    def load_models(self) -> bool:
        """Load all models and initialize their states"""
        print(ui.color_text("\n🧠 Loading models for Mind Meld...", cfg.COLOR_CYAN))
        
        for engine_type, model_name in self.model_configs:
            try:
                print(f"\nLoading {model_name} with {engine_type} engine...")
                
                # Create engine config
                engine_config = {
                    'temperature': 1.0,
                    'top_k': 50,
                    'top_p': 0.95,
                    'use_kv_cache': True,  # Essential for state swapping
                }
                
                # Load engine
                engine = get_engine(engine_type, model_name, engine_config)
                engine.load()
                
                # Create model state
                state = ModelState(
                    engine=engine,
                    name=model_name.split('/')[-1],
                    input_ids=None,
                    attention_mask=None,
                    kv_cache=None,
                    last_hidden_states=None,
                    last_attention=None
                )
                
                self.model_states.append(state)
                print(ui.color_text(f"✓ {model_name} loaded", cfg.COLOR_GREEN))
                
            except Exception as e:
                print(ui.color_text(f"✗ Failed to load {model_name}: {e}", cfg.COLOR_RED))
                return False
        
        if len(self.model_states) < 2:
            print(ui.color_text("\n⚠️ Need at least 2 models for mind melding", cfg.COLOR_YELLOW))
            return False
        
        # Check if models are actually different
        model_names = [state.engine.model_name for state in self.model_states]
        if len(set(model_names)) == 1:
            print(ui.color_text(
                f"\n⚠️ Warning: You're using the same model multiple times: {model_names[0]}",
                cfg.COLOR_YELLOW
            ))
            print("Mind melding works best with DIFFERENT models. Try:")
            print("  - google/gemma-2b-it vs google/gemma-2b (instruct vs base)")
            print("  - google/gemma-2-2b-it vs google/gemma-2b-it (different sizes)")
            print("  - TinyLlama/TinyLlama-1.1B-Chat-v1.0 vs TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T")
            response = input("\nContinue with identical models anyway? (y/n): ")
            if response.lower() != 'y':
                return False
        
        # Validate model compatibility
        if not self._validate_model_compatibility():
            return False
            
        print(ui.color_text(f"\n✓ Loaded {len(self.model_states)} models successfully!", cfg.COLOR_GREEN))
        return True
    
    def _validate_model_compatibility(self) -> bool:
        """Check if models are compatible for state swapping"""
        # Check vocabulary sizes
        vocab_sizes = [state.engine.get_vocabulary_size() for state in self.model_states]
        
        if len(set(vocab_sizes)) > 1:
            print(ui.color_text(
                f"\n⚠️ Warning: Models have different vocabulary sizes: {vocab_sizes}",
                cfg.COLOR_YELLOW
            ))
            print("State swapping may produce unexpected results.")
            
            # Check tokenizer alignment for common tokens
            print("\n🔍 Checking token alignment...")
            test_phrases = [" the", " ", ".", ",", "\n", " is", " and", " AI"]
            misaligned = 0
            
            for phrase in test_phrases:
                token_ids = []
                for state in self.model_states:
                    try:
                        # Encode without special tokens
                        ids, _ = state.engine.encode(phrase, add_special_tokens=False)
                        # Get first token ID
                        first_id = self._get_first_token_id(ids)
                        token_ids.append(first_id)
                    except:
                        token_ids.append(-1)
                
                # Check if all models produce the same token ID
                if len(set(token_ids)) > 1:
                    misaligned += 1
                    if misaligned <= 3:  # Show first few misalignments
                        print(f"  ❌ '{phrase}' maps to different IDs: {token_ids}")
            
            if misaligned > 0:
                print(f"\n⚠️ Found {misaligned}/{len(test_phrases)} token misalignments!")
                print("Models use incompatible tokenizers. Results will be unpredictable.")
                self.tokenizers_compatible = False  # Mark as incompatible
                print("\n💡 Suggestion: Use models from the same family:")
                print("  - Gemma models: gemma-2b-it, gemma-2-2b-it, gemma-2-9b-it")
                print("  - Mistral models: Mistral-7B-v0.1, Mistral-7B-Instruct")
                print("  - Llama models: Llama-3.2-1B, Llama-3.2-3B")
            
            response = input("\nContinue anyway? (y/n): ")
            if response.lower() != 'y':
                return False
        
        return True
    
    def swap_kv_caches(self, model_a_idx: int, model_b_idx: int) -> None:
        """Swap KV caches between two models"""
        state_a = self.model_states[model_a_idx]
        state_b = self.model_states[model_b_idx]
        
        # If tokenizers are incompatible OR if models are identical, reset instead of swap
        if not self.tokenizers_compatible or state_a.name == state_b.name:
            # Clear both caches to avoid issues
            state_a.engine.reset_kv_cache()
            state_b.engine.reset_kv_cache()
            
            if self.swap_config.verbose:
                if state_a.name == state_b.name:
                    print(f"\n🔄 Reset KV caches (same model): {state_a.name}")
                else:
                    print(f"\n🔄 Reset KV caches (incompatible): {state_a.name}, {state_b.name}")
            
            # Record as a reset rather than swap
            self.swap_history.append({
                'token_position': self.token_counter,
                'swap_type': 'kv_reset',
                'models': (model_a_idx, model_b_idx),
                'timestamp': time.time()
            })
            return
        
        # Store original caches
        cache_a = state_a.engine._kv_cache
        cache_b = state_b.engine._kv_cache
        
        # Only swap if both caches exist
        if cache_a is None or cache_b is None:
            if self.swap_config.verbose:
                print(f"\n⚠️ Cannot swap: cache_a={cache_a is not None}, cache_b={cache_b is not None}")
                print(f"  Models: {state_a.name} (cache: {cache_a is not None}), {state_b.name} (cache: {cache_b is not None})")
            return
        
        # Swap caches
        state_a.engine._kv_cache = cache_b
        state_b.engine._kv_cache = cache_a
        
        # Update state tracking
        state_a.kv_cache = cache_b
        state_b.kv_cache = cache_a
        
        # Record swap
        self.swap_history.append({
            'token_position': self.token_counter,
            'swap_type': 'kv_cache',
            'models': (model_a_idx, model_b_idx),
            'timestamp': time.time()
        })
        
        if self.swap_config.verbose:
            print(f"\n🔄 Swapped KV cache: {state_a.name} ↔ {state_b.name}")
    
    def blend_hidden_states(self, states: List[Any], weights: List[float]) -> Any:
        """Blend hidden states from multiple models"""
        if not states or not all(s is not None for s in states):
            return states[0] if states else None
        
        # Get the tensor type from first state
        first_state = states[0]
        
        try:
            if "torch" in sys.modules and hasattr(first_state, "dtype"):
                # PyTorch tensors
                import torch
                blended = torch.zeros_like(first_state)
                for state, weight in zip(states, weights):
                    blended += weight * state
                return blended
                
            elif "mlx" in sys.modules and hasattr(first_state, "dtype"):
                # MLX arrays
                import mlx.core as mx
                blended = mx.zeros_like(first_state)
                for state, weight in zip(states, weights):
                    blended = blended + weight * state
                return blended
                
            elif "numpy" in sys.modules:
                # NumPy arrays
                import numpy as np
                blended = np.zeros_like(first_state)
                for state, weight in zip(states, weights):
                    blended += weight * state
                return blended
                
        except Exception as e:
            if self.swap_config.verbose:
                print(f"⚠️ Could not blend hidden states: {e}")
        
        return first_state
    
    def should_swap(self, current_token: str, confidence: float) -> bool:
        """Determine if we should swap states based on strategy"""
        strategy = self.swap_config.strategy
        
        if strategy == SwapStrategy.FIXED_INTERVAL:
            # Token counter is now incremented BEFORE this check
            # Don't swap on the very first few tokens
            if self.token_counter < 2:
                return False
            return (self.token_counter % self.swap_config.interval) == 0
            
        elif strategy == SwapStrategy.CONFIDENCE_BASED:
            return confidence < self.swap_config.min_confidence
            
        elif strategy == SwapStrategy.PATTERN_BASED:
            if self.swap_config.pattern == "punctuation":
                return current_token.strip() in ".,!?;:"
            elif self.swap_config.pattern == "newline":
                return "\n" in current_token
            elif self.swap_config.pattern == "word_boundary":
                return current_token.strip() == "" or current_token.startswith(" ")
                
        elif strategy == SwapStrategy.ROUND_ROBIN:
            return True  # Always swap in round-robin
            
        elif strategy == SwapStrategy.RANDOM:
            import random
            return random.random() < 0.3  # 30% chance
            
        return False
    
    def get_next_model_indices(self) -> Tuple[int, int]:
        """Get indices for next model swap based on strategy"""
        num_models = len(self.model_states)
        
        if self.swap_config.strategy == SwapStrategy.ROUND_ROBIN:
            current = self.current_model_idx
            next_idx = (current + 1) % num_models
            return current, next_idx
            
        else:
            # For other strategies, swap between first two models by default
            # Or implement more complex selection logic
            return 0, 1
    
    def generate_melded_text(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 1.0,
        top_k: int = 50,
        top_p: float = 0.95
    ) -> str:
        """
        Generate text with state swapping between models
        
        Args:
            prompt: Initial text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_k: Top-k filtering
            top_p: Top-p (nucleus) filtering
            
        Returns:
            Generated text with mind melding
        """
        print(ui.color_text("\n🧬 Starting Mind Meld Generation...", cfg.COLOR_CYAN))
        print(f"Strategy: {self.swap_config.strategy.value}")
        print(f"Models: {[s.name for s in self.model_states]}")
        ui.print_separator()
        
        # Initialize all models with the prompt
        for state in self.model_states:
            input_ids, attention_mask = state.engine.encode(prompt, add_special_tokens=True)
            state.input_ids = input_ids
            state.attention_mask = attention_mask
            state.engine.reset_kv_cache()
        
        generated_text = ""
        self.token_counter = 0
        self.generated_tokens = []
        
        print(f"\n📝 Prompt: {prompt}")
        print("\n🔮 Generating with mind meld:\n")
        
        # Main generation loop
        for step in range(max_tokens):
            # Select active model
            if self.swap_config.strategy == SwapStrategy.ROUND_ROBIN:
                active_idx = self.current_model_idx
            else:
                active_idx = 0  # Default to first model
            
            active_state = self.model_states[active_idx]
            
            # Get prediction from active model
            try:
                # For KV cache to work, we should only pass the last token after first generation
                if active_state.engine._kv_cache is not None:
                    # Use only the last token ID with the cached context
                    last_token_id = active_state.input_ids[..., -1:]
                    last_attention = active_state.attention_mask[..., -1:] if active_state.attention_mask is not None else None
                    
                    result = active_state.engine.predict_next(
                        last_token_id,
                        last_attention,
                        temperature=temperature,
                        top_k=top_k,
                        top_p=top_p,
                        output_attentions=True,
                        output_hidden_states=True
                    )
                else:
                    # First generation - use full sequence
                    result = active_state.engine.predict_next(
                        active_state.input_ids,
                        active_state.attention_mask,
                        temperature=temperature,
                        top_k=top_k,
                        top_p=top_p,
                        output_attentions=True,
                        output_hidden_states=True
                    )
                
                # Extract token and metadata
                next_token_id = result['next_token_id']
                next_token = active_state.engine.get_token_text(next_token_id)
                confidence = result['top_probs_processed'][0] if result['top_probs_processed'] else 0.5
                
                # Store the original token ID for proper propagation
                original_token_id = next_token_id
                
                # Store hidden states and attention if available
                if 'hidden_states' in result and result['hidden_states'] is not None:
                    active_state.last_hidden_states = result['hidden_states']
                if 'attention' in result and result['attention'] is not None:
                    active_state.last_attention = result['attention']
                
                # Track confidence
                active_state.confidence_history.append(confidence)
                
                # Display token with model indicator
                if self.swap_config.verbose:
                    model_indicator = f"[{active_state.name[:3]}]"
                    print(f"{model_indicator}{next_token}", end="", flush=True)
                else:
                    print(next_token, end="", flush=True)
                
                # Check for EOS
                if hasattr(active_state.engine.tokenizer, 'eos_token_id'):
                    if next_token_id == active_state.engine.tokenizer.eos_token_id:
                        print(ui.color_text("\n\n<End of Sequence>", cfg.COLOR_YELLOW))
                        break
                
                # Update generated text and tokens
                generated_text += next_token
                self.generated_tokens.append((next_token, active_idx))
                
                # Update all models' inputs
                for state in self.model_states:
                    # Try to use original token ID if it's within the model's vocabulary
                    vocab_size = state.engine.get_vocabulary_size()
                    
                    if vocab_size > 0 and original_token_id < vocab_size:
                        # Token ID is valid for this model - use it directly
                        # This preserves the exact token across models
                        new_ids = self._create_tensor_from_id(state.input_ids, original_token_id)
                        
                        # Create attention mask
                        if state.attention_mask is not None:
                            new_mask = self._create_tensor_from_id(state.attention_mask, 1)
                        else:
                            new_mask = None
                            
                        if self.swap_config.verbose and state != active_state:
                            # Check if token text would be different
                            alt_text = state.engine.get_token_text(original_token_id)
                            if alt_text != next_token:
                                print(f"\n  ⚠️ Token mismatch in {state.name}: '{next_token}' vs '{alt_text}'", end="")
                    else:
                        # Token ID is out of bounds - must re-encode
                        new_ids, new_mask = state.engine.encode(next_token, add_special_tokens=False)
                        
                        if self.swap_config.verbose:
                            if new_ids is not None:
                                # Get the first token ID from the tensor
                                remapped_id = self._get_first_token_id(new_ids)
                                if remapped_id != original_token_id:
                                    print(f"\n  ⚠️ Token remapped in {state.name}: {original_token_id} → {remapped_id}", end="")
                    
                    state.input_ids = self._concat_tensors(state.input_ids, new_ids)
                    if state.attention_mask is not None and new_mask is not None:
                        state.attention_mask = self._concat_tensors(state.attention_mask, new_mask)
                
                # Also update non-active models to maintain their KV caches
                for i, state in enumerate(self.model_states):
                    if i != active_idx:
                        # Non-active models need to process the token too to maintain cache
                        try:
                            if state.engine._kv_cache is not None:
                                # Use only last token with cache
                                last_id = state.input_ids[..., -1:]
                                last_mask = state.attention_mask[..., -1:] if state.attention_mask is not None else None
                            else:
                                # Full sequence for first time
                                last_id = state.input_ids
                                last_mask = state.attention_mask
                            
                            # Run predict to update cache (we ignore the output)
                            _ = state.engine.predict_next(
                                last_id,
                                last_mask,
                                temperature=1.0,
                                top_k=1,
                                top_p=1.0,
                                output_attentions=False,
                                output_hidden_states=False
                            )
                        except:
                            pass  # Ignore errors for non-active models
                
                # Increment counter BEFORE swap check
                self.token_counter += 1
                
                # Check if we should swap states
                if self.should_swap(next_token, confidence):
                    model_a_idx, model_b_idx = self.get_next_model_indices()
                    
                    # Perform swap based on components
                    if 'kv_cache' in (self.swap_config.swap_components or ['kv_cache']):
                        self.swap_kv_caches(model_a_idx, model_b_idx)
                    
                    # Update current model for round-robin
                    if self.swap_config.strategy == SwapStrategy.ROUND_ROBIN:
                        self.current_model_idx = (self.current_model_idx + 1) % len(self.model_states)
                
            except Exception as e:
                print(ui.color_text(f"\n\n❌ Error during generation: {e}", cfg.COLOR_RED))
                if self.swap_config.verbose:
                    import traceback
                    traceback.print_exc()
                break
        
        # Generate individual model outputs for comparison
        print(ui.color_text("\n\n🔬 Generating individual model outputs for comparison...", cfg.COLOR_CYAN))
        individual_outputs = self._generate_individual_outputs(prompt, len(self.generated_tokens))
        
        # Display summary with comparisons
        self._display_summary(prompt, individual_outputs)
        
        return prompt + generated_text
    
    def _generate_individual_outputs(self, prompt: str, num_tokens: int) -> Dict[str, str]:
        """Generate outputs from each model individually without swapping"""
        individual_outputs = {}
        
        for state in self.model_states:
            # Reset the model's KV cache
            state.engine.reset_kv_cache()
            
            # Encode the prompt
            input_ids, attention_mask = state.engine.encode(prompt, add_special_tokens=True)
            
            generated_text = ""
            
            # Generate tokens without swapping
            for _ in range(num_tokens):
                try:
                    result = state.engine.predict_next(
                        input_ids,
                        attention_mask,
                        temperature=1.0,  # Use same temperature as main generation
                        top_k=50,
                        top_p=0.95,
                        output_attentions=False,
                        output_hidden_states=False
                    )
                    
                    next_token_id = result['next_token_id']
                    next_token = state.engine.get_token_text(next_token_id)
                    
                    # Check for EOS
                    if hasattr(state.engine.tokenizer, 'eos_token_id'):
                        if next_token_id == state.engine.tokenizer.eos_token_id:
                            break
                    
                    generated_text += next_token
                    
                    # Update input for next iteration
                    new_ids, new_mask = state.engine.encode(next_token, add_special_tokens=False)
                    input_ids = self._concat_tensors(input_ids, new_ids)
                    if attention_mask is not None and new_mask is not None:
                        attention_mask = self._concat_tensors(attention_mask, new_mask)
                    
                except Exception as e:
                    print(f"  ⚠️ Error generating for {state.name}: {e}")
                    break
            
            individual_outputs[state.name] = generated_text
            
            # Reset cache again for cleanliness
            state.engine.reset_kv_cache()
        
        return individual_outputs
    
    def _create_tensor_from_id(self, reference_tensor: Any, token_id: int) -> Any:
        """Create a tensor containing a single token ID, matching the type of reference tensor"""
        try:
            if "torch" in sys.modules:
                import torch
                if isinstance(reference_tensor, torch.Tensor):
                    # Create tensor on same device as reference
                    return torch.tensor([token_id], dtype=reference_tensor.dtype, device=reference_tensor.device)
            
            elif "mlx" in sys.modules:
                import mlx.core as mx
                if hasattr(reference_tensor, "dtype"):
                    return mx.array([token_id], dtype=reference_tensor.dtype)
            
            elif "tensorflow" in sys.modules:
                import tensorflow as tf
                if isinstance(reference_tensor, tf.Tensor):
                    return tf.constant([token_id], dtype=reference_tensor.dtype)
            
            elif "numpy" in sys.modules:
                import numpy as np
                if isinstance(reference_tensor, np.ndarray):
                    return np.array([token_id], dtype=reference_tensor.dtype)
            
            # Fallback to list
            return [token_id]
            
        except Exception:
            return [token_id]
    
    def _get_first_token_id(self, tensor: Any) -> int:
        """Extract the first token ID from a tensor"""
        try:
            if "torch" in sys.modules:
                import torch
                if isinstance(tensor, torch.Tensor):
                    return int(tensor[0].item())
            
            elif "mlx" in sys.modules:
                import mlx.core as mx
                if hasattr(tensor, "item"):
                    return int(tensor[0].item())
            
            elif "numpy" in sys.modules:
                import numpy as np
                if isinstance(tensor, np.ndarray):
                    return int(tensor[0])
            
            if isinstance(tensor, (list, tuple)):
                return int(tensor[0])
                
        except Exception:
            pass
        
        return -1
    
    def _concat_tensors(self, tensor1: Any, tensor2: Any) -> Any:
        """Concatenate tensors based on their type"""
        if tensor1 is None:
            return tensor2
        if tensor2 is None:
            return tensor1
        
        try:
            # PyTorch
            if "torch" in sys.modules:
                import torch
                if isinstance(tensor1, torch.Tensor) and isinstance(tensor2, torch.Tensor):
                    # Ensure both tensors are on the same device
                    if tensor1.device != tensor2.device:
                        tensor2 = tensor2.to(tensor1.device)
                    # Handle different dimensions
                    if tensor1.dim() == 1 and tensor2.dim() == 1:
                        return torch.cat([tensor1, tensor2], dim=0)
                    else:
                        return torch.cat([tensor1, tensor2], dim=-1)
            
            # MLX
            elif "mlx" in sys.modules and hasattr(tensor1, "reshape"):
                import mlx.core as mx
                return mx.concatenate([tensor1, tensor2], axis=-1)
            
            # TensorFlow
            elif "tensorflow" in sys.modules and hasattr(tensor1, "shape"):
                import tensorflow as tf
                return tf.concat([tensor1, tensor2], axis=-1)
            
            # NumPy
            elif "numpy" in sys.modules:
                import numpy as np
                # Handle PyTorch tensors that need to be converted
                if hasattr(tensor1, 'cpu'):
                    tensor1 = tensor1.cpu().numpy()
                if hasattr(tensor2, 'cpu'):
                    tensor2 = tensor2.cpu().numpy()
                return np.concatenate([tensor1, tensor2], axis=-1)
            
            # Lists
            elif isinstance(tensor1, list):
                return tensor1 + tensor2
                
        except Exception as e:
            # Silently handle the error and return the first tensor
            pass
        
        return tensor1
    
    def _display_summary(self, prompt: str, individual_outputs: Dict[str, str]) -> None:
        """Display generation summary with comparisons"""
        print("\n\n" + "="*60)
        print(ui.color_text("📊 Mind Meld Summary", cfg.COLOR_CYAN))
        print("="*60)
        
        # Display the complete melded text
        print("\n🧬 MELDED OUTPUT:")
        # Join tokens properly - many tokens don't include spaces
        complete_text = prompt
        for i, (token, _) in enumerate(self.generated_tokens):
            # Add space before token if it doesn't start with space and previous doesn't end with space
            if i > 0 and token and not token.startswith(' ') and not token.startswith('\n'):
                prev_token = self.generated_tokens[i-1][0]
                # Don't add space after punctuation that typically doesn't need it
                if not prev_token.rstrip().endswith(('.', ',', '!', '?', ';', ':', '\n', '"', "'")):
                    # Check if the token looks like it should have a space
                    if token[0].isalnum() or token[0] in ('(', '[', '{'):
                        complete_text += ' '
            complete_text += token
        complete_text = complete_text.strip()
        print(ui.color_text(f'"{complete_text}"', cfg.COLOR_GREEN))
        
        # Display individual model outputs
        print("\n📝 INDIVIDUAL MODEL OUTPUTS (without swapping):")
        for model_name, output in individual_outputs.items():
            # The individual outputs are already properly formatted by the model
            individual_text = prompt + output
            individual_text = individual_text.strip()
            print(f"\n{model_name}:")
            print(ui.color_text(f'  "{individual_text}"', cfg.COLOR_YELLOW))
        
        # Token contribution by model
        print("\n🎯 Token Contributions in Melded Output:")
        for i, state in enumerate(self.model_states):
            count = sum(1 for _, idx in self.generated_tokens if idx == i)
            percentage = (count / len(self.generated_tokens) * 100) if self.generated_tokens else 0
            print(f"  {state.name}: {count} tokens ({percentage:.1f}%)")
        
        # Swap statistics
        print(f"\n🔄 Total Swaps: {len(self.swap_history)}")
        if self.swap_history:
            swap_positions = [s['token_position'] for s in self.swap_history[:10]]
            if len(self.swap_history) > 10:
                print(f"  Swap positions (first 10): {swap_positions}")
            else:
                print(f"  Swap positions: {swap_positions}")
        
        # Confidence statistics
        print("\n📈 Average Confidence by Model:")
        for state in self.model_states:
            if state.confidence_history:
                avg_conf = sum(state.confidence_history) / len(state.confidence_history)
                print(f"  {state.name}: {avg_conf:.3f}")


def main():
    """Main entry point for Mind Meld"""
    parser = argparse.ArgumentParser(
        description="Mind Meld - Generate text by swapping neural states between LLMs",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Model selection
    parser.add_argument(
        "--models",
        nargs="+",
        required=True,
        help="Models to meld (format: model_name or engine:model_name)"
    )
    
    # Swap configuration
    parser.add_argument(
        "--swap-strategy",
        choices=[s.value for s in SwapStrategy],
        default=SwapStrategy.FIXED_INTERVAL.value,
        help="Strategy for swapping states"
    )
    parser.add_argument(
        "--swap-interval",
        type=int,
        default=2,
        help="Tokens between swaps (for fixed_interval strategy)"
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.7,
        help="Minimum confidence threshold (for confidence strategy)"
    )
    parser.add_argument(
        "--swap-components",
        nargs="+",
        choices=["kv_cache", "hidden_states", "attention"],
        default=["kv_cache"],
        help="Which components to swap"
    )
    
    # Generation parameters
    parser.add_argument(
        "--prompt",
        type=str,
        default="The future of artificial intelligence",
        help="Starting prompt for generation"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=100,
        help="Maximum tokens to generate"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=1.0,
        help="Sampling temperature"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=50,
        help="Top-k filtering"
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=0.95,
        help="Top-p (nucleus) filtering"
    )
    
    # Display options
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed swap information"
    )
    
    args = parser.parse_args()
    
    # Parse model specifications
    model_configs = []
    for model_spec in args.models:
        if ":" in model_spec:
            engine_type, model_name = model_spec.split(":", 1)
        else:
            # Default to pytorch engine
            engine_type = "pytorch"
            model_name = model_spec
        
        if engine_type not in SUPPORTED_ENGINES:
            print(ui.color_text(f"❌ Unsupported engine: {engine_type}", cfg.COLOR_RED))
            print(f"Supported engines: {', '.join(SUPPORTED_ENGINES)}")
            return
        
        model_configs.append((engine_type, model_name))
    
    # Create swap configuration
    swap_config = SwapConfig(
        strategy=SwapStrategy(args.swap_strategy),
        interval=args.swap_interval,
        min_confidence=args.min_confidence,
        swap_components=args.swap_components,
        verbose=args.verbose
    )
    
    # Print header
    print(ui.color_text("\n" + "="*60, cfg.COLOR_CYAN))
    print(ui.color_text("  🧠 MIND MELD - Neural State Swapping System 🧠", cfg.COLOR_CYAN))
    print(ui.color_text("="*60, cfg.COLOR_CYAN))
    
    # Initialize Mind Meld Engine
    meld_engine = MindMeldEngine(model_configs, swap_config)
    
    # Load models
    if not meld_engine.load_models():
        print(ui.color_text("\n❌ Failed to initialize Mind Meld", cfg.COLOR_RED))
        return
    
    try:
        # Generate melded text
        result = meld_engine.generate_melded_text(
            prompt=args.prompt,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            top_k=args.top_k,
            top_p=args.top_p
        )
        
        print(ui.color_text("\n\n✨ Mind Meld Complete!", cfg.COLOR_GREEN))
        
    except KeyboardInterrupt:
        print(ui.color_text("\n\n⚠️ Generation interrupted by user", cfg.COLOR_YELLOW))
    except Exception as e:
        print(ui.color_text(f"\n\n❌ Error: {e}", cfg.COLOR_RED))
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()