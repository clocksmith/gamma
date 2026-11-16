/**
 * Report Generator for DREAM Benchmarks
 * Generates comprehensive reports from benchmark results with statistical analysis
 */

import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';
import { StatisticalAnalyzer } from '../utils/statistical-analyzer.js';

export class ReportGenerator {
  constructor(config = {}) {
    this.config = {
      resultsDir: config.resultsDir || './results',
      reportsDir: config.reportsDir || './reports',
      runLabel: config.runLabel || null
    };
  }

  /**
   * Generate and save JSON report from results with full statistics
   */
  async generate(results) {
    if (!results || results.length === 0) {
      console.log('No results to save');
      return null;
    }

    try {
      // Ensure reports directory exists
      await mkdir(this.config.reportsDir, { recursive: true });

      // Create filename with timestamp
      const timestamp = this.config.runLabel || new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `benchmark-results-${timestamp}.json`;
      const filePath = join(this.config.reportsDir, filename);

      // Generate comprehensive report with statistics
      const report = this.generateComprehensiveReport(results);

      // Write results to file
      await writeFile(filePath, JSON.stringify(report, null, 2), 'utf-8');

      console.log(`\n📄 Results saved to: ${filePath}`);
      return filePath;
    } catch (error) {
      console.warn(`Failed to save results: ${error.message}`);
      return null;
    }
  }

  /**
   * Generate comprehensive report with all statistics
   */
  generateComprehensiveReport(results) {
    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success && !r.skipped);
    const skipped = results.filter(r => r.skipped);

    // Group results by task+provider+variant for multi-run analysis
    const groupedResults = this.groupResults(results);

    // Calculate statistics for each group
    const groupStats = this.calculateGroupStatistics(groupedResults);

    // Calculate overall statistics
    const overallStats = this.calculateOverallStatistics(successful);

    // Language comparison (JS vs TS)
    const languageComparison = this.calculateLanguageComparison(successful);

    return {
      metadata: {
        generatedAt: new Date().toISOString(),
        runLabel: this.config.runLabel,
        totalRuns: results.length,
        uniqueTasks: new Set(results.map(r => r.taskName)).size,
        uniqueProviders: new Set(results.map(r => r.provider)).size,
        uniqueVariants: new Set(results.map(r => r.variant)).size
      },
      summary: {
        total: results.length,
        successful: successful.length,
        failed: failed.length,
        skipped: skipped.length,
        successRate: results.length > 0 ? (successful.length / results.length * 100).toFixed(2) + '%' : '0%'
      },
      overallStatistics: overallStats,
      languageComparison,
      groupedStatistics: groupStats,
      rawResults: results
    };
  }

  /**
   * Group results by task+provider+variant
   */
  groupResults(results) {
    const groups = new Map();

    for (const result of results) {
      const key = `${result.taskName}|${result.provider}|${result.variant}`;
      if (!groups.has(key)) {
        groups.set(key, {
          taskName: result.taskName,
          provider: result.provider,
          variant: result.variant,
          category: result.category,
          language: result.language || (result.variant?.includes('typescript') ? 'typescript' : 'javascript'),
          runs: []
        });
      }
      groups.get(key).runs.push(result);
    }

    return groups;
  }

  /**
   * Calculate statistics for each group (multi-run analysis)
   */
  calculateGroupStatistics(groupedResults) {
    const stats = [];

    for (const [key, group] of groupedResults) {
      const successfulRuns = group.runs.filter(r => r.success);
      const numRuns = group.runs.length;
      const numSuccessful = successfulRuns.length;

      // Extract metrics arrays for statistical analysis
      const durations = successfulRuns.map(r => r.duration).filter(d => d != null);
      const accuracies = successfulRuns
        .map(r => r.benchmarks?.accuracyScore)
        .filter(a => a != null);
      const runtimePerfs = successfulRuns
        .flatMap(r => r.benchmarks?.runtimePerformance || [])
        .map(p => p.meanTimeMs)
        .filter(t => t != null && isFinite(t));
      const autoRaterScores = successfulRuns
        .map(r => r.benchmarks?.autoRater?.score)
        .filter(s => s != null);
      const complexities = successfulRuns
        .map(r => r.benchmarks?.complexity?.cyclomaticComplexity)
        .filter(c => c != null);
      const codeLines = successfulRuns
        .map(r => r.benchmarks?.codeSizeMetrics?.codeLines)
        .filter(l => l != null);

      const groupStat = {
        key,
        taskName: group.taskName,
        provider: group.provider,
        variant: group.variant,
        category: group.category,
        language: group.language,
        runInfo: {
          totalRuns: numRuns,
          successfulRuns: numSuccessful,
          failedRuns: numRuns - numSuccessful,
          successRate: numRuns > 0 ? (numSuccessful / numRuns * 100).toFixed(1) + '%' : '0%'
        },
        metrics: {}
      };

      // Calculate statistics for each metric (only if we have data)
      if (durations.length > 0) {
        groupStat.metrics.duration = this.computeMetricStats(durations, 'ms');
      }
      if (accuracies.length > 0) {
        groupStat.metrics.accuracy = this.computeMetricStats(accuracies.map(a => a * 100), '%');
      }
      if (runtimePerfs.length > 0) {
        groupStat.metrics.runtimePerformance = this.computeMetricStats(runtimePerfs, 'ms');
      }
      if (autoRaterScores.length > 0) {
        groupStat.metrics.autoRater = this.computeMetricStats(autoRaterScores.map(s => s * 100), '%');
      }
      if (complexities.length > 0) {
        groupStat.metrics.complexity = this.computeMetricStats(complexities, '');
      }
      if (codeLines.length > 0) {
        groupStat.metrics.codeLines = this.computeMetricStats(codeLines, 'lines');
      }

      stats.push(groupStat);
    }

    return stats;
  }

  /**
   * Compute comprehensive statistics for a metric
   */
  computeMetricStats(values, unit) {
    if (!values || values.length === 0) {
      return null;
    }

    const stats = StatisticalAnalyzer.calculateStats(values);
    if (!stats) return null;

    const result = {
      n: stats.count,
      mean: this.round(stats.mean),
      unit
    };

    // Only add extended stats if we have multiple runs
    if (stats.count > 1) {
      result.stdDev = this.round(stats.stdDev);
      result.stderr = this.round(stats.stderr);
      result.min = this.round(stats.min);
      result.max = this.round(stats.max);
      result.range = this.round(stats.range);
      result.median = this.round(stats.median);
      result.cv = this.round(stats.cv) + '%'; // Coefficient of variation

      // Add confidence interval if enough samples
      if (stats.count >= 3) {
        const ci = StatisticalAnalyzer.confidenceInterval(values, 0.95);
        if (ci) {
          result.ci95 = {
            lower: this.round(ci.lower),
            upper: this.round(ci.upper),
            marginOfError: this.round(ci.marginOfError)
          };
        }
      }

      // Report outliers if any
      if (stats.outliers && stats.outliers.length > 0) {
        result.outliers = stats.outliers.length;
      }
    }

    return result;
  }

  /**
   * Calculate overall statistics across all results
   */
  calculateOverallStatistics(successfulResults) {
    if (successfulResults.length === 0) {
      return null;
    }

    const accuracies = successfulResults
      .map(r => r.benchmarks?.accuracyScore)
      .filter(a => a != null);
    const runtimes = successfulResults
      .flatMap(r => r.benchmarks?.runtimePerformance || [])
      .map(p => p.meanTimeMs)
      .filter(t => t != null && isFinite(t));
    const autoRaters = successfulResults
      .map(r => r.benchmarks?.autoRater?.score)
      .filter(s => s != null);

    return {
      accuracy: accuracies.length > 0 ? this.computeMetricStats(accuracies.map(a => a * 100), '%') : null,
      runtimePerformance: runtimes.length > 0 ? this.computeMetricStats(runtimes, 'ms') : null,
      autoRater: autoRaters.length > 0 ? this.computeMetricStats(autoRaters.map(s => s * 100), '%') : null
    };
  }

  /**
   * Calculate JavaScript vs TypeScript comparison with statistical tests
   */
  calculateLanguageComparison(successfulResults) {
    const jsResults = successfulResults.filter(r =>
      r.variant && !r.variant.includes('typescript')
    );
    const tsResults = successfulResults.filter(r =>
      r.variant && r.variant.includes('typescript')
    );

    if (jsResults.length === 0 || tsResults.length === 0) {
      return null;
    }

    const jsAccuracies = jsResults
      .map(r => r.benchmarks?.accuracyScore)
      .filter(a => a != null);
    const tsAccuracies = tsResults
      .map(r => r.benchmarks?.accuracyScore)
      .filter(a => a != null);

    const jsRuntimes = jsResults
      .flatMap(r => r.benchmarks?.runtimePerformance || [])
      .map(p => p.meanTimeMs)
      .filter(t => t != null && isFinite(t));
    const tsRuntimes = tsResults
      .flatMap(r => r.benchmarks?.runtimePerformance || [])
      .map(p => p.meanTimeMs)
      .filter(t => t != null && isFinite(t));

    const comparison = {
      javascript: {
        runs: jsResults.length,
        accuracy: jsAccuracies.length > 0 ? this.computeMetricStats(jsAccuracies.map(a => a * 100), '%') : null,
        runtime: jsRuntimes.length > 0 ? this.computeMetricStats(jsRuntimes, 'ms') : null
      },
      typescript: {
        runs: tsResults.length,
        accuracy: tsAccuracies.length > 0 ? this.computeMetricStats(tsAccuracies.map(a => a * 100), '%') : null,
        runtime: tsRuntimes.length > 0 ? this.computeMetricStats(tsRuntimes, 'ms') : null
      }
    };

    // Perform statistical comparison if we have enough data
    if (jsAccuracies.length >= 2 && tsAccuracies.length >= 2) {
      const tTest = StatisticalAnalyzer.tTest(
        jsAccuracies.map(a => a * 100),
        tsAccuracies.map(a => a * 100)
      );
      if (tTest) {
        comparison.accuracyComparison = {
          meanDifference: this.round(tTest.meanDiff),
          isSignificant: tTest.isSignificant,
          pValue: tTest.pValue < 0.001 ? '<0.001' : this.round(tTest.pValue),
          effectSize: tTest.effectSize,
          cohensD: this.round(tTest.cohensD)
        };
      }
    }

    if (jsRuntimes.length >= 2 && tsRuntimes.length >= 2) {
      const tTest = StatisticalAnalyzer.tTest(jsRuntimes, tsRuntimes);
      if (tTest) {
        comparison.runtimeComparison = {
          meanDifference: this.round(tTest.meanDiff) + 'ms',
          isSignificant: tTest.isSignificant,
          pValue: tTest.pValue < 0.001 ? '<0.001' : this.round(tTest.pValue),
          effectSize: tTest.effectSize,
          cohensD: this.round(tTest.cohensD)
        };
      }
    }

    return comparison;
  }

  /**
   * Round number to reasonable precision
   */
  round(num, decimals = 2) {
    if (num === null || num === undefined || !isFinite(num)) return null;
    return Math.round(num * Math.pow(10, decimals)) / Math.pow(10, decimals);
  }

  /**
   * Generate a basic text report from results
   */
  static generateTextReport(results) {
    if (!results || results.length === 0) {
      return 'No results to report';
    }

    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success && !r.skipped);
    const skipped = results.filter(r => r.skipped);

    let report = '\n╔══════════════════════════════════════════════════════════════╗\n';
    report += '║              DREAM Benchmark Results Report                  ║\n';
    report += '╚══════════════════════════════════════════════════════════════╝\n\n';

    report += `📊 Summary:\n`;
    report += `   Total Runs:  ${results.length}\n`;
    report += `   Successful:  ${successful.length}\n`;
    report += `   Failed:      ${failed.length}\n`;
    report += `   Skipped:     ${skipped.length}\n`;
    report += `   Success Rate: ${(successful.length / results.length * 100).toFixed(1)}%\n\n`;

    // Group by variant for comparison
    const byVariant = {};
    successful.forEach(r => {
      if (!byVariant[r.variant]) {
        byVariant[r.variant] = [];
      }
      byVariant[r.variant].push(r);
    });

    report += `📈 Results by Variant:\n`;
    for (const [variant, variantResults] of Object.entries(byVariant)) {
      const accuracies = variantResults
        .map(r => r.benchmarks?.accuracyScore)
        .filter(a => a != null);
      const avgAccuracy = accuracies.length > 0
        ? (accuracies.reduce((a, b) => a + b, 0) / accuracies.length * 100).toFixed(1)
        : 'N/A';

      report += `\n   ${variant} (n=${variantResults.length}):\n`;
      report += `     Accuracy: ${avgAccuracy}%\n`;
    }

    return report;
  }

  /**
   * Generate a JSON report from results
   */
  static generateJSONReport(results) {
    return JSON.stringify(results, null, 2);
  }

  /**
   * Generate a summary from results
   */
  static generateSummary(results) {
    const total = results.length;
    const passed = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success && !r.skipped).length;
    const skipped = results.filter(r => r.skipped).length;

    return {
      total,
      passed,
      failed,
      skipped,
      passRate: total > 0 ? (passed / total * 100).toFixed(2) + '%' : '0%'
    };
  }

  /**
   * Generate and save report to file
   */
  static async saveReport(results, outputPath, format = 'json') {
    const report = format === 'json'
      ? this.generateJSONReport(results)
      : this.generateTextReport(results);

    console.log('Report saved to:', outputPath);
    return report;
  }
}

export default ReportGenerator;
