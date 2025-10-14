/**
 * Report Generator
 * Generates comprehensive reports and visualizations from benchmark results.
 * This version is refactored to handle multiple runs per benchmark,
 * providing statistical analysis for more robust insights.
 */

import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';

export class ReportGenerator {
  constructor(outputConfig) {
    this.config = outputConfig;
  }

  /**
   * Primary method to generate all reports.
   * It now processes the raw results before generating reports.
   */
  async generate(rawResults) {
    if (rawResults.length === 0) {
      console.log('No results to generate reports from.');
      return null;
    }

    await this.ensureDirectories();

    const processedData = this._processResults(rawResults);

    const resultsFilePath = await this.saveRawResults(rawResults);
    await this.generateSummaryReport(processedData);
    await this.generateComparisonReport(processedData);
    await this.generateDetailedReport(processedData);
    await this.generateHTMLDashboard(processedData, rawResults);

    console.log(`Reports generated in ${this.config.reportsDir}`);
    return resultsFilePath;
  }

  /**
   * Calculates descriptive statistics for an array of numbers.
   */
  _calculateStats(data) {
    if (!data || data.length === 0) {
      return { count: 0, mean: 0, median: 0, stdev: 0, min: 0, max: 0 };
    }
    const count = data.length;
    const mean = data.reduce((a, b) => a + b, 0) / count;
    const sorted = [...data].sort((a, b) => a - b);
    const median = count % 2 === 0
      ? (sorted[count / 2 - 1] + sorted[count / 2]) / 2
      : sorted[Math.floor(count / 2)];
    const stdev = Math.sqrt(data.map(x => Math.pow(x - mean, 2)).reduce((a, b) => a + b, 0) / (count > 1 ? count - 1 : 1));
    const min = sorted[0];
    const max = sorted[count - 1];
    return { count, mean, median, stdev, min, max };
  }

  /**
   * Groups raw results by benchmark permutation and calculates stats for each group.
   */
  _processResults(rawResults) {
    const successfulResults = rawResults.filter(r => r.success);

    const grouped = successfulResults.reduce((acc, r) => {
      const key = `${r.provider}|${r.variant}|${r.taskName}`;
      if (!acc[key]) {
        acc[key] = {
          provider: r.provider,
          variant: r.variant,
          taskName: r.taskName,
          category: r.category,
          runs: [],
        };
      }
      acc[key].runs.push(r);
      return acc;
    }, {});

    return Object.values(grouped).map(group => {
      const scores = group.runs.map(r => r.evaluation.totalScore);
      const durations = group.runs.map(r => r.duration);
      // Add other metrics if they exist
      const accuracyScores = group.runs.map(r => r.evaluation.scores.accuracy);
      const performanceScores = group.runs.map(r => r.evaluation.scores.performance);
      const qualityScores = group.runs.map(r => r.evaluation.scores.codeQuality);
      const completenessScores = group.runs.map(r => r.evaluation.scores.completeness);

      return {
        ...group,
        stats: {
          score: this._calculateStats(scores),
          duration: this._calculateStats(durations),
          accuracy: this._calculateStats(accuracyScores),
          performance: this._calculateStats(performanceScores),
          codeQuality: this._calculateStats(qualityScores),
          completeness: this._calculateStats(completenessScores),
        },
      };
    });
  }

  async ensureDirectories() {
    await mkdir(this.config.resultsDir, { recursive: true });
    await mkdir(this.config.reportsDir, { recursive: true });
  }

  async saveRawResults(results) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-') ;
    const filename = `results-${timestamp}.json`;
    const filepath = join(this.config.resultsDir, filename);
    await writeFile(filepath, JSON.stringify(results, null, 2));
    console.log(`Raw results saved to ${filepath}`);
    return filepath;
  }

  /**
   * Generates a summary markdown report from processed data.
   */
  async generateSummaryReport(processedData) {
    let report = '# LLM Benchmark Summary (Statistically Analyzed)\n\n';
    report += `Generated: ${new Date().toISOString()}\n\n`;

    // Overall stats
    const overallScore = processedData.reduce((sum, r) => sum + r.stats.score.mean, 0) / processedData.length;
    const overallDuration = processedData.reduce((sum, r) => sum + r.stats.duration.mean, 0) / processedData.length;
    report += `## Overall Performance\n\n`;
    report += `- Average Score (Mean of Means): ${overallScore.toFixed(2)}/100\n`;
    report += `- Average Duration (Mean of Means): ${(overallDuration / 1000).toFixed(2)}s\n\n`;

    // By Provider
    report += `## Performance by LLM Provider\n\n`;
    const providers = [...new Set(processedData.map(r => r.provider))];
    for (const provider of providers) {
      const providerResults = processedData.filter(r => r.provider === provider);
      const providerAvg = providerResults.reduce((sum, r) => sum + r.stats.score.mean, 0) / providerResults.length;
      report += `### ${provider}\n`;
      report += `- Score: ${providerAvg.toFixed(2)}/100\n`;
      report += `- Benchmarks: ${providerResults.length}\n\n`;
    }

    // By Variant
    report += `## Performance by Language Variant\n\n`;
    const variants = [...new Set(processedData.map(r => r.variant))];
    for (const variant of variants) {
      const variantResults = processedData.filter(r => r.variant === variant);
      const variantAvg = variantResults.reduce((sum, r) => sum + r.stats.score.mean, 0) / variantResults.length;
      report += `### ${variant}\n`;
      report += `- Score: ${variantAvg.toFixed(2)}/100\n`;
      report += `- Benchmarks: ${variantResults.length}\n\n`;
    }

    const filepath = join(this.config.reportsDir, 'summary.md');
    await writeFile(filepath, report);
    console.log(`Summary report saved to ${filepath}`);
  }

  /**
   * Generates a comparison markdown report from processed data.
   */
  async generateComparisonReport(processedData) {
    let report = '# LLM Comparison Report (Statistically Analyzed)\n\n';
    const providers = [...new Set(processedData.map(r => r.provider))];
    const variants = [...new Set(processedData.map(r => r.variant))];

    report += `## Score Comparison (Mean ± StDev)\n\n`;
    report += '| Provider | ' + variants.join(' | ') + ' |\n';
    report += '|' + Array(variants.length + 1).fill('---').join('|') + '|\n';

    for (const provider of providers) {
      let row = `| ${provider} |`;
      for (const variant of variants) {
        const results = processedData.filter(r => r.provider === provider && r.variant === variant);
        if (results.length === 0) {
          row += ' N/A |';
          continue;
        }
        const avgScore = results.reduce((sum, r) => sum + r.stats.score.mean, 0) / results.length;
        const avgStdev = results.reduce((sum, r) => sum + r.stats.score.stdev, 0) / results.length;
        row += ` ${avgScore.toFixed(1)} ± ${avgStdev.toFixed(1)} |`;
      }
      report += row + '\n';
    }

    report += '\n## Detailed Criteria Comparison (Mean Score)\n\n';
    for (const variant of variants) {
        report += `### ${variant}\n\n`;
        report += '| Provider | Accuracy | Performance | Code Quality | Completeness | Total Score |\n';
        report += '|---|---|---|---|---|---|\n';
        for (const provider of providers) {
            const results = processedData.filter(r => r.provider === provider && r.variant === variant);
            if (results.length === 0) continue;
            const accuracy = results.reduce((s, r) => s + r.stats.accuracy.mean, 0) / results.length;
            const performance = results.reduce((s, r) => s + r.stats.performance.mean, 0) / results.length;
            const codeQuality = results.reduce((s, r) => s + r.stats.codeQuality.mean, 0) / results.length;
            const completeness = results.reduce((s, r) => s + r.stats.completeness.mean, 0) / results.length;
            const total = results.reduce((s, r) => s + r.stats.score.mean, 0) / results.length;
            report += `| ${provider} | ${(accuracy * 100).toFixed(1)} | ${(performance * 100).toFixed(1)} | ${(codeQuality * 100).toFixed(1)} | ${(completeness * 100).toFixed(1)} | ${total.toFixed(1)} |\n`;
        }
        report += '\n';
    }

    const filepath = join(this.config.reportsDir, 'comparison.md');
    await writeFile(filepath, report);
    console.log(`Comparison report saved to ${filepath}`);
  }

  /**
   * Generates a detailed markdown report from processed data.
   */
  async generateDetailedReport(processedData) {
    let report = '# Detailed Benchmark Results (Statistically Analyzed)\n\n';
    const tasks = [...new Set(processedData.map(r => r.taskName))];

    for (const task of tasks) {
      report += `## ${task}\n\n`;
      report += '| Provider | Variant | Runs | Mean Score | Median | StDev | Mean Duration (ms) |\n';
      report += '|---|---|---|---|---|---|---|\n';

      const taskResults = processedData.filter(r => r.taskName === task);
      for (const result of taskResults) {
        const { score, duration } = result.stats;
        report += `| ${result.provider} | ${result.variant} | ${score.count} | ${score.mean.toFixed(1)} | ${score.median.toFixed(1)} | ${score.stdev.toFixed(2)} | ${duration.mean.toFixed(0)} |\n`;
      }
      report += '\n';
    }

    const filepath = join(this.config.reportsDir, 'detailed.md');
    await writeFile(filepath, report);
    console.log(`Detailed report saved to ${filepath}`);
  }

  /**
   * Generates an interactive HTML dashboard from processed data.
   */
  async generateHTMLDashboard(processedData, rawResults) {
    const totalRuns = rawResults.length;
    const successfulRuns = rawResults.filter(r => r.success).length;
    const overallScore = processedData.reduce((sum, r) => sum + r.stats.score.mean, 0) / processedData.length;
    const overallDuration = processedData.reduce((sum, r) => sum + r.stats.duration.mean, 0) / processedData.length;

    const providers = [...new Set(processedData.map(r => r.provider))];
    const variants = [...new Set(processedData.map(r => r.variant))];
    
    const providerScores = providers.map(p => {
        const results = processedData.filter(r => r.provider === p);
        return results.reduce((sum, r) => sum + r.stats.score.mean, 0) / results.length;
    });

    const variantScores = variants.map(v => {
        const results = processedData.filter(r => r.variant === v);
        return results.reduce((sum, r) => sum + r.stats.score.mean, 0) / results.length;
    });

    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Benchmark Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    body { font-family: sans-serif; padding: 20px; background: #f9f9f9; }
    .container { max-width: 1200px; margin: auto; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }
    .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    h1, h2 { color: #333; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Benchmark Dashboard</h1>
    <div class="grid">
      <div class="card">
        <h2>Performance by Provider</h2>
        <canvas id="providerChart"></canvas>
      </div>
      <div class="card">
        <h2>Performance by Variant</h2>
        <canvas id="variantChart"></canvas>
      </div>
    </div>
  </div>
  <script>
    new Chart(document.getElementById('providerChart'), {
      type: 'bar',
      data: {
        labels: ${JSON.stringify(providers)},
        datasets: [{
          label: 'Mean Score',
          data: ${JSON.stringify(providerScores)},
          backgroundColor: 'rgba(54, 162, 235, 0.6)'
        }]
      },
      options: { scales: { y: { beginAtZero: true, max: 100 } } }
    });
    new Chart(document.getElementById('variantChart'), {
      type: 'bar',
      data: {
        labels: ${JSON.stringify(variants)},
        datasets: [{
          label: 'Mean Score',
          data: ${JSON.stringify(variantScores)},
          backgroundColor: 'rgba(75, 192, 192, 0.6)'
        }]
      },
      options: { scales: { y: { beginAtZero: true, max: 100 } } }
    });
  </script>
</body>
</html>`;

    const filepath = join(this.config.reportsDir, 'dashboard.html');
    await writeFile(filepath, html);
    console.log(`HTML dashboard saved to ${filepath}`);
  }
}