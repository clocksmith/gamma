"""
Comprehensive benchmarking suite for Mind Meld strategies.

Tests different configurations across multiple dimensions:
- Speed (tokens/sec)
- Quality proxies (perplexity proxy, coherence proxy, lexical diversity)
- Memory usage (VRAM)
- Strategy effectiveness
"""

import hashlib
import logging
import platform
import random
import time
import json
import sys
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict, field
import numpy as np

from src.core.fallback_telemetry import FallbackTelemetry
from src.core.engine_interface import LLMEngine
from src.mind_meld.core.meld_engine import MeldEngine
from src.mind_meld.strategies.base_strategy import SwapStrategyBase

logger = logging.getLogger(__name__)


QUALITY_METRIC_CONTRACT: Dict[str, str] = {
    "avg_perplexity_proxy": (
        "Heuristic proxy computed as inverse max next-token probability from "
        "single-step logits. Not corpus perplexity."
    ),
    "coherence_proxy_score": (
        "Heuristic score derived from sentence-length variance and transition-word "
        "counts. Not a reference-based coherence metric."
    ),
    "diversity_score": "Lexical diversity (unique words / total words).",
    "swap_overhead_ms": "Estimated swap overhead (fixed ~5ms per swap), not measured latency.",
}


@dataclass
class BenchmarkConfig:
    """Configuration for a benchmark run."""
    strategy_name: str
    models: List[str]
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7
    top_k: int = 50
    top_p: float = 0.95
    seed: int = 42


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    config: BenchmarkConfig
    generated_text: str

    # Performance metrics
    total_time: float
    tokens_per_second: float
    avg_token_latency: float

    # Memory metrics
    peak_vram_mb: int
    avg_vram_mb: float

    # Quality metrics (heuristic proxies; see QUALITY_METRIC_CONTRACT)
    avg_perplexity_proxy: float
    coherence_proxy_score: float
    diversity_score: float

    # Strategy metrics
    swap_count: int
    swap_overhead_ms: float

    # Token-level data
    token_latencies: List[float]
    vram_samples: List[int]

    # KV cache stability metrics
    kv_cache_attempts: int = 0
    kv_cache_successes: int = 0
    kv_cache_replays: int = 0
    kv_cache_translations: int = 0
    guardrail_replays: int = 0

    # Metadata
    timestamp: float = 0.0
    success: bool = False
    error: Optional[str] = None
    metric_contract: Dict[str, str] = field(default_factory=dict)
    reproducibility: Dict[str, Any] = field(default_factory=dict)

    @property
    def avg_perplexity(self) -> float:
        """Backward-compatible alias for older consumers."""
        return self.avg_perplexity_proxy

    @property
    def coherence_score(self) -> float:
        """Backward-compatible alias for older consumers."""
        return self.coherence_proxy_score


@dataclass
class StabilityResult:
    """Results from stability benchmarking across multiple runs."""
    config: BenchmarkConfig
    num_runs: int

    # Output consistency
    output_similarity_mean: float  # Average pairwise similarity
    output_similarity_std: float   # Std dev of similarity
    exact_match_rate: float        # Fraction of identical outputs

    # Performance stability
    speed_mean: float
    speed_std: float
    latency_mean: float
    latency_std: float

    # KV cache stability
    kv_success_rate_mean: float
    kv_replay_rate_mean: float
    guardrail_trigger_rate: float

    # Individual run results
    individual_results: List[BenchmarkResult]


class MindMeldBenchmark:
    """Comprehensive benchmarking for Mind Meld."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results: List[BenchmarkResult] = []
        self._fallbacks = FallbackTelemetry("mind_meld_benchmark", logger)

    def _log(self, message: str):
        """Log if verbose."""
        if self.verbose:
            print(f"[Benchmark] {message}")

    def _set_seed(self, seed: int) -> None:
        """Set deterministic seeds for benchmark-side randomness."""
        random.seed(int(seed))
        np.random.seed(int(seed))
        try:
            import torch
            torch.manual_seed(int(seed))
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(int(seed))
        except (ImportError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
            # Optional torch dependency for benchmark setup.
            self._fallbacks.record("seed_torch_unavailable", exc)

    def _collect_reproducibility_metadata(self, config: BenchmarkConfig, meld_engine: MeldEngine) -> Dict[str, Any]:
        """Capture run metadata needed to reproduce benchmark behavior."""
        model_fingerprints: List[Dict[str, Any]] = []
        engines = getattr(meld_engine, "engines", [])
        for idx, engine in enumerate(engines):
            identity: Dict[str, Any] = {
                "index": int(idx),
                "class": engine.__class__.__name__,
                "model_name": str(getattr(engine, "model_name", "")),
                "model_path": str(getattr(engine, "model_path", "")),
                "engine_name": str(getattr(engine, "engine_name", "")),
                "device": str(getattr(engine, "device", "")),
            }
            blob = json.dumps(identity, sort_keys=True, default=str, separators=(",", ":"))
            identity["fingerprint_sha256"] = hashlib.sha256(blob.encode("utf-8")).hexdigest()
            model_fingerprints.append(identity)

        metadata: Dict[str, Any] = {
            "seed": int(config.seed),
            "python_version": str(sys.version.split()[0]),
            "platform": platform.platform(),
            "numpy_version": str(np.__version__),
            "model_fingerprints": model_fingerprints,
        }
        try:
            import torch
            metadata["torch_version"] = str(torch.__version__)
            metadata["torch_cuda_available"] = bool(torch.cuda.is_available())
        except (ImportError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
            self._fallbacks.record("metadata_torch_unavailable", exc)
            metadata["torch_version"] = ""
            metadata["torch_cuda_available"] = False
        metadata["fallback_counts"] = self._fallbacks.snapshot()
        return metadata

    def _measure_vram(self) -> int:
        """Measure current VRAM usage in MB."""
        try:
            import torch
            if torch.cuda.is_available():
                return torch.cuda.memory_allocated() // (1024 ** 2)
        except (ImportError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
            self._fallbacks.record("measure_vram_failed", exc)
        return 0

    def _calculate_perplexity(self, logits: np.ndarray) -> float:
        """Calculate a next-token perplexity proxy from logits."""
        probs = np.exp(logits) / np.sum(np.exp(logits))
        max_prob = np.max(probs)
        return 1.0 / max(max_prob, 1e-10)

    def _calculate_coherence(self, text: str) -> float:
        """
        Calculate coherence score (simplified).

        Measures: sentence length variance, transition words, etc.
        """
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if not sentences:
            return 0.0

        # Sentence length variance (lower is more coherent)
        lengths = [len(s.split()) for s in sentences]
        length_variance = np.var(lengths) if len(lengths) > 1 else 0

        # Transition words
        transitions = ['however', 'therefore', 'moreover', 'furthermore', 'additionally']
        transition_count = sum(1 for t in transitions if t in text.lower())

        # Combine metrics (0-1 scale)
        coherence = 0.5  # Base score
        coherence += 0.2 * min(transition_count / len(sentences), 1.0)
        coherence -= 0.1 * min(length_variance / 100, 1.0)

        return np.clip(coherence, 0.0, 1.0)

    def _calculate_diversity(self, text: str) -> float:
        """Calculate lexical diversity (unique words / total words)."""
        words = text.lower().split()
        if not words:
            return 0.0
        return len(set(words)) / len(words)

    def run_single_benchmark(
        self,
        config: BenchmarkConfig,
        meld_engine: MeldEngine
    ) -> BenchmarkResult:
        """Run a single benchmark configuration."""
        self._log(f"Running benchmark: {config.strategy_name} with {len(config.models)} models")
        self._set_seed(int(config.seed))

        # Warmup
        try:
            input_ids, mask = meld_engine.get_active_engine().encode("warmup", add_special_tokens=True)
            meld_engine.get_active_engine().predict_next(input_ids, mask, 0.7, 50, 0.95)
        except (AttributeError, KeyError, RuntimeError, TypeError, ValueError) as exc:
            self._fallbacks.record("warmup_failed", exc, level=logging.INFO)

        # Reset caches
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.reset_peak_memory_stats()
        except (ImportError, AttributeError, RuntimeError, TypeError, ValueError) as exc:
            self._fallbacks.record("cache_reset_failed", exc)

        # Start benchmark
        start_time = time.time()
        start_vram = self._measure_vram()

        token_latencies = []
        vram_samples = []
        perplexities = []

        generated = config.prompt
        success = True
        error = None

        try:
            for i in range(config.max_tokens):
                token_start = time.time()

                # Generate token
                active_engine = meld_engine.get_active_engine()
                input_ids, attention_mask = active_engine.encode(generated, add_special_tokens=True)

                result = active_engine.predict_next(
                    input_ids,
                    attention_mask,
                    temperature=config.temperature,
                    top_k=config.top_k,
                    top_p=config.top_p
                )

                token_id = result['next_token_id']
                token_text = active_engine.get_token_text(token_id)
                generated += token_text

                # Measurements
                token_latency = time.time() - token_start
                token_latencies.append(token_latency)
                vram_samples.append(self._measure_vram())

                # Calculate perplexity
                logits = active_engine.convert_to_numpy(result['logits_raw'])
                if logits.ndim > 1:
                    logits = logits.flatten()
                perplexities.append(self._calculate_perplexity(logits))

                # Check EOS
                if token_id == active_engine.get_eos_token_id():
                    break

        except (AttributeError, KeyError, RuntimeError, TypeError, ValueError, IndexError) as e:
            success = False
            error = str(e)
            self._fallbacks.record("benchmark_iteration_failed", e, level=logging.WARNING)
            self._log(f"Error during benchmark: {e}")

        # Calculate metrics
        end_time = time.time()
        total_time = end_time - start_time
        tokens_generated = len(token_latencies)

        tokens_per_second = tokens_generated / total_time if total_time > 0 else 0
        avg_token_latency = np.mean(token_latencies) if token_latencies else 0

        peak_vram = max(vram_samples) if vram_samples else 0
        avg_vram = np.mean(vram_samples) if vram_samples else 0

        avg_perplexity_proxy = np.mean(perplexities) if perplexities else 0
        coherence_proxy = self._calculate_coherence(generated)
        diversity = self._calculate_diversity(generated)

        # Strategy-specific metrics
        swap_count = getattr(meld_engine, 'swap_count', 0)
        # Estimate swap overhead (rough)
        swap_overhead = (swap_count * 5.0) if swap_count > 0 else 0  # ~5ms per swap estimate

        result = BenchmarkResult(
            config=config,
            generated_text=generated,
            total_time=total_time,
            tokens_per_second=tokens_per_second,
            avg_token_latency=avg_token_latency,
            peak_vram_mb=peak_vram,
            avg_vram_mb=avg_vram,
            avg_perplexity_proxy=avg_perplexity_proxy,
            coherence_proxy_score=coherence_proxy,
            diversity_score=diversity,
            swap_count=swap_count,
            swap_overhead_ms=swap_overhead,
            token_latencies=token_latencies,
            vram_samples=vram_samples,
            timestamp=time.time(),
            success=success,
            error=error,
            metric_contract=dict(QUALITY_METRIC_CONTRACT),
            reproducibility=self._collect_reproducibility_metadata(config, meld_engine),
        )

        self.results.append(result)
        return result

    def run_benchmark_suite(
        self,
        configs: List[BenchmarkConfig],
        engines_factory: Any  # Function that creates engines for each config
    ) -> List[BenchmarkResult]:
        """
        Run complete benchmark suite.

        Args:
            configs: List of benchmark configurations
            engines_factory: Function that creates engines: (config) -> MeldEngine

        Returns:
            List of benchmark results
        """
        results = []

        for config in configs:
            self._log(f"\n{'='*70}")
            self._log(f"Benchmark: {config.strategy_name}")
            self._log(f"{'='*70}")

            try:
                # Create engines for this config
                meld_engine = engines_factory(config)

                # Run benchmark
                result = self.run_single_benchmark(config, meld_engine)
                results.append(result)

                # Print summary
                self._print_result_summary(result)

            except (AttributeError, RuntimeError, TypeError, ValueError, OSError, ImportError) as e:
                self._fallbacks.record("benchmark_suite_config_failed", e, level=logging.WARNING)
                self._log(f"Failed to run benchmark {config.strategy_name}: {e}")

        return results

    def _print_result_summary(self, result: BenchmarkResult):
        """Print summary of benchmark result."""
        print(f"\n📊 Results:")
        print(f"  Total Time: {result.total_time:.2f}s")
        print(f"  Speed: {result.tokens_per_second:.2f} tokens/sec")
        print(f"  Avg Latency: {result.avg_token_latency*1000:.2f}ms/token")
        print(f"  Peak VRAM: {result.peak_vram_mb}MB")
        print(f"  Avg Perplexity Proxy: {result.avg_perplexity_proxy:.2f}")
        print(f"  Coherence Proxy: {result.coherence_proxy_score:.3f}")
        print(f"  Diversity: {result.diversity_score:.3f}")
        print(f"  Swaps: {result.swap_count}")

    def generate_report(
        self,
        output_path: str = "benchmark_report.html"
    ):
        """
        Generate HTML benchmark report.

        Args:
            output_path: Path to save HTML report
        """
        if not self.results:
            self._log("No results to report")
            return

        html = self._build_html_report()

        with open(output_path, 'w') as f:
            f.write(html)

        self._log(f"Report saved to: {output_path}")

    def _build_html_report(self) -> str:
        """Build HTML report from results."""
        # Sort by tokens/sec
        sorted_results = sorted(self.results, key=lambda r: r.tokens_per_second, reverse=True)

        html_parts = [
            "<!DOCTYPE html>",
            "<html><head><title>Mind Meld Benchmark Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #4CAF50; color: white; }",
            "tr:nth-child(even) { background-color: #f2f2f2; }",
            ".best { background-color: #d4edda !important; }",
            "</style>",
            "</head><body>",
            "<h1>Mind Meld Benchmark Report</h1>",
            f"<p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>",
            "<h2>Performance Comparison</h2>",
            "<table>",
            "<tr><th>Strategy</th><th>Speed (tok/s)</th><th>Latency (ms)</th><th>VRAM (MB)</th><th>Perplexity Proxy</th><th>Coherence Proxy</th><th>Swaps</th></tr>"
        ]

        for result in sorted_results:
            row_class = "best" if result == sorted_results[0] else ""
            html_parts.append(f"<tr class='{row_class}'>")
            html_parts.append(f"<td>{result.config.strategy_name}</td>")
            html_parts.append(f"<td>{result.tokens_per_second:.2f}</td>")
            html_parts.append(f"<td>{result.avg_token_latency*1000:.2f}</td>")
            html_parts.append(f"<td>{result.peak_vram_mb}</td>")
            html_parts.append(f"<td>{result.avg_perplexity_proxy:.2f}</td>")
            html_parts.append(f"<td>{result.coherence_proxy_score:.3f}</td>")
            html_parts.append(f"<td>{result.swap_count}</td>")
            html_parts.append("</tr>")

        html_parts.extend([
            "</table>",
            "</body></html>"
        ])

        return "\n".join(html_parts)

    def save_results_json(self, output_path: str = "benchmark_results.json"):
        """Save results to JSON file."""
        # Convert results to serializable format
        data = []
        for result in self.results:
            result_dict = {
                'config': asdict(result.config),
                'total_time': result.total_time,
                'tokens_per_second': result.tokens_per_second,
                'avg_token_latency': result.avg_token_latency,
                'peak_vram_mb': result.peak_vram_mb,
                'avg_vram_mb': result.avg_vram_mb,
                'avg_perplexity_proxy': result.avg_perplexity_proxy,
                'coherence_proxy_score': result.coherence_proxy_score,
                'diversity_score': result.diversity_score,
                'swap_count': result.swap_count,
                'swap_overhead_ms': result.swap_overhead_ms,
                'timestamp': result.timestamp,
                'success': result.success,
                'error': result.error,
                'metric_contract': result.metric_contract,
                'reproducibility': result.reproducibility,
                # Backward-compatible aliases
                'avg_perplexity': result.avg_perplexity_proxy,
                'coherence_score': result.coherence_proxy_score,
            }
            data.append(result_dict)

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        self._log(f"Results saved to: {output_path}")

    def _extract_kv_cache_metrics(self, meld_engine: MeldEngine) -> Dict[str, int]:
        """Extract KV cache diagnostics from meld engine."""
        diag = getattr(meld_engine, '_diag', {})
        return {
            'kv_cache_attempts': diag.get('kv_cache_attempts', 0),
            'kv_cache_successes': diag.get('kv_cache_success', 0),
            'kv_cache_replays': diag.get('kv_cache_replay', 0),
            'kv_cache_translations': diag.get('kv_cache_translated', 0),
            'guardrail_replays': diag.get('guardrail_replay', 0),
        }

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (Jaccard on words)."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union if union > 0 else 0.0

    def run_stability_benchmark(
        self,
        config: BenchmarkConfig,
        meld_engine_factory: Any,
        num_runs: int = 5
    ) -> StabilityResult:
        """
        Run multiple iterations to measure output stability.

        Args:
            config: Benchmark configuration
            meld_engine_factory: Function that creates fresh MeldEngine instances
            num_runs: Number of runs to perform

        Returns:
            StabilityResult with aggregated metrics
        """
        self._log(f"Running stability benchmark with {num_runs} runs")
        results = []

        for i in range(num_runs):
            self._log(f"  Run {i+1}/{num_runs}")
            try:
                meld_engine = meld_engine_factory(config)
                result = self.run_single_benchmark(config, meld_engine)

                # Extract KV cache metrics
                kv_metrics = self._extract_kv_cache_metrics(meld_engine)
                result.kv_cache_attempts = kv_metrics['kv_cache_attempts']
                result.kv_cache_successes = kv_metrics['kv_cache_successes']
                result.kv_cache_replays = kv_metrics['kv_cache_replays']
                result.kv_cache_translations = kv_metrics['kv_cache_translations']
                result.guardrail_replays = kv_metrics['guardrail_replays']

                results.append(result)
            except (AttributeError, RuntimeError, TypeError, ValueError, OSError, ImportError) as e:
                self._fallbacks.record("stability_run_failed", e, level=logging.WARNING)
                self._log(f"  Run {i+1} failed: {e}")

        if not results:
            raise RuntimeError("All stability benchmark runs failed")

        # Calculate output similarity matrix
        similarities = []
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                sim = self._calculate_text_similarity(
                    results[i].generated_text,
                    results[j].generated_text
                )
                similarities.append(sim)

        # Calculate exact match rate
        outputs = [r.generated_text for r in results]
        unique_outputs = len(set(outputs))
        exact_match_rate = 1.0 - (unique_outputs - 1) / max(len(outputs) - 1, 1)

        # Aggregate metrics
        speeds = [r.tokens_per_second for r in results]
        latencies = [r.avg_token_latency for r in results]

        kv_success_rates = [
            r.kv_cache_successes / max(r.kv_cache_attempts, 1)
            for r in results
        ]
        kv_replay_rates = [
            r.kv_cache_replays / max(r.kv_cache_attempts, 1)
            for r in results
        ]
        guardrail_rates = [
            r.guardrail_replays / max(r.swap_count, 1)
            for r in results
        ]

        return StabilityResult(
            config=config,
            num_runs=num_runs,
            output_similarity_mean=np.mean(similarities) if similarities else 1.0,
            output_similarity_std=np.std(similarities) if similarities else 0.0,
            exact_match_rate=exact_match_rate,
            speed_mean=np.mean(speeds),
            speed_std=np.std(speeds),
            latency_mean=np.mean(latencies),
            latency_std=np.std(latencies),
            kv_success_rate_mean=np.mean(kv_success_rates),
            kv_replay_rate_mean=np.mean(kv_replay_rates),
            guardrail_trigger_rate=np.mean(guardrail_rates),
            individual_results=results
        )

    def benchmark_kv_cache_strategies(
        self,
        models: List[str],
        prompt: str,
        max_tokens: int = 50,
        num_runs: int = 3
    ) -> Dict[str, StabilityResult]:
        """
        Compare KV cache handling strategies: direct, translation, replay.

        Args:
            models: Model specs to use
            prompt: Generation prompt
            max_tokens: Tokens to generate
            num_runs: Runs per strategy

        Returns:
            Dict mapping strategy name to StabilityResult
        """
        from src.mind_meld.core.config import MeldConfig, SwapConfig, SwapStrategy
        from src.engines.engine_factory import get_engine

        self._log("Benchmarking KV cache strategies")
        results = {}

        # Test configurations
        kv_configs = [
            ("kv_direct", False, False),      # No translation, no force
            ("kv_translate", True, False),    # Allow translation
            ("kv_force", True, True),         # Force translation
            ("kv_replay_only", False, False), # Will use replay via guardrails
        ]

        base_config = BenchmarkConfig(
            strategy_name="fixed_interval",
            models=models,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.7
        )

        for name, allow_translate, force_translate in kv_configs:
            self._log(f"\nTesting KV strategy: {name}")
            config = BenchmarkConfig(
                strategy_name=name,
                models=models,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.7
            )

            def create_engine(cfg, allow_t=allow_translate, force_t=force_translate):
                meld_config = MeldConfig(
                    swap_config=SwapConfig(strategy=SwapStrategy.FIXED_INTERVAL),
                    max_tokens=cfg.max_tokens,
                    temperature=cfg.temperature
                )

                engines = []
                for model_spec in cfg.models:
                    if ':' in model_spec:
                        engine_name, model_name = model_spec.split(':', 1)
                    else:
                        engine_name, model_name = 'pytorch', model_spec
                    engine = get_engine(engine_name, model_name, {"mode": "benchmark"})
                    engine.load()
                    engines.append(engine)

                class BenchArgs:
                    def __init__(self):
                        self.temperature = cfg.temperature
                        self.top_k = cfg.top_k
                        self.top_p = cfg.top_p
                        self.allow_kv_cache_translation = allow_t
                        self.force_kv_cache_translation = force_t
                        self.meld_diagnostics = True
                        self.verbose = False
                        self.summary_only = True

                return MeldEngine(engines, BenchArgs())

            try:
                stability = self.run_stability_benchmark(config, create_engine, num_runs)
                results[name] = stability
                self._print_stability_summary(name, stability)
            except (AttributeError, RuntimeError, TypeError, ValueError, OSError, ImportError) as e:
                self._fallbacks.record("kv_strategy_failed", e, level=logging.WARNING)
                self._log(f"Strategy {name} failed: {e}")

        return results

    def _print_stability_summary(self, name: str, result: StabilityResult):
        """Print stability benchmark summary."""
        print(f"\n📊 {name} Stability Results:")
        print(f"  Output similarity: {result.output_similarity_mean:.3f} ± {result.output_similarity_std:.3f}")
        print(f"  Exact match rate: {result.exact_match_rate:.1%}")
        print(f"  Speed: {result.speed_mean:.2f} ± {result.speed_std:.2f} tok/s")
        print(f"  KV success rate: {result.kv_success_rate_mean:.1%}")
        print(f"  KV replay rate: {result.kv_replay_rate_mean:.1%}")
        print(f"  Guardrail trigger rate: {result.guardrail_trigger_rate:.1%}")

    def compare_strategies(
        self,
        strategies: List[str],
        models: List[str],
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        seed: int = 42,
    ) -> List[BenchmarkResult]:
        """
        Compare multiple strategies on the same prompt.

        Args:
            strategies: List of strategy names (e.g., ['fixed_interval', 'confidence', 'perplexity'])
            models: List of model names to use
            prompt: Text prompt to generate from
            max_tokens: Max tokens to generate
            temperature: Sampling temperature

        Returns:
            List of benchmark results for each strategy
        """
        from src.mind_meld.core.config import MeldConfig, SwapConfig, SwapStrategy
        from src.engines.engine_factory import get_engine

        self._log(f"Comparing {len(strategies)} strategies")
        self._log(f"Models: {models}")
        self._log(f"Prompt: {prompt[:50]}...")

        configs = []
        for strategy_name in strategies:
            config = BenchmarkConfig(
                strategy_name=strategy_name,
                models=models,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                seed=int(seed),
            )
            configs.append(config)

        # Engine factory
        def create_meld_engine(config: BenchmarkConfig) -> MeldEngine:
            # Map strategy name to SwapStrategy enum
            strategy_map = {
                'fixed_interval': SwapStrategy.FIXED_INTERVAL,
                'pattern': SwapStrategy.PATTERN_BASED,
                'confidence': SwapStrategy.CONFIDENCE_BASED,
                'round_robin': SwapStrategy.ROUND_ROBIN,
                'random': SwapStrategy.RANDOM,
                'perplexity': SwapStrategy.PERPLEXITY_BASED,
                'semantic': SwapStrategy.SEMANTIC_SIMILARITY,
            }

            strategy = strategy_map.get(config.strategy_name, SwapStrategy.FIXED_INTERVAL)

            meld_config = MeldConfig(
                swap_config=SwapConfig(strategy=strategy),
                max_tokens=config.max_tokens,
                temperature=config.temperature
            )

            # Load models using engine factory
            engines = []
            for model_spec in config.models:
                try:
                    # Parse model spec in format "engine:model" or just "model" (defaults to pytorch)
                    if ':' in model_spec:
                        engine_name, model_name = model_spec.split(':', 1)
                    else:
                        engine_name, model_name = 'pytorch', model_spec

                    engine = get_engine(engine_name, model_name, {"mode": "benchmark"})
                    engine.load()
                    engines.append(engine)
                except (AttributeError, RuntimeError, TypeError, ValueError, OSError, ImportError) as e:
                    self._fallbacks.record("model_load_failed", e, level=logging.WARNING)
                    self._log(f"Failed to load model {model_spec}: {e}")
                    raise

            # Create meld engine
            class SimpleArgs:
                def __init__(self):
                    self.strategy = config.strategy_name
                    self.max_length = config.max_tokens
                    self.temperature = config.temperature
                    self.top_k = config.top_k
                    self.top_p = config.top_p

            meld = MeldEngine(engines, SimpleArgs())
            return meld

        # Run benchmarks
        results = self.run_benchmark_suite(configs, create_meld_engine)

        # Print comparison summary
        print("\n" + "=" * 80)
        print("Strategy Comparison Summary")
        print("=" * 80)
        print(f"{'Strategy':<20} {'Speed (t/s)':<15} {'Coherence*':<12} {'Swaps':<10}")
        print("-" * 80)

        for result in results:
            print(f"{result.config.strategy_name:<20} {result.tokens_per_second:<15.2f} "
                  f"{result.coherence_proxy_score:<12.3f} {result.swap_count:<10}")

        return results


# CLI Interface
def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Mind Meld Strategy Benchmark CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare three strategies
  python3 src/benchmarks/mind_meld_benchmark.py \\
    --strategies fixed_interval confidence perplexity \\
    --prompt "Once upon a time" \\
    --models gpt2 gpt2-medium \\
    --output comparison.html

  # Quick test
  python3 src/benchmarks/mind_meld_benchmark.py \\
    --strategies confidence \\
    --prompt "Hello world" \\
    --max-tokens 50

Available strategies:
  - fixed_interval: Swap every N tokens
  - pattern: Swap at punctuation
  - confidence: Swap when confidence drops
  - round_robin: Rotate through models
  - random: Random swaps
  - perplexity: Swap based on perplexity
  - semantic: Swap based on semantic similarity
        """
    )

    parser.add_argument(
        '--strategies',
        nargs='+',
        required=True,
        help='Strategy names to compare (e.g., fixed_interval confidence perplexity)'
    )

    parser.add_argument(
        '--prompt',
        type=str,
        default='Once upon a time in a land far away',
        help='Text prompt to generate from'
    )

    parser.add_argument(
        '--models',
        nargs='+',
        default=['gpt2', 'gpt2-medium'],
        help='Model names to use (default: gpt2 gpt2-medium)'
    )

    parser.add_argument(
        '--max-tokens',
        type=int,
        default=100,
        help='Maximum tokens to generate (default: 100)'
    )

    parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help='Sampling temperature (default: 0.7)'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed used for benchmark-side reproducibility metadata (default: 42)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='benchmark_report.html',
        help='Output HTML report path (default: benchmark_report.html)'
    )

    parser.add_argument(
        '--json',
        type=str,
        help='Also save results as JSON to this path'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress verbose output'
    )

    args = parser.parse_args()

    # Create benchmark
    benchmark = MindMeldBenchmark(verbose=not args.quiet)

    print("=" * 80)
    print("Mind Meld Strategy Benchmark")
    print("=" * 80)
    print(f"Strategies: {', '.join(args.strategies)}")
    print(f"Models: {', '.join(args.models)}")
    print(f"Prompt: {args.prompt[:50]}...")
    print(f"Max tokens: {args.max_tokens}")
    print(f"Seed: {args.seed}")
    print("=" * 80)

    # Run comparison
    try:
        results = benchmark.compare_strategies(
            strategies=args.strategies,
            models=args.models,
            prompt=args.prompt,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            seed=int(args.seed),
        )

        # Generate reports
        print(f"\nGenerating HTML report: {args.output}")
        benchmark.generate_report(args.output)

        if args.json:
            print(f"Saving JSON results: {args.json}")
            benchmark.save_results_json(args.json)

        print("\n✅ Benchmark complete!")

    except (AttributeError, RuntimeError, TypeError, ValueError, OSError, ImportError) as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
