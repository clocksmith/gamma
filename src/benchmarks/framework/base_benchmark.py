"""
Base benchmark framework for GAMMA.

Provides standardized infrastructure for benchmarking LLM engines with
reproducible results, common metrics, and result storage.
"""
import time
import json
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class BenchmarkConfig:
    """Configuration for a benchmark run."""
    name: str
    description: str
    seed: int = 42
    temperature: float = 0.7
    top_k: int = 50
    top_p: float = 0.9
    max_tokens: int = 100
    num_iterations: int = 1
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def get_hash(self) -> str:
        """Get unique hash for this configuration."""
        config_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()[:8]


@dataclass
class BenchmarkResult:
    """Result from a single benchmark run."""
    config_hash: str
    timestamp: str
    engine_name: str
    model_name: str
    metrics: Dict[str, float]
    outputs: List[str] = None
    errors: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.outputs is None:
            self.outputs = []
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class BaseBenchmark(ABC):
    """
    Base class for all benchmarks.

    Provides:
    - Reproducible runs with seed management
    - Common metrics (speed, memory, accuracy)
    - Result storage and comparison
    - Progress tracking
    """

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.results: List[BenchmarkResult] = []

    @abstractmethod
    def run_single_iteration(
        self,
        engine: Any,
        iteration: int
    ) -> Dict[str, Any]:
        """
        Run a single benchmark iteration.

        Args:
            engine: Engine instance to benchmark
            iteration: Iteration number (0-indexed)

        Returns:
            Dictionary with metrics and outputs for this iteration
        """
        pass

    def run(self, engine: Any) -> BenchmarkResult:
        """
        Run the complete benchmark.

        Args:
            engine: Engine instance to benchmark

        Returns:
            BenchmarkResult with aggregated metrics
        """
        print(f"\n{'='*60}")
        print(f"Benchmark: {self.config.name}")
        print(f"Description: {self.config.description}")
        print(f"Engine: {engine.__class__.__name__}")
        print(f"Model: {engine.model_name if hasattr(engine, 'model_name') else 'unknown'}")
        print(f"Iterations: {self.config.num_iterations}")
        print(f"{'='*60}\n")

        all_metrics = []
        all_outputs = []
        all_errors = []

        start_time = time.time()

        for i in range(self.config.num_iterations):
            print(f"Iteration {i+1}/{self.config.num_iterations}...")

            try:
                iteration_result = self.run_single_iteration(engine, i)
                all_metrics.append(iteration_result.get("metrics", {}))
                all_outputs.extend(iteration_result.get("outputs", []))

            except Exception as e:
                error_msg = f"Iteration {i+1} failed: {str(e)}"
                print(f"  ERROR: {error_msg}")
                all_errors.append(error_msg)

        total_time = time.time() - start_time

        # Aggregate metrics
        aggregated_metrics = self._aggregate_metrics(all_metrics)
        aggregated_metrics["total_time_seconds"] = round(total_time, 2)
        aggregated_metrics["avg_time_per_iteration"] = round(
            total_time / self.config.num_iterations, 2
        )

        # Create result
        result = BenchmarkResult(
            config_hash=self.config.get_hash(),
            timestamp=datetime.now().isoformat(),
            engine_name=engine.__class__.__name__,
            model_name=engine.model_name if hasattr(engine, 'model_name') else 'unknown',
            metrics=aggregated_metrics,
            outputs=all_outputs[:10],  # Keep first 10 outputs as samples
            errors=all_errors,
            metadata={
                "config": self.config.to_dict(),
                "success_rate": (self.config.num_iterations - len(all_errors)) / self.config.num_iterations
            }
        )

        self.results.append(result)

        print(f"\n{'='*60}")
        print(f"Benchmark Complete!")
        print(f"Success Rate: {result.metadata['success_rate']*100:.1f}%")
        print(f"Total Time: {aggregated_metrics['total_time_seconds']}s")
        self._print_key_metrics(aggregated_metrics)
        print(f"{'='*60}\n")

        return result

    def _aggregate_metrics(self, metrics_list: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Aggregate metrics across iterations.

        Computes mean, std, min, max for numeric metrics.
        """
        if not metrics_list:
            return {}

        aggregated = {}
        all_keys = set()
        for m in metrics_list:
            all_keys.update(m.keys())

        for key in all_keys:
            values = [m.get(key, 0) for m in metrics_list if key in m]
            if values:
                aggregated[f"{key}_mean"] = round(sum(values) / len(values), 3)
                if len(values) > 1:
                    mean = aggregated[f"{key}_mean"]
                    variance = sum((x - mean) ** 2 for x in values) / len(values)
                    aggregated[f"{key}_std"] = round(variance ** 0.5, 3)
                aggregated[f"{key}_min"] = round(min(values), 3)
                aggregated[f"{key}_max"] = round(max(values), 3)

        return aggregated

    def _print_key_metrics(self, metrics: Dict[str, float]):
        """Print important metrics."""
        key_metrics = [
            "tokens_per_second_mean",
            "latency_ms_mean",
            "accuracy_mean",
            "perplexity_mean"
        ]

        print("\nKey Metrics:")
        for metric in key_metrics:
            if metric in metrics:
                print(f"  {metric}: {metrics[metric]}")

    def save_results(self, output_dir: str = "./output/benchmarks"):
        """
        Save benchmark results to JSON file.

        Args:
            output_dir: Directory to save results
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_{self.config.name}_{timestamp}.json"
        filepath = output_path / filename

        results_data = {
            "config": self.config.to_dict(),
            "results": [r.to_dict() for r in self.results]
        }

        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2)

        print(f"Results saved to: {filepath}")

    def compare_with(self, other_result: BenchmarkResult) -> Dict[str, Any]:
        """
        Compare this benchmark with another result.

        Args:
            other_result: Another BenchmarkResult to compare with

        Returns:
            Dictionary with comparison metrics
        """
        if not self.results:
            return {"error": "No results to compare"}

        my_result = self.results[-1]  # Latest result
        comparison = {
            "engine_a": my_result.engine_name,
            "engine_b": other_result.engine_name,
            "model_a": my_result.model_name,
            "model_b": other_result.model_name,
            "metrics": {}
        }

        # Compare common metrics
        for key in my_result.metrics:
            if key in other_result.metrics:
                a_val = my_result.metrics[key]
                b_val = other_result.metrics[key]

                if b_val != 0:
                    percent_diff = ((a_val - b_val) / b_val) * 100
                    comparison["metrics"][key] = {
                        "a": a_val,
                        "b": b_val,
                        "difference": round(a_val - b_val, 3),
                        "percent_diff": round(percent_diff, 2),
                        "winner": "a" if a_val > b_val else "b"
                    }

        return comparison


class SpeedBenchmark(BaseBenchmark):
    """Benchmark for measuring generation speed (tokens/sec)."""

    def __init__(self, config: BenchmarkConfig, prompts: List[str]):
        super().__init__(config)
        self.prompts = prompts

    def run_single_iteration(self, engine: Any, iteration: int) -> Dict[str, Any]:
        """Run speed benchmark iteration."""
        prompt = self.prompts[iteration % len(self.prompts)]

        # Encode prompt
        input_ids, attention_mask = engine.encode(prompt)

        start_time = time.time()
        tokens_generated = 0

        # Generate tokens
        for _ in range(self.config.max_tokens):
            output = engine.predict_next(
                input_ids,
                attention_mask,
                temperature=self.config.temperature,
                top_k=self.config.top_k,
                top_p=self.config.top_p
            )

            tokens_generated += 1

            # Stop at EOS (if engine supports it)
            if hasattr(engine, 'tokenizer') and hasattr(engine.tokenizer, 'eos_token_id'):
                if output["next_token_id"] == engine.tokenizer.eos_token_id:
                    break

        total_time = time.time() - start_time
        tokens_per_second = tokens_generated / total_time if total_time > 0 else 0

        return {
            "metrics": {
                "tokens_generated": tokens_generated,
                "total_time": total_time,
                "tokens_per_second": tokens_per_second,
                "latency_ms": (total_time / tokens_generated * 1000) if tokens_generated > 0 else 0
            },
            "outputs": [f"Generated {tokens_generated} tokens in {total_time:.2f}s"]
        }
