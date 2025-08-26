"""Unified transformer pipeline for consistent processing across models"""

import sys
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class TransformerStep:
    """Represents a single step in the transformer pipeline"""
    name: str
    function: callable
    input_keys: List[str]
    output_keys: List[str]
    optional: bool = False
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute this transformer step"""
        try:
            # Gather inputs
            inputs = {}
            for key in self.input_keys:
                if key in state:
                    inputs[key] = state[key]
                elif not self.optional:
                    raise KeyError(f"Required input '{key}' not found for step '{self.name}'")
            
            # Execute function
            outputs = self.function(**inputs)
            
            # Update state with outputs
            if isinstance(outputs, dict):
                for key in self.output_keys:
                    if key in outputs:
                        state[key] = outputs[key]
            else:
                # Single output
                if len(self.output_keys) == 1:
                    state[self.output_keys[0]] = outputs
            
            return state
            
        except Exception as e:
            if not self.optional:
                raise RuntimeError(f"Error in transformer step '{self.name}': {e}")
            return state


class UnifiedTransformerPipeline:
    """Ensures identical transformer steps across different models"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.steps: List[TransformerStep] = []
        self.step_index: Dict[str, int] = {}
        
        # Initialize standard transformer pipeline
        self._initialize_standard_pipeline()
    
    def _initialize_standard_pipeline(self):
        """Initialize the standard transformer pipeline steps"""
        
        # Step 1: Input embedding
        self.add_step(TransformerStep(
            name="input_embedding",
            function=self._embed_inputs,
            input_keys=["input_ids", "model_state"],
            output_keys=["embeddings", "position_ids"]
        ))
        
        # Step 2: Position encoding
        self.add_step(TransformerStep(
            name="position_encoding",
            function=self._add_position_encoding,
            input_keys=["embeddings", "position_ids", "model_state"],
            output_keys=["encoded_embeddings"]
        ))
        
        # Step 3: Layer normalization (pre)
        self.add_step(TransformerStep(
            name="pre_norm",
            function=self._layer_norm,
            input_keys=["encoded_embeddings"],
            output_keys=["normed_embeddings"],
            optional=True
        ))
        
        # Step 4: Self-attention
        self.add_step(TransformerStep(
            name="self_attention",
            function=self._compute_attention,
            input_keys=["normed_embeddings", "attention_mask", "kv_cache", "model_state"],
            output_keys=["attention_output", "attention_weights", "updated_kv_cache"]
        ))
        
        # Step 5: Residual connection
        self.add_step(TransformerStep(
            name="attention_residual",
            function=self._add_residual,
            input_keys=["encoded_embeddings", "attention_output"],
            output_keys=["attention_residual_output"]
        ))
        
        # Step 6: Layer normalization (mid)
        self.add_step(TransformerStep(
            name="mid_norm",
            function=self._layer_norm,
            input_keys=["attention_residual_output"],
            output_keys=["mid_normed"],
            optional=True
        ))
        
        # Step 7: Feed-forward network
        self.add_step(TransformerStep(
            name="feed_forward",
            function=self._feed_forward,
            input_keys=["mid_normed", "model_state"],
            output_keys=["ff_output"]
        ))
        
        # Step 8: Final residual
        self.add_step(TransformerStep(
            name="final_residual",
            function=self._add_residual,
            input_keys=["attention_residual_output", "ff_output"],
            output_keys=["hidden_states"]
        ))
        
        # Step 9: Final layer norm
        self.add_step(TransformerStep(
            name="final_norm",
            function=self._layer_norm,
            input_keys=["hidden_states"],
            output_keys=["final_hidden_states"]
        ))
        
        # Step 10: Output projection
        self.add_step(TransformerStep(
            name="output_projection",
            function=self._project_output,
            input_keys=["final_hidden_states", "model_state"],
            output_keys=["logits"]
        ))
        
        # Step 11: Logit processing
        self.add_step(TransformerStep(
            name="logit_processing",
            function=self._process_logits,
            input_keys=["logits", "temperature", "top_k", "top_p", "vocabulary_mask"],
            output_keys=["processed_logits", "probabilities"]
        ))
    
    def add_step(self, step: TransformerStep):
        """Add a step to the pipeline"""
        self.steps.append(step)
        self.step_index[step.name] = len(self.steps) - 1
    
    def insert_step(self, step: TransformerStep, after: str):
        """Insert a step after a named step"""
        if after not in self.step_index:
            raise ValueError(f"Step '{after}' not found in pipeline")
        
        insert_idx = self.step_index[after] + 1
        self.steps.insert(insert_idx, step)
        
        # Update indices
        for i in range(insert_idx, len(self.steps)):
            self.step_index[self.steps[i].name] = i
    
    def remove_step(self, name: str):
        """Remove a step from the pipeline"""
        if name not in self.step_index:
            return
        
        idx = self.step_index[name]
        del self.steps[idx]
        del self.step_index[name]
        
        # Update indices
        for i in range(idx, len(self.steps)):
            self.step_index[self.steps[i].name] = i
    
    def process(
        self,
        input_ids: Any,
        model_state: Any,
        attention_mask: Optional[Any] = None,
        kv_cache: Optional[Any] = None,
        temperature: float = 1.0,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
        vocabulary_mask: Optional[Any] = None,
        custom_steps: Optional[Dict[str, callable]] = None
    ) -> Dict[str, Any]:
        """
        Process inputs through the unified pipeline
        
        Returns:
            Dictionary containing all intermediate and final outputs
        """
        
        # Initialize state
        state = {
            'input_ids': input_ids,
            'model_state': model_state,
            'attention_mask': attention_mask,
            'kv_cache': kv_cache,
            'temperature': temperature,
            'top_k': top_k,
            'top_p': top_p,
            'vocabulary_mask': vocabulary_mask
        }
        
        # Override step functions if custom implementations provided
        if custom_steps:
            for step in self.steps:
                if step.name in custom_steps:
                    step.function = custom_steps[step.name]
        
        # Execute pipeline
        for step in self.steps:
            if self.verbose:
                print(f"  Executing step: {step.name}")
            
            state = step.execute(state)
        
        return state
    
    # Standard transformer operations
    
    def _embed_inputs(self, input_ids: Any, model_state: Any) -> Dict[str, Any]:
        """Embed input tokens"""
        # This would be overridden by model-specific implementation
        return {
            'embeddings': input_ids,  # Placeholder
            'position_ids': np.arange(len(input_ids))
        }
    
    def _add_position_encoding(
        self,
        embeddings: Any,
        position_ids: Any,
        model_state: Any
    ) -> Any:
        """Add positional encoding to embeddings"""
        # Placeholder - would be overridden
        return embeddings
    
    def _layer_norm(self, tensor: Any, eps: float = 1e-5) -> Any:
        """Apply layer normalization"""
        if isinstance(tensor, np.ndarray):
            mean = np.mean(tensor, axis=-1, keepdims=True)
            std = np.std(tensor, axis=-1, keepdims=True)
            return (tensor - mean) / (std + eps)
        
        # Handle other tensor types
        if "torch" in sys.modules:
            import torch
            if isinstance(tensor, torch.Tensor):
                return torch.nn.functional.layer_norm(tensor, tensor.shape[-1:])
        
        return tensor
    
    def _compute_attention(
        self,
        normed_embeddings: Any,
        attention_mask: Optional[Any],
        kv_cache: Optional[Any],
        model_state: Any
    ) -> Dict[str, Any]:
        """Compute self-attention"""
        # Placeholder - would be overridden by model-specific implementation
        return {
            'attention_output': normed_embeddings,
            'attention_weights': None,
            'updated_kv_cache': kv_cache
        }
    
    def _add_residual(self, input_tensor: Any, output_tensor: Any) -> Any:
        """Add residual connection"""
        if isinstance(input_tensor, np.ndarray) and isinstance(output_tensor, np.ndarray):
            return input_tensor + output_tensor
        
        # Handle other tensor types
        if "torch" in sys.modules:
            import torch
            if isinstance(input_tensor, torch.Tensor):
                return input_tensor + output_tensor
        
        if "mlx" in sys.modules:
            import mlx.core as mx
            if hasattr(input_tensor, "dtype"):
                return input_tensor + output_tensor
        
        return output_tensor
    
    def _feed_forward(self, tensor: Any, model_state: Any) -> Any:
        """Apply feed-forward network"""
        # Placeholder - would be overridden
        return tensor
    
    def _project_output(self, hidden_states: Any, model_state: Any) -> Any:
        """Project hidden states to vocabulary"""
        # Placeholder - would be overridden
        return hidden_states
    
    def _process_logits(
        self,
        logits: Any,
        temperature: float,
        top_k: Optional[int],
        top_p: Optional[float],
        vocabulary_mask: Optional[Any]
    ) -> Dict[str, Any]:
        """Process logits with temperature and filtering"""
        
        # Convert to numpy for processing
        if isinstance(logits, np.ndarray):
            logits_np = logits
        else:
            logits_np = self._to_numpy(logits)
        
        # Apply vocabulary mask if provided
        if vocabulary_mask is not None:
            mask_np = self._to_numpy(vocabulary_mask)
            logits_np = logits_np + mask_np
        
        # Apply temperature
        if temperature != 1.0 and temperature > 0:
            logits_np = logits_np / temperature
        
        # Compute probabilities
        exp_logits = np.exp(logits_np - np.max(logits_np))
        probs = exp_logits / np.sum(exp_logits)
        
        # Apply top-k filtering
        if top_k is not None and top_k > 0:
            top_k_indices = np.argpartition(probs, -top_k)[-top_k:]
            filtered_probs = np.zeros_like(probs)
            filtered_probs[top_k_indices] = probs[top_k_indices]
            probs = filtered_probs / np.sum(filtered_probs)
        
        # Apply top-p filtering
        if top_p is not None and 0 < top_p < 1:
            sorted_indices = np.argsort(probs)[::-1]
            sorted_probs = probs[sorted_indices]
            cumsum = np.cumsum(sorted_probs)
            cutoff_idx = np.searchsorted(cumsum, top_p) + 1
            
            filtered_probs = np.zeros_like(probs)
            kept_indices = sorted_indices[:cutoff_idx]
            filtered_probs[kept_indices] = probs[kept_indices]
            probs = filtered_probs / np.sum(filtered_probs)
        
        # Convert back to original type
        processed_logits = self._from_numpy(np.log(probs + 1e-10), logits)
        probabilities = self._from_numpy(probs, logits)
        
        return {
            'processed_logits': processed_logits,
            'probabilities': probabilities
        }
    
    def _to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert tensor to numpy"""
        if isinstance(tensor, np.ndarray):
            return tensor
        
        if "torch" in sys.modules:
            import torch
            if isinstance(tensor, torch.Tensor):
                return tensor.detach().cpu().numpy()
        
        if "mlx" in sys.modules:
            if hasattr(tensor, "dtype"):
                return np.array(tensor)
        
        if "tensorflow" in sys.modules:
            import tensorflow as tf
            if isinstance(tensor, tf.Tensor):
                return tensor.numpy()
        
        return np.array(tensor)
    
    def _from_numpy(self, array: np.ndarray, reference: Any) -> Any:
        """Convert numpy array to match reference tensor type"""
        
        if isinstance(reference, np.ndarray):
            return array
        
        if "torch" in sys.modules:
            import torch
            if isinstance(reference, torch.Tensor):
                return torch.from_numpy(array).to(
                    device=reference.device,
                    dtype=reference.dtype
                )
        
        if "mlx" in sys.modules:
            import mlx.core as mx
            if hasattr(reference, "dtype"):
                return mx.array(array)
        
        if "tensorflow" in sys.modules:
            import tensorflow as tf
            if isinstance(reference, tf.Tensor):
                return tf.constant(array, dtype=reference.dtype)
        
        return array
    
    def create_model_specific_pipeline(self, model_type: str) -> 'UnifiedTransformerPipeline':
        """Create a pipeline customized for a specific model type"""
        pipeline = UnifiedTransformerPipeline(verbose=self.verbose)
        
        # Customize based on model type
        if "gpt" in model_type.lower():
            # GPT-style: no pre-norm, uses post-norm
            pipeline.remove_step("pre_norm")
        elif "bert" in model_type.lower():
            # BERT-style: uses pre-norm
            pass
        elif "t5" in model_type.lower():
            # T5-style: uses RMS norm instead of layer norm
            pass
        
        return pipeline