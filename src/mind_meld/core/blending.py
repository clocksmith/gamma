"""Weighted blending strategies for combining model outputs"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import sys


class BlendingStrategy(Enum):
    """Different strategies for blending model outputs"""
    WEIGHTED_AVERAGE = "weighted_average"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    DYNAMIC_WEIGHTED = "dynamic_weighted"
    ATTENTION_WEIGHTED = "attention_weighted"
    LEARNED = "learned"
    HIERARCHICAL = "hierarchical"
    ENSEMBLE_VOTING = "ensemble_voting"


@dataclass
class BlendingConfig:
    """Configuration for output blending"""
    strategy: BlendingStrategy = BlendingStrategy.WEIGHTED_AVERAGE
    weights: Optional[List[float]] = None
    temperature: float = 1.0
    
    # Confidence-based blending
    use_confidence_scores: bool = True
    confidence_threshold: float = 0.7
    confidence_power: float = 2.0  # Exponent for confidence weighting
    
    # Dynamic weighting
    dynamic_adjustment: bool = False
    adjustment_rate: float = 0.1
    performance_metric: str = "perplexity"  # perplexity, entropy, agreement
    
    # Ensemble settings
    voting_threshold: float = 0.5
    require_unanimous: bool = False
    
    # Smoothing and regularization
    smoothing_factor: float = 0.1
    entropy_regularization: float = 0.01
    
    # Output filtering
    top_k_blend: Optional[int] = 100
    top_p_blend: Optional[float] = 0.95


class LogitBlender:
    """Handles blending of logits from multiple models"""
    
    def __init__(self, config: BlendingConfig = None, verbose: bool = True):
        self.config = config or BlendingConfig()
        self.verbose = verbose
        
        # Dynamic weight tracking
        self.current_weights = None
        self.weight_history = []
        self.performance_history = []
        
        # Model performance tracking
        self.model_scores = {}
        self.blend_count = 0
        
    def blend(
        self,
        logits_list: List[Any],
        model_names: Optional[List[str]] = None,
        confidences: Optional[List[float]] = None,
        attention_scores: Optional[List[Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Blend logits from multiple models
        
        Args:
            logits_list: List of logits from each model
            model_names: Names of the models
            confidences: Confidence scores for each model's output
            attention_scores: Attention scores from each model
            metadata: Additional metadata for blending decisions
        
        Returns:
            Blended logits and blend statistics
        """
        if not logits_list:
            raise ValueError("No logits to blend")
        
        if len(logits_list) == 1:
            return logits_list[0], {"single_model": True}
        
        # Convert to numpy for processing
        logits_np_list = [self._to_numpy(logits) for logits in logits_list]
        
        # Ensure all logits have the same shape
        target_shape = self._get_target_shape(logits_np_list)
        logits_np_list = [self._reshape_logits(l, target_shape) for l in logits_np_list]
        
        # Get or initialize weights
        weights = self._get_weights(len(logits_list), confidences, attention_scores)
        
        # Apply blending strategy
        if self.config.strategy == BlendingStrategy.WEIGHTED_AVERAGE:
            blended = self._weighted_average_blend(logits_np_list, weights)
        elif self.config.strategy == BlendingStrategy.CONFIDENCE_WEIGHTED:
            blended = self._confidence_weighted_blend(logits_np_list, confidences)
        elif self.config.strategy == BlendingStrategy.DYNAMIC_WEIGHTED:
            blended = self._dynamic_weighted_blend(logits_np_list, metadata)
        elif self.config.strategy == BlendingStrategy.ATTENTION_WEIGHTED:
            blended = self._attention_weighted_blend(logits_np_list, attention_scores)
        elif self.config.strategy == BlendingStrategy.HIERARCHICAL:
            blended = self._hierarchical_blend(logits_np_list, weights)
        elif self.config.strategy == BlendingStrategy.ENSEMBLE_VOTING:
            blended = self._ensemble_voting_blend(logits_np_list)
        else:
            blended = self._weighted_average_blend(logits_np_list, weights)
        
        # Apply temperature
        if self.config.temperature != 1.0:
            blended = blended / self.config.temperature
        
        # Apply filtering
        blended = self._apply_filtering(blended)
        
        # Apply regularization
        if self.config.entropy_regularization > 0:
            blended = self._apply_entropy_regularization(blended)
        
        # Convert back to original tensor type
        blended_tensor = self._from_numpy(blended, logits_list[0])
        
        # Track statistics
        stats = self._compute_blend_statistics(
            logits_np_list, blended, weights, model_names
        )
        
        self.blend_count += 1
        
        return blended_tensor, stats
    
    def _weighted_average_blend(
        self,
        logits_list: List[np.ndarray],
        weights: np.ndarray
    ) -> np.ndarray:
        """Perform weighted average blending"""
        # Convert logits to probabilities
        probs_list = [self._softmax(logits) for logits in logits_list]
        
        # Weighted average of probabilities
        blended_probs = np.zeros_like(probs_list[0])
        for i, probs in enumerate(probs_list):
            blended_probs += weights[i] * probs
        
        # Convert back to logits
        blended_logits = np.log(blended_probs + 1e-10)
        
        return blended_logits
    
    def _confidence_weighted_blend(
        self,
        logits_list: List[np.ndarray],
        confidences: Optional[List[float]]
    ) -> np.ndarray:
        """Blend using confidence scores"""
        if confidences is None:
            # Estimate confidence from logit entropy
            confidences = [self._estimate_confidence(logits) for logits in logits_list]
        
        # Apply confidence power scaling
        conf_array = np.array(confidences)
        conf_array = np.power(conf_array, self.config.confidence_power)
        
        # Normalize to weights
        weights = conf_array / np.sum(conf_array)
        
        return self._weighted_average_blend(logits_list, weights)
    
    def _dynamic_weighted_blend(
        self,
        logits_list: List[np.ndarray],
        metadata: Optional[Dict[str, Any]]
    ) -> np.ndarray:
        """Dynamically adjust weights based on performance"""
        # Initialize weights if needed
        if self.current_weights is None:
            self.current_weights = np.ones(len(logits_list)) / len(logits_list)
        
        # Compute performance scores
        if self.config.performance_metric == "perplexity":
            scores = [self._compute_perplexity(logits) for logits in logits_list]
            # Lower perplexity is better, so invert
            scores = 1.0 / (np.array(scores) + 1e-6)
        elif self.config.performance_metric == "entropy":
            scores = [self._compute_entropy(logits) for logits in logits_list]
            # Lower entropy might indicate more confidence
            scores = 1.0 / (np.array(scores) + 1e-6)
        elif self.config.performance_metric == "agreement":
            scores = self._compute_agreement_scores(logits_list)
        else:
            scores = np.ones(len(logits_list))
        
        # Update weights with momentum
        target_weights = scores / np.sum(scores)
        self.current_weights = (
            (1 - self.config.adjustment_rate) * self.current_weights +
            self.config.adjustment_rate * target_weights
        )
        
        # Store history
        self.weight_history.append(self.current_weights.copy())
        self.performance_history.append(scores)
        
        return self._weighted_average_blend(logits_list, self.current_weights)
    
    def _attention_weighted_blend(
        self,
        logits_list: List[np.ndarray],
        attention_scores: Optional[List[Any]]
    ) -> np.ndarray:
        """Use attention scores to weight blending"""
        if attention_scores is None:
            # Fall back to weighted average
            weights = np.ones(len(logits_list)) / len(logits_list)
        else:
            # Extract attention-based importance scores
            importance_scores = []
            for attn in attention_scores:
                attn_np = self._to_numpy(attn)
                # Use mean attention over last layer as importance
                if len(attn_np.shape) > 2:
                    importance = np.mean(attn_np[-1, :, :])
                else:
                    importance = np.mean(attn_np)
                importance_scores.append(importance)
            
            weights = np.array(importance_scores)
            weights = weights / np.sum(weights)
        
        return self._weighted_average_blend(logits_list, weights)
    
    def _hierarchical_blend(
        self,
        logits_list: List[np.ndarray],
        weights: np.ndarray
    ) -> np.ndarray:
        """Hierarchical blending - blend in stages"""
        if len(logits_list) <= 2:
            return self._weighted_average_blend(logits_list, weights)
        
        # First stage: blend pairs
        stage1_blends = []
        stage1_weights = []
        
        for i in range(0, len(logits_list), 2):
            if i + 1 < len(logits_list):
                # Blend pair
                pair_weights = np.array([weights[i], weights[i+1]])
                pair_weights = pair_weights / np.sum(pair_weights)
                blended = self._weighted_average_blend(
                    [logits_list[i], logits_list[i+1]],
                    pair_weights
                )
                stage1_blends.append(blended)
                stage1_weights.append(weights[i] + weights[i+1])
            else:
                # Odd one out
                stage1_blends.append(logits_list[i])
                stage1_weights.append(weights[i])
        
        # Recursive blend
        stage1_weights = np.array(stage1_weights)
        stage1_weights = stage1_weights / np.sum(stage1_weights)
        
        return self._hierarchical_blend(stage1_blends, stage1_weights)
    
    def _ensemble_voting_blend(
        self,
        logits_list: List[np.ndarray]
    ) -> np.ndarray:
        """Ensemble voting - combine top predictions"""
        # Get top-k predictions from each model
        k = min(10, logits_list[0].shape[-1])
        
        vote_counts = np.zeros_like(logits_list[0])
        
        for logits in logits_list:
            top_k_indices = np.argpartition(logits, -k)[-k:]
            vote_counts[top_k_indices] += 1
        
        # Normalize votes
        vote_probs = vote_counts / len(logits_list)
        
        # Apply voting threshold
        if self.config.require_unanimous:
            # Only keep unanimous votes
            vote_probs[vote_probs < 1.0] = 0
        else:
            # Apply threshold
            vote_probs[vote_probs < self.config.voting_threshold] = 0
        
        # Combine with average logits
        avg_logits = np.mean(logits_list, axis=0)
        
        # Weight by votes
        weighted_logits = avg_logits * (vote_probs + self.config.smoothing_factor)
        
        return weighted_logits
    
    def _get_weights(
        self,
        num_models: int,
        confidences: Optional[List[float]],
        attention_scores: Optional[List[Any]]
    ) -> np.ndarray:
        """Get or compute blending weights"""
        if self.config.weights is not None:
            weights = np.array(self.config.weights[:num_models])
            if len(weights) < num_models:
                # Pad with equal weights
                remaining = num_models - len(weights)
                weights = np.concatenate([
                    weights,
                    np.ones(remaining) / remaining
                ])
        elif confidences is not None and self.config.use_confidence_scores:
            weights = np.array(confidences)
        else:
            weights = np.ones(num_models)
        
        # Normalize
        weights = weights / np.sum(weights)
        
        return weights
    
    def _get_target_shape(self, logits_list: List[np.ndarray]) -> Tuple[int, ...]:
        """Determine target shape for alignment"""
        # Use the maximum vocabulary size
        max_vocab = max(l.shape[-1] for l in logits_list)
        
        if len(logits_list[0].shape) > 1:
            return logits_list[0].shape[:-1] + (max_vocab,)
        else:
            return (max_vocab,)
    
    def _reshape_logits(
        self,
        logits: np.ndarray,
        target_shape: Tuple[int, ...]
    ) -> np.ndarray:
        """Reshape logits to target shape"""
        if logits.shape == target_shape:
            return logits
        
        # Pad or truncate vocabulary dimension
        target_vocab = target_shape[-1]
        current_vocab = logits.shape[-1]
        
        if current_vocab < target_vocab:
            # Pad with low values
            padding = np.full(
                logits.shape[:-1] + (target_vocab - current_vocab,),
                -1e9
            )
            logits = np.concatenate([logits, padding], axis=-1)
        elif current_vocab > target_vocab:
            # Truncate
            logits = logits[..., :target_vocab]
        
        return logits
    
    def _apply_filtering(self, logits: np.ndarray) -> np.ndarray:
        """Apply top-k and top-p filtering"""
        if self.config.top_k_blend is not None:
            logits = self._top_k_filtering(logits, self.config.top_k_blend)
        
        if self.config.top_p_blend is not None:
            logits = self._top_p_filtering(logits, self.config.top_p_blend)
        
        return logits
    
    def _apply_entropy_regularization(self, logits: np.ndarray) -> np.ndarray:
        """Apply entropy regularization to encourage diversity"""
        probs = self._softmax(logits)
        entropy = -np.sum(probs * np.log(probs + 1e-10))
        
        # Add entropy bonus to logits
        entropy_bonus = self.config.entropy_regularization * entropy
        logits = logits + entropy_bonus
        
        return logits
    
    def _estimate_confidence(self, logits: np.ndarray) -> float:
        """Estimate confidence from logit distribution"""
        probs = self._softmax(logits)
        
        # Use max probability as confidence
        max_prob = np.max(probs)
        
        # Also consider entropy (lower entropy = higher confidence)
        entropy = -np.sum(probs * np.log(probs + 1e-10))
        normalized_entropy = entropy / np.log(len(probs))
        
        # Combine max prob and inverse entropy
        confidence = max_prob * (1 - normalized_entropy * 0.5)
        
        return float(confidence)
    
    def _compute_perplexity(self, logits: np.ndarray) -> float:
        """Compute perplexity of logit distribution"""
        probs = self._softmax(logits)
        entropy = -np.sum(probs * np.log(probs + 1e-10))
        perplexity = np.exp(entropy)
        return float(perplexity)
    
    def _compute_entropy(self, logits: np.ndarray) -> float:
        """Compute entropy of logit distribution"""
        probs = self._softmax(logits)
        entropy = -np.sum(probs * np.log(probs + 1e-10))
        return float(entropy)
    
    def _compute_agreement_scores(
        self,
        logits_list: List[np.ndarray]
    ) -> np.ndarray:
        """Compute how much each model agrees with others"""
        num_models = len(logits_list)
        scores = np.zeros(num_models)
        
        for i in range(num_models):
            agreements = []
            for j in range(num_models):
                if i != j:
                    # Compute KL divergence as disagreement
                    p = self._softmax(logits_list[i])
                    q = self._softmax(logits_list[j])
                    kl_div = np.sum(p * np.log(p / (q + 1e-10) + 1e-10))
                    # Convert to agreement (inverse of divergence)
                    agreement = 1.0 / (1.0 + kl_div)
                    agreements.append(agreement)
            
            scores[i] = np.mean(agreements) if agreements else 1.0
        
        return scores
    
    def _compute_blend_statistics(
        self,
        logits_list: List[np.ndarray],
        blended: np.ndarray,
        weights: np.ndarray,
        model_names: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Compute statistics about the blend"""
        stats = {
            "blend_count": self.blend_count,
            "num_models": len(logits_list),
            "weights": weights.tolist(),
            "strategy": self.config.strategy.value
        }
        
        if model_names:
            stats["model_names"] = model_names
            stats["model_weights"] = {
                name: float(weight)
                for name, weight in zip(model_names, weights)
            }
        
        # Compute diversity metrics
        entropies = [self._compute_entropy(l) for l in logits_list]
        stats["input_entropies"] = entropies
        stats["blended_entropy"] = self._compute_entropy(blended)
        
        # Compute agreement
        top_tokens = []
        for logits in logits_list:
            top_token = np.argmax(logits)
            top_tokens.append(int(top_token))
        
        stats["top_token_agreement"] = len(set(top_tokens)) == 1
        stats["top_tokens"] = top_tokens
        
        # Track performance if using dynamic weighting
        if self.config.strategy == BlendingStrategy.DYNAMIC_WEIGHTED:
            stats["weight_history_length"] = len(self.weight_history)
            if self.weight_history:
                stats["weight_trend"] = {
                    f"model_{i}": [
                        float(w[i]) for w in self.weight_history[-10:]
                    ]
                    for i in range(len(weights))
                }
        
        return stats
    
    def reset_dynamic_weights(self):
        """Reset dynamic weight tracking"""
        self.current_weights = None
        self.weight_history = []
        self.performance_history = []
    
    def get_weight_summary(self) -> Dict[str, Any]:
        """Get summary of weight evolution"""
        if not self.weight_history:
            return {"message": "No weight history available"}
        
        history_array = np.array(self.weight_history)
        
        return {
            "num_blends": len(self.weight_history),
            "current_weights": self.current_weights.tolist() if self.current_weights is not None else None,
            "mean_weights": np.mean(history_array, axis=0).tolist(),
            "std_weights": np.std(history_array, axis=0).tolist(),
            "final_weights": history_array[-1].tolist() if len(history_array) > 0 else None
        }
    
    # Utility methods
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Compute softmax"""
        exp_x = np.exp(x - np.max(x))
        return exp_x / np.sum(exp_x)
    
    def _top_k_filtering(self, logits: np.ndarray, k: int) -> np.ndarray:
        """Apply top-k filtering"""
        if k <= 0:
            return logits
        
        top_k_indices = np.argpartition(logits, -k)[-k:]
        filtered = np.full_like(logits, -1e9)
        filtered[top_k_indices] = logits[top_k_indices]
        
        return filtered
    
    def _top_p_filtering(self, logits: np.ndarray, p: float) -> np.ndarray:
        """Apply nucleus (top-p) filtering"""
        if p <= 0 or p >= 1:
            return logits
        
        sorted_indices = np.argsort(logits)[::-1]
        sorted_logits = logits[sorted_indices]
        
        probs = self._softmax(sorted_logits)
        cumsum = np.cumsum(probs)
        
        cutoff_idx = np.searchsorted(cumsum, p)
        if cutoff_idx < len(cumsum):
            cutoff_idx += 1
        
        filtered = np.full_like(logits, -1e9)
        kept_indices = sorted_indices[:cutoff_idx]
        filtered[kept_indices] = logits[kept_indices]
        
        return filtered
    
    def _to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert various tensor types to numpy"""
        if isinstance(tensor, np.ndarray):
            return tensor
        
        if "torch" in sys.modules:
            import torch
            if isinstance(tensor, torch.Tensor):
                return tensor.detach().cpu().numpy()
        
        if "mlx" in sys.modules:
            import mlx.core as mx
            if hasattr(tensor, "dtype"):
                return np.array(tensor)
        
        if "tensorflow" in sys.modules:
            import tensorflow as tf
            if isinstance(tensor, tf.Tensor):
                return tensor.numpy()
        
        return np.array(tensor)
    
    def _from_numpy(self, array: np.ndarray, reference: Any) -> Any:
        """Convert numpy array back to original tensor type"""
        if "torch" in sys.modules:
            import torch
            if isinstance(reference, torch.Tensor):
                return torch.from_numpy(array.astype(np.float32)).to(
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