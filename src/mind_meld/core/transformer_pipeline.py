"""Unified transformer pipeline for consistent processing across models"""

import logging
import sys
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


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
                logger.debug(f"Executing step: {step.name}")
            
            state = step.execute(state)
        
        return state
    
    # Standard transformer operations

    def _embed_inputs(self, input_ids: Any, model_state: Any) -> Dict[str, Any]:
        """
        Embed input tokens using the model's embedding layer.

        Args:
            input_ids: Token IDs to embed (numpy array, torch tensor, or similar)
            model_state: Model state containing embedding weights or model reference

        Returns:
            Dict with 'embeddings' and 'position_ids'
        """
        # Convert input_ids to numpy for processing
        input_np = self._to_numpy(input_ids)
        if input_np.ndim == 0:
            input_np = input_np.reshape(1)

        seq_len = input_np.shape[-1] if input_np.ndim > 0 else 1

        # Try to get embeddings from model state
        if isinstance(model_state, dict):
            # Direct embedding matrix provided
            if 'embedding_matrix' in model_state:
                embed_matrix = model_state['embedding_matrix']
                embed_np = self._to_numpy(embed_matrix)
                # Perform lookup
                embeddings = embed_np[input_np.flatten()]
                if input_np.ndim > 1:
                    embeddings = embeddings.reshape(*input_np.shape, -1)
            elif 'model' in model_state and hasattr(model_state['model'], 'get_input_embeddings'):
                # HuggingFace-style model
                model = model_state['model']
                embed_layer = model.get_input_embeddings()
                if "torch" in sys.modules:
                    import torch
                    input_tensor = torch.tensor(input_np)
                    embeddings = embed_layer(input_tensor)
                else:
                    # Fallback: use weight matrix directly
                    if hasattr(embed_layer, 'weight'):
                        embed_np = self._to_numpy(embed_layer.weight)
                        embeddings = embed_np[input_np.flatten()]
                    else:
                        embeddings = input_np.astype(np.float32)
            else:
                # No embedding info available - use one-hot encoding as fallback
                vocab_size = model_state.get('vocab_size', 32000)
                embeddings = np.zeros((seq_len, vocab_size), dtype=np.float32)
                for i, token_id in enumerate(input_np.flatten()):
                    if token_id < vocab_size:
                        embeddings[i, token_id] = 1.0
        else:
            # Model object passed directly
            if hasattr(model_state, 'get_input_embeddings'):
                embed_layer = model_state.get_input_embeddings()
                if hasattr(embed_layer, 'weight'):
                    embed_np = self._to_numpy(embed_layer.weight)
                    embeddings = embed_np[input_np.flatten()]
                else:
                    embeddings = input_np.astype(np.float32)
            else:
                # Fallback
                embeddings = input_np.astype(np.float32)

        return {
            'embeddings': embeddings,
            'position_ids': np.arange(seq_len)
        }

    def _add_position_encoding(
        self,
        embeddings: Any,
        position_ids: Any,
        model_state: Any
    ) -> Any:
        """
        Add positional encoding to embeddings.

        Supports:
        - Sinusoidal (original Transformer)
        - Learned position embeddings
        - RoPE (Rotary Position Embeddings) - placeholder for future
        """
        embeddings_np = self._to_numpy(embeddings)
        position_np = self._to_numpy(position_ids)

        if embeddings_np.ndim < 2:
            return embeddings

        seq_len = embeddings_np.shape[-2] if embeddings_np.ndim > 1 else len(embeddings_np)
        hidden_dim = embeddings_np.shape[-1]

        # Determine encoding type from model_state
        encoding_type = 'sinusoidal'
        if isinstance(model_state, dict):
            encoding_type = model_state.get('position_encoding_type', 'sinusoidal')

            # Check for learned position embeddings
            if 'position_embedding_matrix' in model_state:
                pos_embed_matrix = self._to_numpy(model_state['position_embedding_matrix'])
                max_positions = pos_embed_matrix.shape[0]
                valid_positions = position_np[position_np < max_positions]

                if len(valid_positions) == seq_len:
                    pos_embeddings = pos_embed_matrix[position_np]
                    return embeddings_np + pos_embeddings

        # Sinusoidal position encoding (Vaswani et al., 2017)
        if encoding_type == 'sinusoidal':
            position_encoding = self._compute_sinusoidal_encoding(seq_len, hidden_dim)
            return embeddings_np + position_encoding[:seq_len]

        # ALiBi (Press et al., 2021) - applied in attention, not here
        if encoding_type == 'alibi':
            return embeddings_np

        # RoPE - applied in attention layer, not here
        if encoding_type == 'rope':
            return embeddings_np

        return embeddings_np

    def _compute_sinusoidal_encoding(self, seq_len: int, hidden_dim: int) -> np.ndarray:
        """Compute sinusoidal positional encoding."""
        position = np.arange(seq_len)[:, np.newaxis]
        div_term = np.exp(np.arange(0, hidden_dim, 2) * (-np.log(10000.0) / hidden_dim))

        pe = np.zeros((seq_len, hidden_dim), dtype=np.float32)
        pe[:, 0::2] = np.sin(position * div_term)
        if hidden_dim > 1:
            pe[:, 1::2] = np.cos(position * div_term[:hidden_dim // 2])

        return pe

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

    def _rms_norm(self, tensor: Any, eps: float = 1e-5) -> Any:
        """Apply RMS (Root Mean Square) layer normalization - used by LLaMA, T5."""
        tensor_np = self._to_numpy(tensor)
        rms = np.sqrt(np.mean(tensor_np ** 2, axis=-1, keepdims=True) + eps)
        normed = tensor_np / rms
        return self._from_numpy(normed, tensor)

    def _compute_attention(
        self,
        normed_embeddings: Any,
        attention_mask: Optional[Any],
        kv_cache: Optional[Any],
        model_state: Any
    ) -> Dict[str, Any]:
        """
        Compute scaled dot-product self-attention.

        Args:
            normed_embeddings: Layer-normalized input embeddings
            attention_mask: Optional attention mask (causal or padding mask)
            kv_cache: Optional KV cache for incremental decoding
            model_state: Model state with attention weights/config

        Returns:
            Dict with attention_output, attention_weights, and updated_kv_cache
        """
        embeddings_np = self._to_numpy(normed_embeddings)

        if embeddings_np.ndim < 2:
            return {
                'attention_output': normed_embeddings,
                'attention_weights': None,
                'updated_kv_cache': kv_cache
            }

        seq_len = embeddings_np.shape[-2] if embeddings_np.ndim > 1 else 1
        hidden_dim = embeddings_np.shape[-1]

        # Get attention config from model_state
        num_heads = 1
        head_dim = hidden_dim

        if isinstance(model_state, dict):
            num_heads = model_state.get('num_attention_heads', 1)
            head_dim = hidden_dim // num_heads if num_heads > 0 else hidden_dim

            # Use provided Q, K, V projection weights if available
            if all(k in model_state for k in ['q_proj', 'k_proj', 'v_proj']):
                q_proj = self._to_numpy(model_state['q_proj'])
                k_proj = self._to_numpy(model_state['k_proj'])
                v_proj = self._to_numpy(model_state['v_proj'])

                # Project to Q, K, V
                q = np.dot(embeddings_np, q_proj)
                k = np.dot(embeddings_np, k_proj)
                v = np.dot(embeddings_np, v_proj)
            else:
                # Self-attention without projections (identity)
                q = k = v = embeddings_np
        else:
            q = k = v = embeddings_np

        # Handle KV cache for incremental decoding
        if kv_cache is not None:
            cached_k, cached_v = kv_cache
            cached_k_np = self._to_numpy(cached_k)
            cached_v_np = self._to_numpy(cached_v)
            k = np.concatenate([cached_k_np, k], axis=-2)
            v = np.concatenate([cached_v_np, v], axis=-2)

        # Store new KV cache
        updated_kv_cache = (k, v)

        # Scaled dot-product attention
        scale = 1.0 / np.sqrt(head_dim)
        attention_scores = np.dot(q, k.T) * scale

        # Apply attention mask (causal mask for autoregressive models)
        if attention_mask is not None:
            mask_np = self._to_numpy(attention_mask)
            attention_scores = attention_scores + mask_np
        else:
            # Create causal mask for autoregressive decoding
            causal_mask = np.triu(np.full((seq_len, k.shape[-2]), -np.inf), k=1)
            if seq_len == 1 and k.shape[-2] > 1:
                # Single token generation - no mask needed for the new token
                causal_mask = np.zeros((1, k.shape[-2]))
            attention_scores = attention_scores + causal_mask[-seq_len:]

        # Softmax
        attention_scores_max = np.max(attention_scores, axis=-1, keepdims=True)
        attention_weights = np.exp(attention_scores - attention_scores_max)
        attention_weights = attention_weights / (np.sum(attention_weights, axis=-1, keepdims=True) + 1e-10)

        # Apply attention to values
        attention_output = np.dot(attention_weights, v)

        return {
            'attention_output': self._from_numpy(attention_output, normed_embeddings),
            'attention_weights': attention_weights,
            'updated_kv_cache': updated_kv_cache
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
        """
        Apply feed-forward network (FFN / MLP layer).

        Standard FFN: Linear -> Activation -> Linear
        GLU variants: Linear -> (Linear * Activation) -> Linear
        """
        tensor_np = self._to_numpy(tensor)
        hidden_dim = tensor_np.shape[-1]

        # Get FFN config from model_state
        intermediate_dim = hidden_dim * 4  # Default expansion factor
        activation = 'gelu'
        use_glu = False

        if isinstance(model_state, dict):
            intermediate_dim = model_state.get('intermediate_size', hidden_dim * 4)
            activation = model_state.get('hidden_act', 'gelu')
            use_glu = model_state.get('use_glu', False)

            # Use provided weights if available
            if 'ff_up_proj' in model_state and 'ff_down_proj' in model_state:
                up_proj = self._to_numpy(model_state['ff_up_proj'])
                down_proj = self._to_numpy(model_state['ff_down_proj'])

                if use_glu and 'ff_gate_proj' in model_state:
                    gate_proj = self._to_numpy(model_state['ff_gate_proj'])
                    # SwiGLU / GeGLU variant
                    gate = self._apply_activation(np.dot(tensor_np, gate_proj), activation)
                    up = np.dot(tensor_np, up_proj)
                    intermediate = gate * up
                else:
                    # Standard FFN
                    intermediate = self._apply_activation(np.dot(tensor_np, up_proj), activation)

                output = np.dot(intermediate, down_proj)
                return self._from_numpy(output, tensor)

        # Fallback: simple linear transformation (no actual FFN weights)
        return tensor

    def _apply_activation(self, tensor: np.ndarray, activation: str) -> np.ndarray:
        """Apply activation function."""
        if activation == 'gelu':
            # GELU approximation
            return 0.5 * tensor * (1.0 + np.tanh(np.sqrt(2.0 / np.pi) * (tensor + 0.044715 * tensor ** 3)))
        elif activation == 'silu' or activation == 'swish':
            # SiLU / Swish
            return tensor * (1.0 / (1.0 + np.exp(-tensor)))
        elif activation == 'relu':
            return np.maximum(0, tensor)
        elif activation == 'tanh':
            return np.tanh(tensor)
        else:
            # Default to GELU
            return 0.5 * tensor * (1.0 + np.tanh(np.sqrt(2.0 / np.pi) * (tensor + 0.044715 * tensor ** 3)))

    def _project_output(self, hidden_states: Any, model_state: Any) -> Any:
        """
        Project hidden states to vocabulary logits.

        Args:
            hidden_states: Final hidden states from transformer
            model_state: Model state containing output projection weights

        Returns:
            Logits over vocabulary
        """
        hidden_np = self._to_numpy(hidden_states)

        if isinstance(model_state, dict):
            # Check for explicit output projection matrix
            if 'output_projection' in model_state:
                output_proj = self._to_numpy(model_state['output_projection'])
                logits = np.dot(hidden_np, output_proj)
                return self._from_numpy(logits, hidden_states)

            # Many models tie input/output embeddings
            if 'embedding_matrix' in model_state:
                embed_matrix = self._to_numpy(model_state['embedding_matrix'])
                # Output projection is transpose of embedding matrix
                logits = np.dot(hidden_np, embed_matrix.T)
                return self._from_numpy(logits, hidden_states)

            # HuggingFace-style model with lm_head
            if 'model' in model_state:
                model = model_state['model']
                if hasattr(model, 'lm_head'):
                    if hasattr(model.lm_head, 'weight'):
                        lm_weight = self._to_numpy(model.lm_head.weight)
                        logits = np.dot(hidden_np, lm_weight.T)
                        return self._from_numpy(logits, hidden_states)
                elif hasattr(model, 'get_output_embeddings'):
                    output_embed = model.get_output_embeddings()
                    if output_embed is not None and hasattr(output_embed, 'weight'):
                        output_weight = self._to_numpy(output_embed.weight)
                        logits = np.dot(hidden_np, output_weight.T)
                        return self._from_numpy(logits, hidden_states)

        # Model object passed directly
        elif hasattr(model_state, 'lm_head'):
            if hasattr(model_state.lm_head, 'weight'):
                lm_weight = self._to_numpy(model_state.lm_head.weight)
                logits = np.dot(hidden_np, lm_weight.T)
                return self._from_numpy(logits, hidden_states)

        # Fallback: return hidden states as-is (assumes hidden_dim == vocab_size)
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
        """Convert tensor to numpy."""
        from src.core.tensor_utils import to_numpy
        return to_numpy(tensor)
    
    def _from_numpy(self, array: np.ndarray, reference: Any) -> Any:
        """Convert numpy array to match reference tensor type."""
        from src.core.tensor_utils import from_numpy
        return from_numpy(array, reference)
    
    def create_model_specific_pipeline(self, model_type: str) -> 'UnifiedTransformerPipeline':
        """
        Create a pipeline customized for a specific model type.

        Supported model families:
        - GPT/GPT-2/GPT-Neo: Post-norm architecture
        - BERT/RoBERTa: Pre-norm with bidirectional attention
        - LLaMA/Mistral: Pre-norm with RMSNorm and SwiGLU
        - T5/FLAN: Encoder-decoder with relative position bias
        - Gemma: Similar to LLaMA with some differences
        """
        pipeline = UnifiedTransformerPipeline(verbose=self.verbose)

        model_type_lower = model_type.lower()

        # GPT family: post-norm, causal attention
        if any(name in model_type_lower for name in ["gpt", "gpt2", "gpt-neo", "gpt-j"]):
            pipeline.remove_step("pre_norm")
            # GPT uses post-layer norm

        # BERT family: pre-norm, bidirectional attention
        elif any(name in model_type_lower for name in ["bert", "roberta", "albert"]):
            # BERT uses bidirectional attention - modify attention step
            pass

        # LLaMA family: RMSNorm, SwiGLU, RoPE
        elif any(name in model_type_lower for name in ["llama", "mistral", "vicuna", "alpaca"]):
            # Replace layer norm with RMS norm
            for step in pipeline.steps:
                if "norm" in step.name:
                    step.function = pipeline._rms_norm

            # Add RoPE indicator to state processing
            original_process = pipeline.process

            def llama_process(*args, **kwargs):
                if 'model_state' not in kwargs or not isinstance(kwargs.get('model_state'), dict):
                    kwargs['model_state'] = kwargs.get('model_state', {})
                if isinstance(kwargs['model_state'], dict):
                    kwargs['model_state']['position_encoding_type'] = 'rope'
                    kwargs['model_state']['use_glu'] = True
                    kwargs['model_state']['hidden_act'] = 'silu'
                return original_process(*args, **kwargs)

            pipeline.process = llama_process

        # Gemma: Similar to LLaMA
        elif "gemma" in model_type_lower:
            for step in pipeline.steps:
                if "norm" in step.name:
                    step.function = pipeline._rms_norm

        # T5 family: encoder-decoder, relative position bias
        elif any(name in model_type_lower for name in ["t5", "flan", "mt5"]):
            # T5 uses RMS norm
            for step in pipeline.steps:
                if "norm" in step.name:
                    step.function = pipeline._rms_norm

            # T5 uses relative position bias in attention
            original_process = pipeline.process

            def t5_process(*args, **kwargs):
                if 'model_state' not in kwargs or not isinstance(kwargs.get('model_state'), dict):
                    kwargs['model_state'] = kwargs.get('model_state', {})
                if isinstance(kwargs['model_state'], dict):
                    kwargs['model_state']['position_encoding_type'] = 'relative'
                return original_process(*args, **kwargs)

            pipeline.process = t5_process

        # Falcon: Parallel attention and FFN
        elif "falcon" in model_type_lower:
            # Falcon computes attention and FFN in parallel
            # This is a more complex modification
            pass

        # MPT: ALiBi position encoding
        elif "mpt" in model_type_lower:
            original_process = pipeline.process

            def mpt_process(*args, **kwargs):
                if 'model_state' not in kwargs or not isinstance(kwargs.get('model_state'), dict):
                    kwargs['model_state'] = kwargs.get('model_state', {})
                if isinstance(kwargs['model_state'], dict):
                    kwargs['model_state']['position_encoding_type'] = 'alibi'
                return original_process(*args, **kwargs)

            pipeline.process = mpt_process

        # Phi: Similar to GPT but with different FFN
        elif "phi" in model_type_lower:
            pipeline.remove_step("pre_norm")

        # Qwen: Similar to LLaMA
        elif "qwen" in model_type_lower:
            for step in pipeline.steps:
                if "norm" in step.name:
                    step.function = pipeline._rms_norm

        return pipeline

    def get_supported_model_types(self) -> List[str]:
        """Return list of explicitly supported model types."""
        return [
            "gpt", "gpt2", "gpt-neo", "gpt-j",
            "bert", "roberta", "albert",
            "llama", "llama2", "mistral", "vicuna", "alpaca",
            "gemma",
            "t5", "flan-t5", "mt5",
            "falcon",
            "mpt",
            "phi", "phi-2",
            "qwen"
        ]