"""
Quality metrics for LLM output evaluation.

Provides standardized metrics for measuring:
- Text quality (perplexity, coherence, diversity)
- Output consistency (same prompt, multiple runs)
- Latency distribution (p50, p95, p99)
- Generation characteristics (repetition, entropy)
"""
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


@dataclass
class QualityMetrics:
    """Container for all quality metrics."""
    # Text quality
    perplexity: Optional[float] = None
    coherence_score: Optional[float] = None
    diversity_score: Optional[float] = None

    # Repetition metrics
    repetition_ratio: Optional[float] = None
    unique_ngram_ratio: Optional[float] = None

    # Latency percentiles
    latency_p50: Optional[float] = None
    latency_p95: Optional[float] = None
    latency_p99: Optional[float] = None
    latency_mean: Optional[float] = None
    latency_std: Optional[float] = None

    # Consistency (across multiple runs)
    output_consistency: Optional[float] = None
    token_agreement_rate: Optional[float] = None

    # Generation stats
    avg_token_entropy: Optional[float] = None
    avg_confidence: Optional[float] = None
    eos_reached: bool = False
    tokens_generated: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def to_report_dict(self) -> Dict[str, str]:
        """Convert to formatted report dictionary."""
        report = {}
        if self.perplexity is not None:
            report["Perplexity"] = f"{self.perplexity:.2f}"
        if self.coherence_score is not None:
            report["Coherence"] = f"{self.coherence_score:.2%}"
        if self.diversity_score is not None:
            report["Diversity"] = f"{self.diversity_score:.2%}"
        if self.repetition_ratio is not None:
            report["Repetition"] = f"{self.repetition_ratio:.2%}"
        if self.latency_p50 is not None:
            report["Latency (p50)"] = f"{self.latency_p50:.1f}ms"
        if self.latency_p95 is not None:
            report["Latency (p95)"] = f"{self.latency_p95:.1f}ms"
        if self.latency_p99 is not None:
            report["Latency (p99)"] = f"{self.latency_p99:.1f}ms"
        if self.output_consistency is not None:
            report["Consistency"] = f"{self.output_consistency:.2%}"
        if self.avg_confidence is not None:
            report["Avg Confidence"] = f"{self.avg_confidence:.2%}"
        return report


class QualityAnalyzer:
    """Analyzes quality of LLM outputs."""

    def __init__(self):
        self.latencies: List[float] = []
        self.token_probs: List[float] = []
        self.outputs: List[str] = []
        self.token_sequences: List[List[int]] = []

    def reset(self):
        """Reset all collected data."""
        self.latencies = []
        self.token_probs = []
        self.outputs = []
        self.token_sequences = []

    def record_latency(self, latency_ms: float):
        """Record a token generation latency."""
        self.latencies.append(latency_ms)

    def record_token_prob(self, prob: float):
        """Record token probability for confidence tracking."""
        self.token_probs.append(prob)

    def record_output(self, text: str, token_ids: Optional[List[int]] = None):
        """Record a generated output."""
        self.outputs.append(text)
        if token_ids:
            self.token_sequences.append(token_ids)

    def compute_metrics(self) -> QualityMetrics:
        """Compute all quality metrics from recorded data."""
        metrics = QualityMetrics()

        # Latency percentiles
        if self.latencies:
            latencies = np.array(self.latencies)
            metrics.latency_mean = float(np.mean(latencies))
            metrics.latency_std = float(np.std(latencies))
            metrics.latency_p50 = float(np.percentile(latencies, 50))
            metrics.latency_p95 = float(np.percentile(latencies, 95))
            metrics.latency_p99 = float(np.percentile(latencies, 99))

        # Confidence metrics
        if self.token_probs:
            probs = np.array(self.token_probs)
            metrics.avg_confidence = float(np.mean(probs))
            # Entropy from probabilities
            valid_probs = probs[probs > 0]
            if len(valid_probs) > 0:
                entropy = -np.mean(valid_probs * np.log2(valid_probs))
                metrics.avg_token_entropy = float(entropy)

        # Text quality metrics
        if self.outputs:
            metrics.diversity_score = self._compute_diversity(self.outputs)
            metrics.repetition_ratio = self._compute_repetition(self.outputs)
            metrics.coherence_score = self._compute_coherence(self.outputs)

            if len(self.outputs) > 1:
                metrics.output_consistency = self._compute_consistency(self.outputs)

        # Token-level metrics
        if self.token_sequences:
            metrics.tokens_generated = sum(len(seq) for seq in self.token_sequences)
            if len(self.token_sequences) > 1:
                metrics.token_agreement_rate = self._compute_token_agreement()
            metrics.unique_ngram_ratio = self._compute_ngram_diversity()

        return metrics

    def _compute_diversity(self, texts: List[str]) -> float:
        """Compute lexical diversity (unique words / total words)."""
        all_words = []
        for text in texts:
            words = re.findall(r'\b\w+\b', text.lower())
            all_words.extend(words)

        if not all_words:
            return 0.0

        return len(set(all_words)) / len(all_words)

    def _compute_repetition(self, texts: List[str]) -> float:
        """Compute repetition ratio (repeated n-grams)."""
        all_text = " ".join(texts)
        words = re.findall(r'\b\w+\b', all_text.lower())

        if len(words) < 3:
            return 0.0

        # Count trigram repetitions
        trigrams = [tuple(words[i:i+3]) for i in range(len(words)-2)]
        trigram_counts = Counter(trigrams)

        repeated = sum(1 for count in trigram_counts.values() if count > 1)
        return repeated / len(trigrams) if trigrams else 0.0

    def _compute_coherence(self, texts: List[str]) -> float:
        """
        Compute simple coherence score based on sentence structure.
        Higher = more coherent (consistent sentence lengths, proper punctuation).
        """
        scores = []
        for text in texts:
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]

            if not sentences:
                scores.append(0.0)
                continue

            # Score based on:
            # 1. Has multiple sentences
            # 2. Sentences have reasonable length
            # 3. Ends with punctuation

            score = 0.0

            # Multiple sentences
            if len(sentences) > 1:
                score += 0.3

            # Reasonable sentence lengths (5-30 words)
            lengths = [len(s.split()) for s in sentences]
            good_lengths = sum(1 for l in lengths if 5 <= l <= 30)
            score += 0.4 * (good_lengths / len(lengths))

            # Ends with punctuation
            if text.rstrip()[-1:] in '.!?':
                score += 0.3

            scores.append(score)

        return sum(scores) / len(scores) if scores else 0.0

    def _compute_consistency(self, texts: List[str]) -> float:
        """Compute output consistency across multiple runs."""
        if len(texts) < 2:
            return 1.0

        # Compare each pair of outputs
        similarities = []
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                sim = self._text_similarity(texts[i], texts[j])
                similarities.append(sim)

        return sum(similarities) / len(similarities) if similarities else 1.0

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Compute Jaccard similarity between two texts."""
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))

        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union

    def _compute_token_agreement(self) -> float:
        """Compute token-level agreement across multiple runs."""
        if len(self.token_sequences) < 2:
            return 1.0

        # Find minimum length
        min_len = min(len(seq) for seq in self.token_sequences)
        if min_len == 0:
            return 0.0

        agreements = 0
        for pos in range(min_len):
            tokens_at_pos = [seq[pos] for seq in self.token_sequences]
            # Check if all tokens at this position are the same
            if len(set(tokens_at_pos)) == 1:
                agreements += 1

        return agreements / min_len

    def _compute_ngram_diversity(self, n: int = 3) -> float:
        """Compute unique n-gram ratio across all token sequences."""
        all_ngrams = []
        for seq in self.token_sequences:
            if len(seq) >= n:
                ngrams = [tuple(seq[i:i+n]) for i in range(len(seq)-n+1)]
                all_ngrams.extend(ngrams)

        if not all_ngrams:
            return 1.0

        return len(set(all_ngrams)) / len(all_ngrams)


def compute_perplexity(logits_sequence: List[np.ndarray], token_ids: List[int]) -> float:
    """
    Compute perplexity from a sequence of logits and corresponding token IDs.

    Args:
        logits_sequence: List of logit arrays (vocab_size,) for each position
        token_ids: List of actual token IDs that were selected

    Returns:
        Perplexity score (lower = better)
    """
    if not logits_sequence or not token_ids:
        return float('inf')

    total_log_prob = 0.0
    count = 0

    for logits, token_id in zip(logits_sequence, token_ids):
        # Convert logits to probabilities
        logits = np.array(logits).flatten()
        max_logit = np.max(logits)
        exp_logits = np.exp(logits - max_logit)  # Numerical stability
        probs = exp_logits / np.sum(exp_logits)

        # Get probability of the actual token
        if 0 <= token_id < len(probs):
            prob = probs[token_id]
            if prob > 0:
                total_log_prob += np.log(prob)
                count += 1

    if count == 0:
        return float('inf')

    avg_log_prob = total_log_prob / count
    perplexity = np.exp(-avg_log_prob)

    return float(perplexity)


@dataclass
class BenchmarkReport:
    """Unified benchmark report format."""
    title: str
    timestamp: str
    summary: Dict[str, Any] = field(default_factory=dict)
    models: List[Dict[str, Any]] = field(default_factory=list)
    comparison: Optional[Dict[str, Any]] = None
    quality_metrics: Optional[QualityMetrics] = None

    def add_model_result(
        self,
        name: str,
        engine: str,
        metrics: Dict[str, float],
        quality: Optional[QualityMetrics] = None
    ):
        """Add a model's benchmark results."""
        result = {
            "name": name,
            "engine": engine,
            "metrics": metrics,
        }
        if quality:
            result["quality"] = quality.to_dict()
        self.models.append(result)

    def generate_comparison(self):
        """Generate comparison between models."""
        if len(self.models) < 2:
            return

        self.comparison = {
            "fastest": None,
            "most_consistent": None,
            "lowest_perplexity": None,
            "rankings": {}
        }

        # Speed ranking
        speed_key = "tokens_per_second_mean"
        speeds = [(m["name"], m["metrics"].get(speed_key, 0)) for m in self.models]
        speeds.sort(key=lambda x: x[1], reverse=True)
        if speeds and speeds[0][1] > 0:
            self.comparison["fastest"] = speeds[0][0]
            self.comparison["rankings"]["speed"] = [s[0] for s in speeds]

        # Consistency ranking (if available)
        consistency = []
        for m in self.models:
            if "quality" in m and "output_consistency" in m["quality"]:
                consistency.append((m["name"], m["quality"]["output_consistency"]))
        if consistency:
            consistency.sort(key=lambda x: x[1], reverse=True)
            self.comparison["most_consistent"] = consistency[0][0]
            self.comparison["rankings"]["consistency"] = [c[0] for c in consistency]

    def to_text(self, width: int = 80) -> str:
        """Generate text report."""
        lines = []
        sep = "=" * width

        lines.append(sep)
        lines.append(f" {self.title}".center(width))
        lines.append(f" {self.timestamp}".center(width))
        lines.append(sep)
        lines.append("")

        # Summary
        if self.summary:
            lines.append("SUMMARY")
            lines.append("-" * width)
            for key, value in self.summary.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        # Model results
        lines.append("MODEL RESULTS")
        lines.append("-" * width)

        # Table header
        header = f"{'Model':<30} {'Engine':<12} {'Tokens/s':>10} {'Latency':>12} {'Quality':>10}"
        lines.append(header)
        lines.append("-" * width)

        for m in self.models:
            name = m["name"][:28] + ".." if len(m["name"]) > 30 else m["name"]
            engine = m["engine"][:10] + ".." if len(m["engine"]) > 12 else m["engine"]
            tps = m["metrics"].get("tokens_per_second_mean", 0)
            latency = m["metrics"].get("latency_ms_mean", 0)

            quality_str = "-"
            if "quality" in m:
                q = m["quality"]
                if "coherence_score" in q:
                    quality_str = f"{q['coherence_score']:.0%}"
                elif "diversity_score" in q:
                    quality_str = f"{q['diversity_score']:.0%}"

            lines.append(f"{name:<30} {engine:<12} {tps:>10.2f} {latency:>10.1f}ms {quality_str:>10}")

        lines.append("")

        # Comparison
        if self.comparison:
            lines.append("COMPARISON")
            lines.append("-" * width)
            if self.comparison.get("fastest"):
                lines.append(f"  Fastest: {self.comparison['fastest']}")
            if self.comparison.get("most_consistent"):
                lines.append(f"  Most Consistent: {self.comparison['most_consistent']}")
            lines.append("")

        lines.append(sep)

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "models": self.models,
            "comparison": self.comparison,
        }
