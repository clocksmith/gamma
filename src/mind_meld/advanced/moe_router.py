"""
Mixture-of-Experts (MoE) style routing for Mind Meld.

Routes generation to specialist models based on content classification.
Each model is an "expert" in certain types of content.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from collections import deque, Counter

from src.core.engine_interface import LLMEngine
from src.mind_meld.utils import VerboseLoggerMixin


class ContentType(Enum):
    """Types of content for routing."""
    CODE = "code"
    PROSE = "prose"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    MATH = "math"
    DIALOGUE = "dialogue"
    LIST = "list"
    UNKNOWN = "unknown"


class ContentClassifier(VerboseLoggerMixin):
    """
    Classify content type for routing decisions.

    Uses simple heuristics and keyword matching.
    Can be extended with ML models.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.history = deque(maxlen=50)

        # Define classification patterns
        self.code_keywords = {
            'def', 'class', 'import', 'function', 'return', 'if', 'else',
            'for', 'while', 'print', 'console.log', 'const', 'let', 'var',
            '{}', '[]', '()', '=>', '==', '!=', '++', '--'
        }

        self.math_keywords = {
            'equation', 'solve', 'calculate', 'formula', 'theorem',
            'proof', 'derivative', 'integral', 'matrix', 'vector',
            '+', '-', '*', '/', '=', '∫', '∑', '∂'
        }

        self.technical_keywords = {
            'algorithm', 'system', 'architecture', 'implementation',
            'protocol', 'interface', 'component', 'module', 'framework',
            'optimization', 'performance', 'scalability'
        }

        self.creative_keywords = {
            'story', 'character', 'scene', 'narrative', 'plot',
            'protagonist', 'adventure', 'journey', 'emotion', 'beautiful',
            'mysterious', 'dramatic', 'poetry', 'metaphor'
        }

    def classify_context(self, context: str) -> ContentType:
        """
        Classify content type based on context.

        Args:
            context: Text context to classify

        Returns:
            ContentType classification
        """
        context_lower = context.lower()

        # Count keyword matches
        code_score = sum(1 for kw in self.code_keywords if kw in context_lower)
        math_score = sum(1 for kw in self.math_keywords if kw in context_lower)
        technical_score = sum(1 for kw in self.technical_keywords if kw in context_lower)
        creative_score = sum(1 for kw in self.creative_keywords if kw in context_lower)

        # Check for dialogue markers
        dialogue_markers = context.count('"') + context.count("'") + context.count(':')
        dialogue_score = dialogue_markers // 2

        # Check for list markers
        list_markers = context.count('\n- ') + context.count('\n* ') + context.count('\n1.')
        list_score = list_markers

        # Check for code-like patterns
        if any(pattern in context for pattern in ['```', 'def ', 'class ', 'import ', 'function ']):
            code_score += 5

        # Determine content type
        scores = {
            ContentType.CODE: code_score,
            ContentType.MATH: math_score,
            ContentType.TECHNICAL: technical_score,
            ContentType.CREATIVE: creative_score,
            ContentType.DIALOGUE: dialogue_score,
            ContentType.LIST: list_score
        }

        if max(scores.values()) == 0:
            # Default to prose if no specific indicators
            classification = ContentType.PROSE
        else:
            classification = max(scores.items(), key=lambda x: x[1])[0]

        self.history.append(classification)
        self._log(f"Classified as {classification.value} (scores: {scores})")

        return classification

    def get_dominant_type(self, window: int = 10) -> ContentType:
        """Get most common content type in recent history."""
        recent = list(self.history)[-window:]
        if not recent:
            return ContentType.PROSE

        counter = Counter(recent)
        return counter.most_common(1)[0][0]

    def predict_next_type(self, current_type: ContentType, token: str) -> ContentType:
        """Predict content type for next generation step."""
        # Simple transitions
        if token in ['```', '`']:
            return ContentType.CODE

        if token in ['\n', '.', '!', '?']:
            # Potential transition point - use recent history
            return self.get_dominant_type(window=3)

        # Continue current type
        return current_type


class MoERouter(VerboseLoggerMixin):
    """
    Mixture-of-Experts router for Mind Meld.

    Routes generation to specialist models based on content type.
    """

    def __init__(
        self,
        models: Dict[ContentType, LLMEngine],
        classifier: Optional[ContentClassifier] = None,
        fallback_model: Optional[LLMEngine] = None,
        verbose: bool = False
    ):
        """
        Initialize MoE router.

        Args:
            models: Dict mapping ContentType to specialist models
            classifier: Content classifier (creates one if None)
            fallback_model: Model to use when no specialist available
            verbose: Enable verbose logging
        """
        self.models = models
        self.classifier = classifier or ContentClassifier(verbose=verbose)
        self.fallback_model = fallback_model or list(models.values())[0]
        self.verbose = verbose

        # Statistics
        self.routing_stats = {ctype: 0 for ctype in ContentType}
        self.total_tokens = 0

    def get_expert_for_content(self, content_type: ContentType) -> LLMEngine:
        """Get expert model for content type."""
        model = self.models.get(content_type, self.fallback_model)
        self.routing_stats[content_type] += 1
        self.total_tokens += 1
        return model

    def route_generation(
        self,
        context: str,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.95
    ) -> Tuple[int, str, ContentType, LLMEngine]:
        """
        Route generation to appropriate expert and generate token.

        Args:
            context: Current generation context
            temperature: Sampling temperature
            top_k: Top-K filtering
            top_p: Top-P filtering

        Returns:
            (token_id, token_text, content_type, model_used)
        """
        # Classify content
        content_type = self.classifier.classify_context(context)

        # Get appropriate expert
        expert = self.get_expert_for_content(content_type)

        self._log(f"Routing to {expert.model_name} for {content_type.value} content")

        # Generate token
        input_ids, attention_mask = expert.encode(context, add_special_tokens=True)
        result = expert.predict_next(
            input_ids,
            attention_mask,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p
        )

        token_id = result['next_token_id']
        token_text = expert.get_token_text(token_id)

        return token_id, token_text, content_type, expert

    def generate(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.95
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate text with MoE routing.

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
        content_type_sequence = []
        model_sequence = []

        for _ in range(max_tokens):
            token_id, token_text, content_type, model_used = self.route_generation(
                generated,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p
            )

            generated += token_text
            content_type_sequence.append(content_type.value)
            model_sequence.append(model_used.model_name)

            # Check for EOS
            if token_id == model_used.get_eos_token_id():
                break

        # Calculate statistics
        content_distribution = {
            ctype.value: count / self.total_tokens if self.total_tokens > 0 else 0
            for ctype, count in self.routing_stats.items()
        }

        # Count model switches
        switches = sum(1 for i in range(1, len(model_sequence))
                      if model_sequence[i] != model_sequence[i-1])

        stats = {
            'total_tokens': len(content_type_sequence),
            'content_distribution': content_distribution,
            'model_switches': switches,
            'unique_models_used': len(set(model_sequence)),
            'model_sequence': model_sequence[:20],  # First 20 for inspection
            'content_sequence': content_type_sequence[:20]
        }

        return generated, stats

    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        return {
            'total_tokens': self.total_tokens,
            'routing_distribution': {
                ctype.value: count for ctype, count in self.routing_stats.items()
            },
            'available_experts': [ctype.value for ctype in self.models.keys()]
        }

    def reset_stats(self):
        """Reset statistics."""
        self.routing_stats = {ctype: 0 for ctype in ContentType}
        self.total_tokens = 0
        self.classifier.history.clear()


class AdaptiveMoERouter(MoERouter):
    """
    Adaptive MoE router that learns from generation quality.

    Adjusts routing decisions based on recent performance.
    """

    def __init__(
        self,
        models: Dict[ContentType, LLMEngine],
        classifier: Optional[ContentClassifier] = None,
        fallback_model: Optional[LLMEngine] = None,
        learning_rate: float = 0.1,
        verbose: bool = False
    ):
        """
        Initialize adaptive router.

        Args:
            models: Dict mapping ContentType to specialist models
            classifier: Content classifier
            fallback_model: Fallback model
            learning_rate: Learning rate for adaptation
            verbose: Enable verbose logging
        """
        super().__init__(models, classifier, fallback_model, verbose)
        self.learning_rate = learning_rate

        # Performance tracking per content type
        self.performance_scores = {
            ctype: {model.model_name: 1.0 for model in models.values()}
            for ctype in ContentType
        }

    def update_performance(
        self,
        content_type: ContentType,
        model_name: str,
        score: float
    ):
        """
        Update performance score for model on content type.

        Args:
            content_type: Content type
            model_name: Model name
            score: Performance score (0-1, higher is better)
        """
        if content_type not in self.performance_scores:
            self.performance_scores[content_type] = {}

        current_score = self.performance_scores[content_type].get(model_name, 0.5)
        # Exponential moving average
        new_score = (1 - self.learning_rate) * current_score + self.learning_rate * score
        self.performance_scores[content_type][model_name] = new_score

        self._log(f"Updated {model_name} score for {content_type.value}: {new_score:.3f}")

    def get_expert_for_content(self, content_type: ContentType) -> LLMEngine:
        """Get best performing expert for content type."""
        # Get performance scores for this content type
        scores = self.performance_scores.get(content_type, {})

        if not scores:
            return super().get_expert_for_content(content_type)

        # Find model with best score
        best_model_name = max(scores.items(), key=lambda x: x[1])[0]

        # Find corresponding engine
        for model in self.models.values():
            if model.model_name == best_model_name:
                self.routing_stats[content_type] += 1
                self.total_tokens += 1
                return model

        return super().get_expert_for_content(content_type)
