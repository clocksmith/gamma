/**
 * Historical Benchmark Tracker
 * Tracks benchmark results over time and detects regressions
 */

import { readFile, writeFile, readdir } from 'fs/promises';
import { existsSync } from 'fs';
import { join } from 'path';
import { StatisticalAnalyzer } from './statistical-analyzer.js';

export class HistoricalTracker {
  constructor(historyDir = './benchmark/history') {
    this.historyDir = historyDir;
  }

  /**
   * Save current benchmark results to history
   */
  async saveResults(results, metadata = {}) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `benchmark-${timestamp}.json`;
    const filepath = join(this.historyDir, filename);

    const historyEntry = {
      timestamp: new Date().toISOString(),
      metadata: {
        ...metadata,
        git_commit: await this.getGitCommit(),
        git_branch: await this.getGitBranch(),
        node_version: process.version
      },
      results,
      summary: this.summarizeResults(results)
    };

    try {
      const { mkdirSync } = await import('fs');
      mkdirSync(this.historyDir, { recursive: true });
      await writeFile(filepath, JSON.stringify(historyEntry, null, 2));
      console.log(`✓ Saved historical results to ${filename}`);
      return filepath;
    } catch (error) {
      console.error(`Failed to save historical results: ${error.message}`);
      return null;
    }
  }

  /**
   * Load all historical results
   */
  async loadHistory() {
    if (!existsSync(this.historyDir)) {
      return [];
    }

    try {
      const files = await readdir(this.historyDir);
      const historyFiles = files.filter(f => f.startsWith('benchmark-') && f.endsWith('.json'));

      const history = [];
      for (const file of historyFiles) {
        const filepath = join(this.historyDir, file);
        const content = await readFile(filepath, 'utf-8');
        const data = JSON.parse(content);
        history.push(data);
      }

      // Sort by timestamp
      return history.sort((a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      );
    } catch (error) {
      console.error(`Failed to load history: ${error.message}`);
      return [];
    }
  }

  /**
   * Compare current results with historical baseline
   */
  async compareWithBaseline(currentResults, baselineCount = 5) {
    const history = await this.loadHistory();

    if (history.length === 0) {
      return {
        hasBaseline: false,
        message: 'No historical data available for comparison'
      };
    }

    // Get last N runs as baseline
    const baseline = history.slice(-Math.min(baselineCount, history.length));
    const comparison = this.compareResults(currentResults, baseline);

    return {
      hasBaseline: true,
      baseline: baseline.map(h => ({
        timestamp: h.timestamp,
        summary: h.summary
      })),
      comparison,
      regressions: this.detectRegressions(comparison)
    };
  }

  /**
   * Compare current results with historical data
   */
  compareResults(currentResults, historicalData) {
    const comparisons = [];

    // Group current results by provider/variant/task
    const currentGroups = this.groupResults(currentResults);

    for (const [key, currentGroup] of Object.entries(currentGroups)) {
      // Extract historical values for this group
      const historicalValues = historicalData.map(h => {
        const hResults = this.groupResults(h.results);
        return hResults[key];
      }).filter(Boolean);

      if (historicalValues.length === 0) continue;

      // Calculate statistics
      const currentScores = currentGroup.map(r => r.evaluation.totalScore);
      const currentDurations = currentGroup.map(r => r.duration);

      const historicalScores = historicalValues.flatMap(g =>
        g.map(r => r.evaluation.totalScore)
      );
      const historicalDurations = historicalValues.flatMap(g =>
        g.map(r => r.duration)
      );

      const [provider, variant, taskName] = key.split('|');

      comparisons.push({
        provider,
        variant,
        taskName,
        current: {
          score: StatisticalAnalyzer.calculateStats(currentScores),
          duration: StatisticalAnalyzer.calculateStats(currentDurations)
        },
        historical: {
          score: StatisticalAnalyzer.calculateStats(historicalScores),
          duration: StatisticalAnalyzer.calculateStats(historicalDurations)
        },
        comparison: {
          scoreChange: this.calculateChange(currentScores, historicalScores),
          durationChange: this.calculateChange(currentDurations, historicalDurations),
          scoreTTest: StatisticalAnalyzer.tTest(currentScores, historicalScores),
          durationTTest: StatisticalAnalyzer.tTest(currentDurations, historicalDurations)
        }
      });
    }

    return comparisons;
  }

  /**
   * Detect regressions in benchmark results
   */
  detectRegressions(comparisons, scoreThreshold = -5, durationThreshold = 20) {
    const regressions = [];

    for (const comp of comparisons) {
      const issues = [];

      // Check for score regression (5% drop or more)
      if (comp.comparison.scoreChange.percentChange < scoreThreshold &&
          comp.comparison.scoreTTest?.isSignificant) {
        issues.push({
          type: 'score_regression',
          severity: 'high',
          message: `Score decreased by ${Math.abs(comp.comparison.scoreChange.percentChange).toFixed(1)}%`,
          current: comp.current.score.mean,
          historical: comp.historical.score.mean
        });
      }

      // Check for performance regression (20% slower or more)
      if (comp.comparison.durationChange.percentChange > durationThreshold &&
          comp.comparison.durationTTest?.isSignificant) {
        issues.push({
          type: 'performance_regression',
          severity: 'medium',
          message: `Duration increased by ${comp.comparison.durationChange.percentChange.toFixed(1)}%`,
          current: comp.current.duration.mean,
          historical: comp.historical.duration.mean
        });
      }

      if (issues.length > 0) {
        regressions.push({
          provider: comp.provider,
          variant: comp.variant,
          taskName: comp.taskName,
          issues
        });
      }
    }

    return regressions;
  }

  /**
   * Calculate change between two sets of values
   */
  calculateChange(current, historical) {
    const currentMean = current.reduce((a, b) => a + b, 0) / current.length;
    const historicalMean = historical.reduce((a, b) => a + b, 0) / historical.length;

    const absoluteChange = currentMean - historicalMean;
    const percentChange = historicalMean !== 0 ?
      (absoluteChange / historicalMean) * 100 : 0;

    return {
      current: currentMean,
      historical: historicalMean,
      absoluteChange,
      percentChange,
      trend: percentChange > 1 ? 'improving' :
             percentChange < -1 ? 'degrading' : 'stable'
    };
  }

  /**
   * Group results by provider, variant, and task
   */
  groupResults(results) {
    const groups = {};

    for (const result of results) {
      if (!result.success || !result.evaluation) continue;

      const key = `${result.provider}|${result.variant}|${result.taskName}`;
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(result);
    }

    return groups;
  }

  /**
   * Summarize results for storage
   */
  summarizeResults(results) {
    const successful = results.filter(r => r.success);

    if (successful.length === 0) {
      return { count: 0, avgScore: 0, avgDuration: 0 };
    }

    const scores = successful.map(r => r.evaluation.totalScore);
    const durations = successful.map(r => r.duration);

    return {
      count: results.length,
      successful: successful.length,
      failed: results.length - successful.length,
      scores: StatisticalAnalyzer.calculateStats(scores),
      durations: StatisticalAnalyzer.calculateStats(durations)
    };
  }

  /**
   * Get current git commit hash
   */
  async getGitCommit() {
    try {
      const { execSync } = await import('child_process');
      return execSync('git rev-parse HEAD', { encoding: 'utf-8' }).trim();
    } catch {
      return 'unknown';
    }
  }

  /**
   * Get current git branch
   */
  async getGitBranch() {
    try {
      const { execSync } = await import('child_process');
      return execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf-8' }).trim();
    } catch {
      return 'unknown';
    }
  }

  /**
   * Generate trend analysis over time
   */
  async analyzeTrends(metricName = 'score', groupBy = 'variant') {
    const history = await this.loadHistory();

    if (history.length < 3) {
      return {
        hasEnoughData: false,
        message: 'Need at least 3 historical data points for trend analysis'
      };
    }

    const trends = {};

    // Group by specified dimension
    for (const entry of history) {
      const groups = this.groupResults(entry.results);

      for (const [key, results] of Object.entries(groups)) {
        const [provider, variant, taskName] = key.split('|');
        let groupKey;

        if (groupBy === 'variant') groupKey = variant;
        else if (groupBy === 'provider') groupKey = provider;
        else if (groupBy === 'task') groupKey = taskName;
        else groupKey = key;

        if (!trends[groupKey]) {
          trends[groupKey] = [];
        }

        const values = results.map(r =>
          metricName === 'score' ? r.evaluation.totalScore : r.duration
        );

        trends[groupKey].push({
          timestamp: entry.timestamp,
          mean: values.reduce((a, b) => a + b, 0) / values.length,
          min: Math.min(...values),
          max: Math.max(...values)
        });
      }
    }

    // Analyze each trend
    const analysis = {};
    for (const [key, data] of Object.entries(trends)) {
      const values = data.map(d => d.mean);
      const trendAnalysis = StatisticalAnalyzer.analyzeTrend(values);

      analysis[key] = {
        data,
        trend: trendAnalysis,
        summary: `${key}: ${trendAnalysis.trend} (${trendAnalysis.percentChange.toFixed(1)}% change)`
      };
    }

    return {
      hasEnoughData: true,
      trends: analysis,
      period: {
        start: history[0].timestamp,
        end: history[history.length - 1].timestamp,
        dataPoints: history.length
      }
    };
  }

  /**
   * Generate regression report
   */
  generateRegressionReport(regressions) {
    if (regressions.length === 0) {
      return '✓ No regressions detected';
    }

    const lines = [
      '\n⚠️  REGRESSIONS DETECTED',
      '=' .repeat(50),
      ''
    ];

    for (const regression of regressions) {
      lines.push(`${regression.provider} / ${regression.variant} / ${regression.taskName}`);

      for (const issue of regression.issues) {
        const emoji = issue.severity === 'high' ? '🔴' : '🟡';
        lines.push(`  ${emoji} ${issue.message}`);
        lines.push(`     Current: ${issue.current.toFixed(2)}`);
        lines.push(`     Historical: ${issue.historical.toFixed(2)}`);
      }

      lines.push('');
    }

    return lines.join('\n');
  }
}
