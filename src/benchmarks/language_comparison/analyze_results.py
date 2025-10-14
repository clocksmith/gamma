#!/usr/bin/env python3
"""
Benchmark Results Analyzer
Analyzes and visualizes LLM benchmark results with detailed metrics.
Refactored to use pandas for data processing and matplotlib/seaborn for visualization.
"""

import json
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict

class BenchmarkAnalyzer:
    def __init__(self, results_file: str):
        self.results_file = Path(results_file)
        if not self.results_file.exists():
            print(f"Error: Results file not found at {self.results_file}")
            sys.exit(1)
        self.df = self._load_and_process_results()

    def _load_and_process_results(self) -> pd.DataFrame:
        """Load results and process them into a pandas DataFrame."""
        with open(self.results_file) as f:
            data = json.load(f)

        # Normalize the nested JSON structure into a flat list of dicts
        processed_records = []
        for record in data:
            if not record.get('success'):
                continue
            
            flat_record = {
                'provider': record.get('provider'),
                'variant': record.get('variant'),
                'task': record.get('taskName'),
                'category': record.get('category'),
                'duration_ms': record.get('duration'),
                'score': record.get('evaluation', {}).get('totalScore'),
                'accuracy': record.get('evaluation', {}).get('scores', {}).get('accuracy'),
                'code_quality': record.get('evaluation', {}).get('scores', {}).get('codeQuality'),
            }
            processed_records.append(flat_record)
        
        return pd.DataFrame(processed_records)

    def print_summary(self):
        """Print a summary of the results to the console."""
        if self.df.empty:
            print("No successful results to analyze.")
            return

        print("\n" + "="*80)
        print(f"BENCHMARK RESULTS ANALYSIS: {self.results_file.name}")
        print("="*80 + "\n")

        print("📊 Provider Performance (Mean Score):")
        provider_summary = self.df.groupby('provider')['score'].agg(['mean', 'std', 'count']).sort_values(by='mean', ascending=False)
        print(provider_summary)
        print("\n")

        print("📝 Variant Performance (Mean Score):")
        variant_summary = self.df.groupby('variant')['score'].agg(['mean', 'std', 'count']).sort_values(by='mean', ascending=False)
        print(variant_summary)
        print("\n")

    def visualize_results(self, reports_dir: str):
        """Generate and save visualizations of the results."""
        if self.df.empty:
            print("No data to visualize.")
            return

        reports_path = Path(reports_dir)
        reports_path.mkdir(exist_ok=True)

        sns.set_theme(style="whitegrid")

        # --- Provider Score Comparison ---
        plt.figure(figsize=(10, 6))
        provider_plot = sns.barplot(data=self.df, x='provider', y='score', palette='viridis')
        provider_plot.set_title('Benchmark Score by Provider', fontsize=16)
        provider_plot.set_xlabel('Provider', fontsize=12)
        provider_plot.set_ylabel('Mean Score', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        provider_fig_path = reports_path / 'provider_score_comparison.png'
        plt.savefig(provider_fig_path)
        print(f"✓ Saved provider comparison chart to {provider_fig_path}")
        plt.close()

        # --- Variant Score Comparison ---
        plt.figure(figsize=(10, 6))
        variant_plot = sns.barplot(data=self.df, x='variant', y='score', palette='plasma')
        variant_plot.set_title('Benchmark Score by Language Variant', fontsize=16)
        variant_plot.set_xlabel('Variant', fontsize=12)
        variant_plot.set_ylabel('Mean Score', fontsize=12)
        plt.tight_layout()
        variant_fig_path = reports_path / 'variant_score_comparison.png'
        plt.savefig(variant_fig_path)
        print(f"✓ Saved variant comparison chart to {variant_fig_path}")
        plt.close()

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python analyze_results.py <results-file.json> [--visualize] [--reports-dir <path>]")
        sys.exit(1)

    results_file = args[0]
    do_visualize = '--visualize' in args
    
    reports_dir = 'benchmark/reports' # Default
    if '--reports-dir' in args:
        try:
            reports_dir_index = args.index('--reports-dir') + 1
            reports_dir = args[reports_dir_index]
        except (ValueError, IndexError):
            print("Error: --reports-dir flag must be followed by a path.")
            sys.exit(1)

    # Handle wildcard for latest file
    if '*' in results_file:
        results_path = Path(results_file)
        results_dir_glob = results_path.parent
        pattern = results_path.name
        matching_files = sorted(results_dir_glob.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        if not matching_files:
            print(f"Error: No files found matching {results_file}")
            sys.exit(1)
        results_file = matching_files[0]
        print(f"Analyzing most recent results file: {results_file}\n")

    analyzer = BenchmarkAnalyzer(results_file)
    analyzer.print_summary()

    if do_visualize:
        analyzer.visualize_results(reports_dir)

if __name__ == '__main__':
    main()