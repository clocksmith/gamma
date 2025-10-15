"""
GAMMA Benchmarks Module

Contains various benchmarking tools:
- mind_meld_benchmark: Performance testing for Mind Meld multi-model collaboration
- dream: DREAM benchmarking suite for TypeScript vs JavaScript LLM code generation
"""

from .mind_meld_benchmark import MindMeldBenchmark, BenchmarkConfig, BenchmarkResult

__all__ = ['MindMeldBenchmark', 'BenchmarkConfig', 'BenchmarkResult']
