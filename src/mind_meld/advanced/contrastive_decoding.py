"""
Contrastive Decoding for Mind Meld.

Amplifies the unique capabilities of expert models by contrasting
them against amateur models. Subtracts amateur logits from expert logits
to highlight sophisticated vocabulary and reduce generic output.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

from src.core.engine_interface import LLMEngine
from src.engines import sampling_utils
from src.mind_meld.utils import VerboseLoggerMixin


@dataclass
class ContrastiveConfig:
    """Configuration for contrastive decoding."""
    alpha: float = 0.5  # Weight for amateur subtraction (0-1)
    beta: float = 0.1  # Minimum probability threshold
    temperature: float = 1.0  # Temperature for sampling
    use_adaptive_alpha: bool = True  # Adapt alpha based on perplexity difference


class ContrastiveDecoder(VerboseLoggerMixin):
    """
    Contrastive Decoding implementation.

    Logit formula: final_logits = expert_logits - alpha * amateur_logits

    This amplifies tokens that the expert model prefers but the amateur
    doesn't, leading to more sophisticated, specific output.
    """

    def __init__(
        self,
        expert_model: LLMEngine,
        amateur_model: LLMEngine,
        config: Optional[ContrastiveConfig] = None,
        verbose: bool = False
    ):
        """
        Initialize contrastive decoder.

        Args:
            expert_model: Large, capable model (target quality)
            amateur_model: Smaller model (3-5x smaller than expert)
            config: Configuration for contrastive decoding
            verbose: Enable verbose logging
        """
        self.expert_model = expert_model
        self.amateur_model = amateur_model
        self.config = config or ContrastiveConfig()
        self.verbose = verbose

        # Statistics
        self.total_tokens = 0
        self.avg_expert_confidence = 0.0
        self.avg_amateur_confidence = 0.0
        self.avg_alpha_used = 0.0

    def calculate_adaptive_alpha(
        self,
        expert_logits: np.ndarray,
        amateur_logits: np.ndarray
    ) -> float:
        """
        Adaptively calculate alpha based on model agreement.

        When models disagree more (higher divergence), use higher alpha
        to emphasize expert's unique preferences.

        Args:
            expert_logits: Logits from expert model
            amateur_logits: Logits from amateur model

        Returns:
            Adapted alpha value
        """
        # Convert to probabilities
        expert_probs = self._softmax(expert_logits)
        amateur_probs = self._softmax(amateur_logits)

        # Calculate KL divergence: D_KL(Expert || Amateur)
        # Measures how much expert diverges from amateur
        kl_div = np.sum(expert_probs * np.log(
            (expert_probs + 1e-10) / (amateur_probs + 1e-10)
        ))

        # Map KL divergence to alpha
        # Higher divergence -> higher alpha -> stronger contrast
        # Typical KL range: 0-5, map to alpha range: 0.1-0.9
        alpha = np.clip(0.1 + kl_div * 0.15, 0.1, 0.9)

        self._log(f"KL divergence: {kl_div:.3f}, alpha: {alpha:.3f}")
        return float(alpha)

    def _softmax(self, logits: np.ndarray) -> np.ndarray:
        """Stable softmax computation."""
        logits = sampling_utils.sanitize_logits(logits)
        logits_shifted = logits - np.max(logits)
        exp_logits = np.exp(logits_shifted)
        return exp_logits / np.sum(exp_logits)

    def contrast_logits(
        self,
        expert_logits: np.ndarray,
        amateur_logits: np.ndarray,
        alpha: Optional[float] = None
    ) -> np.ndarray:
        """
        Perform contrastive decoding on logits.

        Args:
            expert_logits: Raw logits from expert model
            amateur_logits: Raw logits from amateur model
            alpha: Contrast weight (if None, uses config/adaptive)

        Returns:
            Contrasted logits
        """
        # Handle vocabulary size mismatches
        min_vocab = min(len(expert_logits), len(amateur_logits))
        expert_logits = expert_logits[:min_vocab]
        amateur_logits = amateur_logits[:min_vocab]

        # Determine alpha
        if alpha is None:
            if self.config.use_adaptive_alpha:
                alpha = self.calculate_adaptive_alpha(expert_logits, amateur_logits)
            else:
                alpha = self.config.alpha

        # Contrastive formula: expert - alpha * amateur
        contrasted = expert_logits - alpha * amateur_logits

        # Apply minimum probability threshold (prevent over-suppression)
        # Convert to probs, apply threshold, convert back
        contrasted_probs = self._softmax(contrasted)
        contrasted_probs = np.maximum(contrasted_probs, self.config.beta)

        # Renormalize
        contrasted_probs = contrasted_probs / np.sum(contrasted_probs)

        # Convert back to logits
        contrasted_logits = np.log(contrasted_probs + 1e-10)

        # Update stats
        self.avg_alpha_used = (self.avg_alpha_used * self.total_tokens + alpha) / (self.total_tokens + 1)

        return contrasted_logits

    def predict_next(
        self,
        context: str,
        temperature: float = 1.0,
        top_k: int = 50,
        top_p: float = 0.95
    ) -> Tuple[int, str, Dict[str, Any]]:
        """
        Generate next token using contrastive decoding.

        Args:
            context: Current context
            temperature: Sampling temperature
            top_k: Top-K filtering
            top_p: Top-P filtering

        Returns:
            (token_id, token_text, metadata)
        """
        # Get predictions from both models
        expert_input_ids, expert_mask = self.expert_model.encode(context, add_special_tokens=True)
        amateur_input_ids, amateur_mask = self.amateur_model.encode(context, add_special_tokens=True)

        expert_result = self.expert_model.predict_next(
            expert_input_ids, expert_mask,
            temperature=temperature, top_k=top_k, top_p=top_p
        )

        amateur_result = self.amateur_model.predict_next(
            amateur_input_ids, amateur_mask,
            temperature=temperature, top_k=top_k, top_p=top_p
        )

        # Get raw logits
        expert_logits = self.expert_model.convert_to_numpy(expert_result['logits_raw'])
        amateur_logits = self.amateur_model.convert_to_numpy(amateur_result['logits_raw'])

        # Flatten if needed
        if expert_logits.ndim > 1:
            expert_logits = expert_logits.flatten()
        if amateur_logits.ndim > 1:
            amateur_logits = amateur_logits.flatten()

        # Perform contrastive decoding
        contrasted_logits = self.contrast_logits(expert_logits, amateur_logits)

        # Sample from contrasted distribution
        contrasted_probs = self._softmax(contrasted_logits / temperature)

        # Apply top-k and top-p filtering
        if top_k > 0:
            top_k_indices = np.argsort(contrasted_probs)[-top_k:]
            filtered_probs = np.zeros_like(contrasted_probs)
            filtered_probs[top_k_indices] = contrasted_probs[top_k_indices]
            contrasted_probs = filtered_probs / np.sum(filtered_probs)

        # Sample token
        token_id = np.argmax(contrasted_probs)
        token_text = self.expert_model.get_token_text(token_id)

        # Calculate confidences
        expert_conf = float(np.max(self._softmax(expert_logits)))
        amateur_conf = float(np.max(self._softmax(amateur_logits)))

        # Update stats
        self.total_tokens += 1
        self.avg_expert_confidence = (
            self.avg_expert_confidence * (self.total_tokens - 1) + expert_conf
        ) / self.total_tokens
        self.avg_amateur_confidence = (
            self.avg_amateur_confidence * (self.total_tokens - 1) + amateur_conf
        ) / self.total_tokens

        metadata = {
            'expert_confidence': expert_conf,
            'amateur_confidence': amateur_conf,
            'alpha_used': float(self.avg_alpha_used),
            'expert_top_token': int(expert_result['next_token_id']),
            'amateur_top_token': int(amateur_result['next_token_id']),
            'agreement': expert_result['next_token_id'] == amateur_result['next_token_id']
        }

        return token_id, token_text, metadata

    def generate(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 1.0,
        top_k: int = 50,
        top_p: float = 0.95
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate text using contrastive decoding.

        Args:
            prompt: Initial prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_k: Top-K filtering
            top_p: Top-P filtering

        Returns:
            (generated_text, statistics)
        """
        generated = prompt
        agreement_count = 0
        disagreement_count = 0

        for i in range(max_tokens):
            token_id, token_text, metadata = self.predict_next(
                generated,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p
            )

            generated += token_text

            if metadata['agreement']:
                agreement_count += 1
            else:
                disagreement_count += 1

            # Check for EOS
            if token_id == self.expert_model.get_eos_token_id():
                break

        stats = {
            'total_tokens': self.total_tokens,
            'avg_expert_confidence': self.avg_expert_confidence,
            'avg_amateur_confidence': self.avg_amateur_confidence,
            'avg_alpha': self.avg_alpha_used,
            'agreement_rate': agreement_count / max(agreement_count + disagreement_count, 1),
            'disagreement_count': disagreement_count
        }

        return generated, stats

    def get_stats(self) -> Dict[str, Any]:
        """Get decoder statistics."""
        return {
            'total_tokens': self.total_tokens,
            'avg_expert_confidence': self.avg_expert_confidence,
            'avg_amateur_confidence': self.avg_amateur_confidence,
            'avg_alpha': self.avg_alpha_used,
            'config': {
                'alpha': self.config.alpha,
                'beta': self.config.beta,
                'adaptive': self.config.use_adaptive_alpha
            }
        }

    def reset_stats(self):
        """Reset statistics."""
        self.total_tokens = 0
        self.avg_expert_confidence = 0.0
        self.avg_amateur_confidence = 0.0
        self.avg_alpha_used = 0.0


class MultiModelContrastiveDecoder:
    """
    Contrastive decoding with multiple expert/amateur pairs.

    Allows different amateurs to contrast different aspects of the expert.
    """

    def __init__(
        self,
        expert_model: LLMEngine,
        amateur_models: List[LLMEngine],
        weights: Optional[List[float]] = None,
        config: Optional[ContrastiveConfig] = None,
        verbose: bool = False
    ):
        """
        Initialize multi-model contrastive decoder.

        Args:
            expert_model: Expert model
            amateur_models: List of amateur models
            weights: Weights for each amateur's contribution
            config: Configuration
            verbose: Enable verbose logging
        """
        self.expert_model = expert_model
        self.amateur_models = amateur_models
        self.weights = weights or [1.0 / len(amateur_models)] * len(amateur_models)
        self.config = config or ContrastiveConfig()
        self.verbose = verbose

        # Normalize weights
        weight_sum = sum(self.weights)
        self.weights = [w / weight_sum for w in self.weights]

    def contrast_logits(
        self,
        expert_logits: np.ndarray,
        amateur_logits_list: List[np.ndarray]
    ) -> np.ndarray:
        """Contrast expert against weighted combination of amateurs."""
        # Combine amateur logits with weights
        combined_amateur = np.zeros_like(expert_logits)

        for amateur_logits, weight in zip(amateur_logits_list, self.weights):
            # Handle vocab size mismatch
            min_vocab = min(len(combined_amateur), len(amateur_logits))
            combined_amateur[:min_vocab] += weight * amateur_logits[:min_vocab]

        # Perform contrastive decoding
        decoder = ContrastiveDecoder(self.expert_model, None, self.config, self.verbose)
        # Temporarily override amateur logits
        return expert_logits - self.config.alpha * combined_amateur
