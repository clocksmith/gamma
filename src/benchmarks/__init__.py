"""
GAMMA Benchmarks Module

Contains various benchmarking tools:
- mind_meld_benchmark: Performance testing for Mind Meld multi-model collaboration
- language_comparison: TypeScript vs JavaScript LLM code generation comparison (from DREAM)
"""

from .mind_meld_benchmark import MindMeldBenchmark, BenchmarkConfig, BenchmarkResult

__all__ = ['MindMeldBenchmark', 'BenchmarkConfig', 'BenchmarkResult']
