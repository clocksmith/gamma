#!/usr/bin/env python3
"""
Comprehensive Benchmark Results Analyzer
Analyzes and visualizes LLM benchmark results with advanced statistical metrics including:
- KL divergence and Jensen-Shannon distance
- Statistical significance tests (t-tests, Cohen's d)
- Distribution analysis and visualizations
- Performance metrics and token efficiency
"""

import json
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict, Tuple
from scipy import stats
from scipy.spatial import distance
from scipy.special import rel_entr

class BenchmarkAnalyzer:
    def __init__(self, results_file: str):
        self.results_file = Path(results_file)
        if not self.results_file.exists():
            print(f"Error: Results file not found at {self.results_file}")
            sys.exit(1)
        self.raw_data = None  # Store raw JSON for code variation analysis
        self.df = self._load_and_process_results()

    def _load_and_process_results(self) -> pd.DataFrame:
        """Load results and process them into a pandas DataFrame."""
        with open(self.results_file) as f:
            data = json.load(f)

        self.raw_data = data  # Store for code variation analysis

        processed_records = []
        for record in data:
            if not record.get('success'):
                continue

            # New structure: benchmarks at top level
            benchmarks = record.get('benchmarks', {})
            code_size = benchmarks.get('codeSizeMetrics', {})
            complexity = benchmarks.get('complexity', {})
            auto_rater = benchmarks.get('autoRater', {})
            completeness = benchmarks.get('completeness', {})
            ref_comparison = benchmarks.get('referenceComparison', {})

            # Calculate runtime performance average if available
            runtime_perf = benchmarks.get('runtimePerformance')
            avg_runtime_ms = 0
            if runtime_perf and isinstance(runtime_perf, list) and len(runtime_perf) > 0:
                # Filter out None values and calculate mean
                valid_times = [p.get('meanTimeMs', 0) for p in runtime_perf if p.get('meanTimeMs') is not None]
                if valid_times:
                    avg_runtime_ms = np.mean(valid_times)

            # Calculate aggregate score from available metrics
            accuracy_score = benchmarks.get('accuracyScore', 0)
            auto_rater_score = auto_rater.get('score', 0) if isinstance(auto_rater, dict) else 0
            completeness_score = completeness.get('score', 0) if isinstance(completeness, dict) else 0

            # Weighted total score: accuracy (50%), auto-rater (30%), completeness (20%)
            total_score = (accuracy_score * 0.5) + (auto_rater_score * 0.3) + (completeness_score * 0.2)

            flat_record = {
                'provider': record.get('provider'),
                'variant': record.get('variant'),
                'task': record.get('taskName'),
                'category': record.get('category'),
                'run': record.get('run', 1),
                'duration_ms': record.get('duration'),
                'score': total_score,
                'accuracy': accuracy_score,
                'performance': 1.0 - min(avg_runtime_ms / 1000.0, 1.0) if avg_runtime_ms > 0 else 0.5,  # Normalize runtime to 0-1
                'code_quality': auto_rater_score,
                'completeness': completeness_score,
                # Advanced LLM metrics
                'f1_score': np.nan,  # Not currently calculated
                'precision': np.nan,  # Not currently calculated
                'recall': np.nan,  # Not currently calculated
                'edit_similarity': ref_comparison.get('editSimilarity', np.nan),
                'ast_similarity': ref_comparison.get('astSimilarity', np.nan),
                # Token metrics
                'input_tokens': code_size.get('inputTokens', 0),
                'output_tokens': code_size.get('outputTokens', 0),
                'total_tokens': code_size.get('tokensUsed', 0),
                'tokens_per_sec': 0,  # Not currently calculated
                # Code metrics
                'code_lines': code_size.get('codeLines', 0),
                'total_lines': code_size.get('totalLines', 0),
                'comment_lines': code_size.get('commentLines', 0),
                # Complexity metrics
                'cyclomatic_complexity': complexity.get('cyclomaticComplexity', np.nan),
                'halstead_difficulty': complexity.get('halsteadDifficulty', np.nan),
                'halstead_volume': complexity.get('halsteadVolume', np.nan),
                'halstead_effort': complexity.get('halsteadEffort', np.nan),
                'maintainability_index': complexity.get('maintainabilityIndex', np.nan),
                'max_nesting_depth': complexity.get('maxNestingDepth', np.nan),
                # Runtime performance
                'avg_runtime_ms': avg_runtime_ms,
            }
            processed_records.append(flat_record)

        return pd.DataFrame(processed_records)

    def calculate_kl_divergence(self, dist1: np.ndarray, dist2: np.ndarray, bins: int = 20) -> float:
        """Calculate KL divergence between two distributions."""
        # Create histograms
        hist1, bin_edges = np.histogram(dist1, bins=bins, density=True)
        hist2, _ = np.histogram(dist2, bins=bin_edges, density=True)

        # Add small epsilon to avoid division by zero
        epsilon = 1e-10
        hist1 = hist1 + epsilon
        hist2 = hist2 + epsilon

        # Normalize
        hist1 = hist1 / hist1.sum()
        hist2 = hist2 / hist2.sum()

        # Calculate KL divergence
        kl_div = np.sum(rel_entr(hist1, hist2))
        return kl_div

    def calculate_js_distance(self, dist1: np.ndarray, dist2: np.ndarray, bins: int = 20) -> float:
        """Calculate Jensen-Shannon distance (symmetric version of KL divergence)."""
        hist1, bin_edges = np.histogram(dist1, bins=bins, density=True)
        hist2, _ = np.histogram(dist2, bins=bin_edges, density=True)

        epsilon = 1e-10
        hist1 = hist1 + epsilon
        hist2 = hist2 + epsilon
        hist1 = hist1 / hist1.sum()
        hist2 = hist2 / hist2.sum()

        return distance.jensenshannon(hist1, hist2)

    def cohens_d(self, group1: np.ndarray, group2: np.ndarray) -> float:
        """Calculate Cohen's d effect size."""
        n1, n2 = len(group1), len(group2)
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
        pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
        return (np.mean(group1) - np.mean(group2)) / pooled_std if pooled_std > 0 else 0

    def print_summary(self):
        """Print comprehensive statistical summary."""
        if self.df.empty:
            print("No successful results to analyze.")
            return

        print("\n" + "="*80)
        print(f"COMPREHENSIVE BENCHMARK ANALYSIS: {self.results_file.name}")
        print("="*80 + "\n")

        print("📊 Overall Statistics:")
        print(f"Total runs: {len(self.df)}")
        print(f"Mean score: {self.df['score'].mean():.2f} (±{self.df['score'].std():.2f})")
        print(f"Mean duration: {self.df['duration_ms'].mean():.0f}ms (±{self.df['duration_ms'].std():.0f}ms)")
        print(f"Mean tokens: {self.df['total_tokens'].mean():.0f} (±{self.df['total_tokens'].std():.0f})")
        print()

        print("📊 Provider Performance:")
        provider_stats = self.df.groupby('provider').agg({
            'score': ['mean', 'std', 'count'],
            'duration_ms': 'mean',
            'total_tokens': 'mean'
        }).round(2)
        print(provider_stats)
        print()

        print("📝 Variant Performance:")
        variant_stats = self.df.groupby('variant').agg({
            'score': ['mean', 'std', 'count'],
            'duration_ms': 'mean',
            'code_lines': 'mean'
        }).round(2)
        print(variant_stats)
        print()

        # Statistical comparisons between variants
        variants = self.df['variant'].unique()
        if len(variants) >= 2:
            print("📈 Statistical Comparisons (Variant Pairs):")
            for i, var1 in enumerate(variants):
                for var2 in variants[i+1:]:
                    scores1 = self.df[self.df['variant'] == var1]['score'].values
                    scores2 = self.df[self.df['variant'] == var2]['score'].values

                    if len(scores1) > 0 and len(scores2) > 0:
                        t_stat, p_value = stats.ttest_ind(scores1, scores2)
                        cohen_d = self.cohens_d(scores1, scores2)
                        js_dist = self.calculate_js_distance(scores1, scores2)

                        print(f"\n{var1} vs {var2}:")
                        print(f"  t-statistic: {t_stat:.3f}, p-value: {p_value:.4f}")
                        print(f"  Cohen's d: {cohen_d:.3f} ({'small' if abs(cohen_d) < 0.5 else 'medium' if abs(cohen_d) < 0.8 else 'large'} effect)")
                        print(f"  Jensen-Shannon distance: {js_dist:.4f}")
            print()

    def visualize_results(self, reports_dir: str):
        """Generate comprehensive visualizations."""
        if self.df.empty:
            print("No data to visualize.")
            return

        viz_path = Path(reports_dir) / 'visualizations'
        viz_path.mkdir(parents=True, exist_ok=True)

        sns.set_theme(style="whitegrid", palette="husl")

        print(f"\n📊 Generating visualizations in {viz_path}/")

        self._plot_score_distributions(viz_path)
        self._plot_kl_divergence_heatmap(viz_path)
        self._plot_performance_comparison(viz_path)
        self._plot_statistical_tests(viz_path)
        self._plot_token_efficiency(viz_path)
        self._plot_code_metrics(viz_path)
        self._plot_comprehensive_heatmap(viz_path)
        self._plot_f1_precision_recall(viz_path)
        self._plot_complexity_metrics(viz_path)
        self._plot_pass_at_k(viz_path)
        self._plot_code_variation(viz_path)

        print(f"\n✓ All visualizations saved to {viz_path}/")

    def _plot_score_distributions(self, output_dir: Path):
        """Plot score distributions with violin, box, and histogram plots."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Violin plot by provider
        sns.violinplot(data=self.df, x='provider', y='score', ax=axes[0, 0])
        axes[0, 0].set_title('Score Distribution by Provider', fontsize=14, weight='bold')
        axes[0, 0].set_xticklabels(axes[0, 0].get_xticklabels(), rotation=45, ha='right')

        # Violin plot by variant
        sns.violinplot(data=self.df, x='variant', y='score', ax=axes[0, 1])
        axes[0, 1].set_title('Score Distribution by Variant', fontsize=14, weight='bold')
        axes[0, 1].set_xticklabels(axes[0, 1].get_xticklabels(), rotation=45, ha='right')

        # Box plot comparison
        sns.boxplot(data=self.df, x='variant', y='score', ax=axes[1, 0])
        axes[1, 0].set_title('Score Box Plot by Variant', fontsize=14, weight='bold')
        axes[1, 0].set_xticklabels(axes[1, 0].get_xticklabels(), rotation=45, ha='right')

        # Histogram
        for variant in self.df['variant'].unique():
            data = self.df[self.df['variant'] == variant]['score']
            axes[1, 1].hist(data, alpha=0.5, label=variant, bins=15)
        axes[1, 1].set_title('Score Histogram by Variant', fontsize=14, weight='bold')
        axes[1, 1].set_xlabel('Score')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].legend()

        plt.tight_layout()
        plt.savefig(output_dir / 'score_distributions.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✓ score_distributions.png")

    def _plot_kl_divergence_heatmap(self, output_dir: Path):
        """Plot KL divergence and JS distance heatmaps between variants."""
        variants = sorted(self.df['variant'].unique())
        n = len(variants)

        if n < 2:
            return

        kl_matrix = np.zeros((n, n))
        js_matrix = np.zeros((n, n))

        for i, var1 in enumerate(variants):
            for j, var2 in enumerate(variants):
                scores1 = self.df[self.df['variant'] == var1]['score'].values
                scores2 = self.df[self.df['variant'] == var2]['score'].values

                if len(scores1) > 0 and len(scores2) > 0:
                    kl_matrix[i, j] = self.calculate_kl_divergence(scores1, scores2)
                    js_matrix[i, j] = self.calculate_js_distance(scores1, scores2)

        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        # KL Divergence heatmap
        sns.heatmap(kl_matrix, xticklabels=variants, yticklabels=variants,
                   annot=True, fmt='.3f', cmap='YlOrRd', ax=axes[0], cbar_kws={'label': 'KL Divergence'})
        axes[0].set_title('KL Divergence Between Variants', fontsize=14, weight='bold')

        # Jensen-Shannon Distance heatmap
        sns.heatmap(js_matrix, xticklabels=variants, yticklabels=variants,
                   annot=True, fmt='.4f', cmap='viridis', ax=axes[1], cbar_kws={'label': 'JS Distance'})
        axes[1].set_title('Jensen-Shannon Distance Between Variants', fontsize=14, weight='bold')

        plt.tight_layout()
        plt.savefig(output_dir / 'kl_divergence_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✓ kl_divergence_heatmap.png")

    def _plot_performance_comparison(self, output_dir: Path):
        """Plot performance metrics: duration and token usage."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Duration by variant
        sns.barplot(data=self.df, x='variant', y='duration_ms', ax=axes[0, 0], errorbar='sd')
        axes[0, 0].set_title('Mean Duration by Variant', fontsize=14, weight='bold')
        axes[0, 0].set_ylabel('Duration (ms)')
        axes[0, 0].set_xticklabels(axes[0, 0].get_xticklabels(), rotation=45, ha='right')

        # Duration by provider
        sns.barplot(data=self.df, x='provider', y='duration_ms', ax=axes[0, 1], errorbar='sd')
        axes[0, 1].set_title('Mean Duration by Provider', fontsize=14, weight='bold')
        axes[0, 1].set_ylabel('Duration (ms)')
        axes[0, 1].set_xticklabels(axes[0, 1].get_xticklabels(), rotation=45, ha='right')

        # Token usage by variant
        sns.barplot(data=self.df, x='variant', y='total_tokens', ax=axes[1, 0], errorbar='sd')
        axes[1, 0].set_title('Mean Token Usage by Variant', fontsize=14, weight='bold')
        axes[1, 0].set_ylabel('Total Tokens')
        axes[1, 0].set_xticklabels(axes[1, 0].get_xticklabels(), rotation=45, ha='right')

        # Tokens per second
        sns.barplot(data=self.df, x='provider', y='tokens_per_sec', ax=axes[1, 1], errorbar='sd')
        axes[1, 1].set_title('Tokens per Second by Provider', fontsize=14, weight='bold')
        axes[1, 1].set_ylabel('Tokens/sec')
        axes[1, 1].set_xticklabels(axes[1, 1].get_xticklabels(), rotation=45, ha='right')

        plt.tight_layout()
        plt.savefig(output_dir / 'performance_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✓ performance_comparison.png")

    def _plot_statistical_tests(self, output_dir: Path):
        """Plot statistical test results (t-tests, Cohen's d)."""
        variants = sorted(self.df['variant'].unique())
        if len(variants) < 2:
            return

        comparisons = []
        t_stats = []
        p_values = []
        cohens_ds = []

        for i, var1 in enumerate(variants):
            for var2 in variants[i+1:]:
                scores1 = self.df[self.df['variant'] == var1]['score'].values
                scores2 = self.df[self.df['variant'] == var2]['score'].values

                if len(scores1) > 0 and len(scores2) > 0:
                    t_stat, p_value = stats.ttest_ind(scores1, scores2)
                    cohen_d = self.cohens_d(scores1, scores2)

                    comparisons.append(f"{var1}\nvs\n{var2}")
                    t_stats.append(t_stat)
                    p_values.append(p_value)
                    cohens_ds.append(abs(cohen_d))

        if not comparisons:
            return

        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        # P-values
        axes[0].bar(range(len(comparisons)), p_values, color=['green' if p < 0.05 else 'red' for p in p_values])
        axes[0].axhline(y=0.05, color='black', linestyle='--', label='p=0.05')
        axes[0].set_xticks(range(len(comparisons)))
        axes[0].set_xticklabels(comparisons, rotation=0, fontsize=8)
        axes[0].set_ylabel('P-value')
        axes[0].set_title('Statistical Significance (t-test p-values)', fontsize=14, weight='bold')
        axes[0].legend()

        # Cohen's d
        colors = ['green' if d > 0.8 else 'yellow' if d > 0.5 else 'orange' for d in cohens_ds]
        axes[1].bar(range(len(comparisons)), cohens_ds, color=colors)
        axes[1].axhline(y=0.5, color='gray', linestyle='--', label='Medium effect')
        axes[1].axhline(y=0.8, color='black', linestyle='--', label='Large effect')
        axes[1].set_xticks(range(len(comparisons)))
        axes[1].set_xticklabels(comparisons, rotation=0, fontsize=8)
        axes[1].set_ylabel("Cohen's d (effect size)")
        axes[1].set_title("Effect Sizes (Cohen's d)", fontsize=14, weight='bold')
        axes[1].legend()

        plt.tight_layout()
        plt.savefig(output_dir / 'statistical_tests.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✓ statistical_tests.png")

    def _plot_token_efficiency(self, output_dir: Path):
        """Plot token efficiency metrics."""
        # Calculate score per token
        self.df['score_per_token'] = self.df['score'] / (self.df['total_tokens'] + 1)
        self.df['score_per_line'] = self.df['score'] / (self.df['code_lines'] + 1)

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Score vs tokens scatter
        for variant in self.df['variant'].unique():
            data = self.df[self.df['variant'] == variant]
            axes[0, 0].scatter(data['total_tokens'], data['score'], label=variant, alpha=0.6, s=100)
        axes[0, 0].set_xlabel('Total Tokens')
        axes[0, 0].set_ylabel('Score')
        axes[0, 0].set_title('Score vs Token Usage', fontsize=14, weight='bold')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # Score per token by variant
        sns.barplot(data=self.df, x='variant', y='score_per_token', ax=axes[0, 1], errorbar='sd')
        axes[0, 1].set_title('Token Efficiency by Variant', fontsize=14, weight='bold')
        axes[0, 1].set_ylabel('Score per Token')
        axes[0, 1].set_xticklabels(axes[0, 1].get_xticklabels(), rotation=45, ha='right')

        # Score vs duration
        for variant in self.df['variant'].unique():
            data = self.df[self.df['variant'] == variant]
            axes[1, 0].scatter(data['duration_ms'], data['score'], label=variant, alpha=0.6, s=100)
        axes[1, 0].set_xlabel('Duration (ms)')
        axes[1, 0].set_ylabel('Score')
        axes[1, 0].set_title('Score vs Duration', fontsize=14, weight='bold')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # Score per code line
        sns.barplot(data=self.df, x='variant', y='score_per_line', ax=axes[1, 1], errorbar='sd')
        axes[1, 1].set_title('Score per Code Line', fontsize=14, weight='bold')
        axes[1, 1].set_ylabel('Score per Line')
        axes[1, 1].set_xticklabels(axes[1, 1].get_xticklabels(), rotation=45, ha='right')

        plt.tight_layout()
        plt.savefig(output_dir / 'token_efficiency.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✓ token_efficiency.png")

    def _plot_code_metrics(self, output_dir: Path):
        """Plot code metrics analysis."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Code lines by variant
        sns.barplot(data=self.df, x='variant', y='code_lines', ax=axes[0, 0], errorbar='sd')
        axes[0, 0].set_title('Mean Code Lines by Variant', fontsize=14, weight='bold')
        axes[0, 0].set_ylabel('Code Lines')
        axes[0, 0].set_xticklabels(axes[0, 0].get_xticklabels(), rotation=45, ha='right')

        # Comment ratio
        self.df['comment_ratio'] = self.df['comment_lines'] / (self.df['total_lines'] + 1)
        sns.barplot(data=self.df, x='variant', y='comment_ratio', ax=axes[0, 1], errorbar='sd')
        axes[0, 1].set_title('Comment Ratio by Variant', fontsize=14, weight='bold')
        axes[0, 1].set_ylabel('Comment Lines / Total Lines')
        axes[0, 1].set_xticklabels(axes[0, 1].get_xticklabels(), rotation=45, ha='right')

        # Code lines vs score
        for variant in self.df['variant'].unique():
            data = self.df[self.df['variant'] == variant]
            axes[1, 0].scatter(data['code_lines'], data['score'], label=variant, alpha=0.6, s=100)
        axes[1, 0].set_xlabel('Code Lines')
        axes[1, 0].set_ylabel('Score')
        axes[1, 0].set_title('Code Length vs Score', fontsize=14, weight='bold')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # Tokens vs code lines
        for variant in self.df['variant'].unique():
            data = self.df[self.df['variant'] == variant]
            axes[1, 1].scatter(data['code_lines'], data['total_tokens'], label=variant, alpha=0.6, s=100)
        axes[1, 1].set_xlabel('Code Lines')
        axes[1, 1].set_ylabel('Total Tokens')
        axes[1, 1].set_title('Code Lines vs Token Count', fontsize=14, weight='bold')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_dir / 'code_metrics.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✓ code_metrics.png")

    def _plot_comprehensive_heatmap(self, output_dir: Path):
        """Plot comprehensive heatmap of all metrics by variant and provider."""
        # Aggregate data
        metrics = ['score', 'accuracy', 'performance', 'code_quality', 'completeness']

        # Create pivot table for variant comparison
        pivot_data = []
        for metric in metrics:
            for variant in sorted(self.df['variant'].unique()):
                mean_val = self.df[self.df['variant'] == variant][metric].mean() * 100
                pivot_data.append({'Variant': variant, 'Metric': metric.replace('_', ' ').title(), 'Value': mean_val})

        pivot_df = pd.DataFrame(pivot_data)
        pivot_table = pivot_df.pivot(index='Variant', columns='Metric', values='Value')

        plt.figure(figsize=(12, 8))
        sns.heatmap(pivot_table, annot=True, fmt='.1f', cmap='RdYlGn', center=50,
                   vmin=0, vmax=100, cbar_kws={'label': 'Score (%)'})
        plt.title('Comprehensive Metrics Heatmap by Variant', fontsize=16, weight='bold')
        plt.tight_layout()
        plt.savefig(output_dir / 'comprehensive_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✓ comprehensive_heatmap.png")

    def _plot_f1_precision_recall(self, output_dir: Path):
        """Plot F1, Precision, and Recall metrics."""
        # Filter out NaN values
        df_f1 = self.df[self.df['f1_score'].notna()]

        if len(df_f1) == 0:
            print("  ⚠ Skipping F1/Precision/Recall plot (no data)")
            return

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # F1 Score by variant
        sns.barplot(data=df_f1, x='variant', y='f1_score', ax=axes[0, 0], errorbar='sd')
        axes[0, 0].set_title('F1 Score by Variant', fontsize=14, weight='bold')
        axes[0, 0].set_ylabel('F1 Score')
        axes[0, 0].set_ylim([0, 1.05])
        axes[0, 0].set_xticklabels(axes[0, 0].get_xticklabels(), rotation=45, ha='right')

        # Precision vs Recall scatter
        for variant in df_f1['variant'].unique():
            data = df_f1[df_f1['variant'] == variant]
            axes[0, 1].scatter(data['recall'], data['precision'], label=variant, alpha=0.6, s=100)
        axes[0, 1].plot([0, 1], [0, 1], 'k--', alpha=0.3, label='Perfect')
        axes[0, 1].set_xlabel('Recall')
        axes[0, 1].set_ylabel('Precision')
        axes[0, 1].set_title('Precision vs Recall', fontsize=14, weight='bold')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].set_xlim([0, 1.05])
        axes[0, 1].set_ylim([0, 1.05])

        # Precision by variant
        sns.barplot(data=df_f1, x='variant', y='precision', ax=axes[1, 0], errorbar='sd')
        axes[1, 0].set_title('Precision by Variant', fontsize=14, weight='bold')
        axes[1, 0].set_ylabel('Precision')
        axes[1, 0].set_ylim([0, 1.05])
        axes[1, 0].set_xticklabels(axes[1, 0].get_xticklabels(), rotation=45, ha='right')

        # Recall by variant
        sns.barplot(data=df_f1, x='variant', y='recall', ax=axes[1, 1], errorbar='sd')
        axes[1, 1].set_title('Recall by Variant', fontsize=14, weight='bold')
        axes[1, 1].set_ylabel('Recall')
        axes[1, 1].set_ylim([0, 1.05])
        axes[1, 1].set_xticklabels(axes[1, 1].get_xticklabels(), rotation=45, ha='right')

        plt.tight_layout()
        plt.savefig(output_dir / 'f1_precision_recall.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✓ f1_precision_recall.png")

    def _plot_complexity_metrics(self, output_dir: Path):
        """Plot code complexity metrics."""
        df_complex = self.df[self.df['cyclomatic_complexity'].notna()]

        if len(df_complex) == 0:
            print("  ⚠ Skipping complexity metrics plot (no data)")
            return

        fig, axes = plt.subplots(2, 3, figsize=(20, 12))

        # Cyclomatic Complexity
        sns.barplot(data=df_complex, x='variant', y='cyclomatic_complexity', ax=axes[0, 0], errorbar='sd')
        axes[0, 0].set_title('Cyclomatic Complexity by Variant', fontsize=14, weight='bold')
        axes[0, 0].set_ylabel('Cyclomatic Complexity')
        axes[0, 0].set_xticklabels(axes[0, 0].get_xticklabels(), rotation=45, ha='right')

        # Halstead Volume
        sns.barplot(data=df_complex, x='variant', y='halstead_volume', ax=axes[0, 1], errorbar='sd')
        axes[0, 1].set_title('Halstead Volume by Variant', fontsize=14, weight='bold')
        axes[0, 1].set_ylabel('Halstead Volume')
        axes[0, 1].set_xticklabels(axes[0, 1].get_xticklabels(), rotation=45, ha='right')

        # Maintainability Index
        sns.barplot(data=df_complex, x='variant', y='maintainability_index', ax=axes[0, 2], errorbar='sd')
        axes[0, 2].set_title('Maintainability Index by Variant', fontsize=14, weight='bold')
        axes[0, 2].set_ylabel('Maintainability Index (0-171)')
        axes[0, 2].set_xticklabels(axes[0, 2].get_xticklabels(), rotation=45, ha='right')

        # Cyclomatic Complexity vs Score
        for variant in df_complex['variant'].unique():
            data = df_complex[df_complex['variant'] == variant]
            axes[1, 0].scatter(data['cyclomatic_complexity'], data['score'], label=variant, alpha=0.6, s=100)
        axes[1, 0].set_xlabel('Cyclomatic Complexity')
        axes[1, 0].set_ylabel('Score')
        axes[1, 0].set_title('Cyclomatic Complexity vs Score', fontsize=14, weight='bold')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # Maintainability Index vs Score
        for variant in df_complex['variant'].unique():
            data = df_complex[df_complex['variant'] == variant]
            axes[1, 1].scatter(data['maintainability_index'], data['score'], label=variant, alpha=0.6, s=100)
        axes[1, 1].set_xlabel('Maintainability Index')
        axes[1, 1].set_ylabel('Score')
        axes[1, 1].set_title('Maintainability Index vs Score', fontsize=14, weight='bold')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)

        # Nesting Depth
        sns.barplot(data=df_complex, x='variant', y='max_nesting_depth', ax=axes[1, 2], errorbar='sd')
        axes[1, 2].set_title('Max Nesting Depth by Variant', fontsize=14, weight='bold')
        axes[1, 2].set_ylabel('Max Nesting Depth')
        axes[1, 2].set_xticklabels(axes[1, 2].get_xticklabels(), rotation=45, ha='right')

        plt.tight_layout()
        plt.savefig(output_dir / 'complexity_metrics.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✓ complexity_metrics.png")

    def _plot_pass_at_k(self, output_dir: Path):
        """Plot Pass@k curves."""
        # Calculate Pass@k for each variant/provider combination
        pass_at_k_data = []

        # Group by task/provider/variant
        grouped = self.df.groupby(['provider', 'variant', 'task'])

        for (provider, variant, task), group in grouped:
            # Sort by run number
            runs = group.sort_values('run')
            # Consider passed if accuracy > 0.9
            passed_runs = (runs['accuracy'] > 0.9).values

            # Calculate Pass@k for k=1 to len(passed_runs)
            for k in range(1, len(passed_runs) + 1):
                # Check if at least one of first k attempts passed
                pass_at_k = int(any(passed_runs[:k]))
                pass_at_k_data.append({
                    'provider': provider,
                    'variant': variant,
                    'task': task,
                    'k': k,
                    'passed': pass_at_k
                })

        if not pass_at_k_data:
            print("  ⚠ Skipping Pass@k plot (insufficient data)")
            return

        df_pass = pd.DataFrame(pass_at_k_data)

        # Calculate average Pass@k across all tasks for each k
        pass_rates = df_pass.groupby(['variant', 'k'])['passed'].mean().reset_index()

        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        # Pass@k curves by variant
        for variant in pass_rates['variant'].unique():
            data = pass_rates[pass_rates['variant'] == variant]
            axes[0].plot(data['k'], data['passed'] * 100, marker='o', label=variant, linewidth=2)

        axes[0].set_xlabel('k (Number of Attempts)', fontsize=12)
        axes[0].set_ylabel('Pass@k (%)', fontsize=12)
        axes[0].set_title('Pass@k: % Problems Solved in k Attempts', fontsize=14, weight='bold')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        axes[0].set_ylim([0, 105])

        # Pass@1, Pass@3, Pass@5 comparison
        k_values = [1, 3, 5]
        comparison_data = []
        for variant in self.df['variant'].unique():
            for k in k_values:
                k_data = pass_rates[(pass_rates['variant'] == variant) & (pass_rates['k'] == k)]
                if not k_data.empty:
                    comparison_data.append({
                        'Variant': variant,
                        'Metric': f'Pass@{k}',
                        'Value': k_data['passed'].values[0] * 100
                    })

        if comparison_data:
            df_comp = pd.DataFrame(comparison_data)
            pivot = df_comp.pivot(index='Variant', columns='Metric', values='Value')

            x = np.arange(len(pivot.index))
            width = 0.25

            for i, col in enumerate(pivot.columns):
                axes[1].bar(x + i * width, pivot[col], width, label=col)

            axes[1].set_xlabel('Variant', fontsize=12)
            axes[1].set_ylabel('Pass Rate (%)', fontsize=12)
            axes[1].set_title('Pass@k Comparison', fontsize=14, weight='bold')
            axes[1].set_xticks(x + width)
            axes[1].set_xticklabels(pivot.index, rotation=45, ha='right')
            axes[1].legend()
            axes[1].grid(True, alpha=0.3, axis='y')
            axes[1].set_ylim([0, 105])

        plt.tight_layout()
        plt.savefig(output_dir / 'pass_at_k.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✓ pass_at_k.png")

    def _plot_code_variation(self, output_dir: Path):
        """Plot code variation metrics for multi-run benchmarks."""
        if not self.raw_data:
            print("  ⚠ Skipping code variation plot (no raw data)")
            return

        # Extract code variation data from raw JSON
        variation_data = []
        for record in self.raw_data:
            if not record.get('success'):
                continue

            code_var = record.get('codeVariation')
            if code_var and isinstance(code_var, dict):
                variation_data.append({
                    'task': record.get('taskName'),
                    'provider': record.get('provider'),
                    'variant': record.get('variant'),
                    'total_samples': code_var.get('totalSamples', 0),
                    'unique_outputs': code_var.get('uniqueOutputs', 0),
                    'duplicate_rate': code_var.get('duplicateRate', 0),
                    'avg_similarity': code_var.get('avgSimilarity', 0)
                })

        if not variation_data:
            print("  ⚠ Skipping code variation plot (no multi-run data)")
            return

        df_var = pd.DataFrame(variation_data)

        # Create 2x2 grid of plots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # 1. Duplicate Rate by Task/Variant
        pivot_dup = df_var.pivot_table(
            values='duplicate_rate',
            index='task',
            columns='variant',
            aggfunc='mean'
        )

        if not pivot_dup.empty:
            sns.heatmap(
                pivot_dup * 100,
                annot=True,
                fmt='.1f',
                cmap='YlOrRd',
                ax=axes[0, 0],
                cbar_kws={'label': 'Duplicate Rate (%)'},
                vmin=0,
                vmax=100
            )
            axes[0, 0].set_title('Duplicate Rate: % Identical Code Across Runs', fontsize=14, weight='bold')
            axes[0, 0].set_xlabel('Variant')
            axes[0, 0].set_ylabel('Task')
        else:
            axes[0, 0].text(0.5, 0.5, 'No data', ha='center', va='center', transform=axes[0, 0].transAxes)

        # 2. Code Similarity Heatmap
        pivot_sim = df_var.pivot_table(
            values='avg_similarity',
            index='task',
            columns='variant',
            aggfunc='mean'
        )

        if not pivot_sim.empty:
            sns.heatmap(
                pivot_sim * 100,
                annot=True,
                fmt='.1f',
                cmap='viridis',
                ax=axes[0, 1],
                cbar_kws={'label': 'Avg Similarity (%)'},
                vmin=0,
                vmax=100
            )
            axes[0, 1].set_title('Average Code Similarity Between Runs', fontsize=14, weight='bold')
            axes[0, 1].set_xlabel('Variant')
            axes[0, 1].set_ylabel('Task')
        else:
            axes[0, 1].text(0.5, 0.5, 'No data', ha='center', va='center', transform=axes[0, 1].transAxes)

        # 3. Unique Outputs Distribution
        if len(df_var) > 0:
            df_var['diversity_rate'] = (df_var['unique_outputs'] / df_var['total_samples']) * 100

            for variant in df_var['variant'].unique():
                data = df_var[df_var['variant'] == variant]['diversity_rate']
                axes[1, 0].hist(data, alpha=0.6, label=variant, bins=10, edgecolor='black')

            axes[1, 0].set_xlabel('Diversity Rate (% Unique Outputs)', fontsize=12)
            axes[1, 0].set_ylabel('Frequency', fontsize=12)
            axes[1, 0].set_title('Distribution of Code Diversity Across Tasks', fontsize=14, weight='bold')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3, axis='y')
            axes[1, 0].set_xlim([0, 105])

        # 4. Variation Summary by Variant
        if len(df_var) > 0:
            summary = df_var.groupby('variant').agg({
                'duplicate_rate': 'mean',
                'avg_similarity': 'mean',
                'unique_outputs': 'mean'
            }).reset_index()

            x = np.arange(len(summary))
            width = 0.25

            bars1 = axes[1, 1].bar(
                x - width,
                summary['duplicate_rate'] * 100,
                width,
                label='Duplicate Rate',
                color='coral'
            )
            bars2 = axes[1, 1].bar(
                x,
                summary['avg_similarity'] * 100,
                width,
                label='Avg Similarity',
                color='skyblue'
            )
            bars3 = axes[1, 1].bar(
                x + width,
                (summary['unique_outputs'] / df_var['total_samples'].max()) * 100,
                width,
                label='Diversity (normalized)',
                color='lightgreen'
            )

            axes[1, 1].set_xlabel('Variant', fontsize=12)
            axes[1, 1].set_ylabel('Percentage (%)', fontsize=12)
            axes[1, 1].set_title('Code Variation Metrics by Variant', fontsize=14, weight='bold')
            axes[1, 1].set_xticks(x)
            axes[1, 1].set_xticklabels(summary['variant'], rotation=45, ha='right')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3, axis='y')
            axes[1, 1].set_ylim([0, 105])

        plt.tight_layout()
        plt.savefig(output_dir / 'code_variation.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✓ code_variation.png")

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python analyze_results.py <results-file.json> [--visualize] [--reports-dir <path>]")
        sys.exit(1)

    results_file = args[0]
    do_visualize = '--visualize' in args

    reports_dir = './reports'
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