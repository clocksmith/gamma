/**
 * Interactive Dashboard Generator
 * Creates comprehensive HTML dashboards with charts, filtering, and drill-down navigation
 */

import { writeFile } from 'fs/promises';
import { StatisticalAnalyzer } from './statistical-analyzer.js';
import { AdvancedMetrics } from './advanced-metrics.js';

export class DashboardGenerator {
  /**
   * Generate interactive HTML dashboard
   */
  static async generate(results, outputPath, options = {}) {
    const html = this.buildHTML(results, options);
    await writeFile(outputPath, html);
    console.log(`✓ Dashboard generated: ${outputPath}`);
    return outputPath;
  }

  /**
   * Build complete HTML dashboard
   */
  static buildHTML(results, options) {
    const data = this.prepareData(results);

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Benchmark Dashboard - Codegen Suite</title>
    ${this.getStyles()}
</head>
<body>
    <div class="dashboard">
        <header class="dashboard-header">
            <h1>📊 Codegen Benchmark Dashboard</h1>
            <p class="subtitle">TS/JS Prompt Ladder Benchmarks</p>
            <div class="timestamp">Generated: ${new Date().toLocaleString()}</div>
        </header>

        ${this.buildSummarySection(data)}
        ${this.buildFilterSection(data)}
        ${this.buildChartsSection(data)}
        ${this.buildDetailedResults(data)}
        ${this.buildStatisticalAnalysis(data)}
        ${this.buildAdvancedMetrics(data)}
    </div>

    <script>${this.getJavaScript(data)}</script>
</body>
</html>`;
  }

  /**
   * Prepare and organize data for dashboard
   */
  static prepareData(results) {
    const successful = results.filter(r => r.success && r.evaluation);

    // Group by various dimensions
    const byProvider = this.groupBy(successful, 'provider');
    const byVariant = this.groupBy(successful, 'variant');
    const byTask = this.groupBy(successful, 'taskName');
    const byCategory = this.groupBy(successful, 'category');

    // Calculate statistics
    const overallStats = this.calculateGroupStats(successful);
    const providerStats = this.calculateStatsForGroups(byProvider);
    const variantStats = this.calculateStatsForGroups(byVariant);
    const taskStats = this.calculateStatsForGroups(byTask);

    return {
      results: successful,
      totalCount: results.length,
      successCount: successful.length,
      failureCount: results.length - successful.length,
      byProvider,
      byVariant,
      byTask,
      byCategory,
      overallStats,
      providerStats,
      variantStats,
      taskStats
    };
  }

  /**
   * Build summary section
   */
  static buildSummarySection(data) {
    return `
    <section class="summary-section">
        <h2>Overview</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">${data.totalCount}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat-card success">
                <div class="stat-value">${data.successCount}</div>
                <div class="stat-label">Successful</div>
            </div>
            <div class="stat-card ${data.failureCount > 0 ? 'failure' : ''}">
                <div class="stat-value">${data.failureCount}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data.overallStats.score.mean.toFixed(1)}</div>
                <div class="stat-label">Avg Score</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${(data.overallStats.duration.mean / 1000).toFixed(2)}s</div>
                <div class="stat-label">Avg Duration</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${Object.keys(data.byProvider).length}</div>
                <div class="stat-label">Providers</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${Object.keys(data.byVariant).length}</div>
                <div class="stat-label">Variants</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${Object.keys(data.byTask).length}</div>
                <div class="stat-label">Tasks</div>
            </div>
        </div>
    </section>`;
  }

  /**
   * Build filter section
   */
  static buildFilterSection(data) {
    const providers = Object.keys(data.byProvider);
    const variants = Object.keys(data.byVariant);
    const categories = Object.keys(data.byCategory);

    return `
    <section class="filter-section">
        <h2>Filters</h2>
        <div class="filters">
            <div class="filter-group">
                <label for="provider-filter">Provider:</label>
                <select id="provider-filter" onchange="applyFilters()">
                    <option value="">All</option>
                    ${providers.map(p => `<option value="${p}">${p}</option>`).join('')}
                </select>
            </div>
            <div class="filter-group">
                <label for="variant-filter">Variant:</label>
                <select id="variant-filter" onchange="applyFilters()">
                    <option value="">All</option>
                    ${variants.map(v => `<option value="${v}">${v}</option>`).join('')}
                </select>
            </div>
            <div class="filter-group">
                <label for="category-filter">Category:</label>
                <select id="category-filter" onchange="applyFilters()">
                    <option value="">All</option>
                    ${categories.map(c => `<option value="${c}">${c}</option>`).join('')}
                </select>
            </div>
            <div class="filter-group">
                <label for="score-filter">Min Score:</label>
                <input type="number" id="score-filter" min="0" max="100" placeholder="0" onchange="applyFilters()">
            </div>
            <button onclick="resetFilters()" class="btn-reset">Reset Filters</button>
        </div>
    </section>`;
  }

  /**
   * Build charts section
   */
  static buildChartsSection(data) {
    return `
    <section class="charts-section">
        <h2>Visualizations</h2>
        <div class="charts-grid">
            <div class="chart-container">
                <h3>Scores by Provider</h3>
                <canvas id="providerChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>Scores by Variant</h3>
                <canvas id="variantChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>Duration by Provider</h3>
                <canvas id="durationChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>Score Distribution</h3>
                <canvas id="distributionChart"></canvas>
            </div>
        </div>
    </section>`;
  }

  /**
   * Build detailed results table
   */
  static buildDetailedResults(data) {
    return `
    <section class="results-section">
        <h2>Detailed Results</h2>
        <div class="results-toolbar">
            <button onclick="exportToCSV()" class="btn">Export CSV</button>
            <button onclick="exportToJSON()" class="btn">Export JSON</button>
        </div>
        <div class="table-container">
            <table id="results-table" class="results-table">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">Task</th>
                        <th onclick="sortTable(1)">Provider</th>
                        <th onclick="sortTable(2)">Variant</th>
                        <th onclick="sortTable(3)">Category</th>
                        <th onclick="sortTable(4)">Score</th>
                        <th onclick="sortTable(5)">Duration (ms)</th>
                        <th onclick="sortTable(6)">Accuracy</th>
                        <th onclick="sortTable(7)">Quality</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.buildResultRows(data.results)}
                </tbody>
            </table>
        </div>
    </section>`;
  }

  /**
   * Build result table rows
   */
  static buildResultRows(results) {
    return results.map((r, idx) => {
      const score = r.evaluation.totalScore;
      const scoreClass = score >= 80 ? 'excellent' : score >= 60 ? 'good' : score >= 40 ? 'fair' : 'poor';

      return `
        <tr class="result-row" data-provider="${r.provider}" data-variant="${r.variant}" data-category="${r.category}" data-score="${score}">
            <td>${r.taskName}</td>
            <td>${r.provider}</td>
            <td>${r.variant}</td>
            <td>${r.category}</td>
            <td class="score ${scoreClass}">${score.toFixed(1)}</td>
            <td>${r.duration}</td>
            <td>${(r.evaluation.scores.accuracy * 100).toFixed(0)}%</td>
            <td>${(r.evaluation.scores.codeQuality * 100).toFixed(0)}%</td>
            <td>
                <button onclick="viewDetails(${idx})" class="btn-small">Details</button>
            </td>
        </tr>`;
    }).join('');
  }

  /**
   * Build statistical analysis section
   */
  static buildStatisticalAnalysis(data) {
    return `
    <section class="stats-section">
        <h2>Statistical Analysis</h2>
        <div class="stats-details">
            <h3>Provider Comparison</h3>
            <table class="stats-table">
                <thead>
                    <tr>
                        <th>Provider</th>
                        <th>Mean Score</th>
                        <th>Median</th>
                        <th>Std Dev</th>
                        <th>95% CI</th>
                        <th>Tests</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.buildStatsRows(data.providerStats)}
                </tbody>
            </table>

            <h3>Variant Comparison</h3>
            <table class="stats-table">
                <thead>
                    <tr>
                        <th>Variant</th>
                        <th>Mean Score</th>
                        <th>Median</th>
                        <th>Std Dev</th>
                        <th>95% CI</th>
                        <th>Tests</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.buildStatsRows(data.variantStats)}
                </tbody>
            </table>
        </div>
    </section>`;
  }

  /**
   * Build statistics table rows
   */
  static buildStatsRows(stats) {
    return Object.entries(stats).map(([name, data]) => {
      const ci = data.ci;
      return `
        <tr>
            <td><strong>${name}</strong></td>
            <td>${data.score.mean.toFixed(2)}</td>
            <td>${data.score.median.toFixed(2)}</td>
            <td>${data.score.stdDev.toFixed(2)}</td>
            <td>${ci.lower.toFixed(2)} - ${ci.upper.toFixed(2)}</td>
            <td>${data.score.count}</td>
        </tr>`;
    }).join('');
  }

  /**
   * Build advanced metrics section
   */
  static buildAdvancedMetrics(data) {
    return `
    <section class="advanced-metrics-section">
        <h2>Advanced Metrics</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>Code Quality Insights</h3>
                <p>Analyzing complexity, maintainability, and readability across all results...</p>
                <div id="quality-insights"></div>
            </div>
            <div class="metric-card">
                <h3>Performance Insights</h3>
                <p>Duration trends and outlier analysis...</p>
                <div id="performance-insights"></div>
            </div>
            <div class="metric-card">
                <h3>Type Safety Analysis</h3>
                <p>Comparing TypeScript vs JavaScript vs JSDoc...</p>
                <div id="type-safety-insights"></div>
            </div>
        </div>
    </section>`;
  }

  /**
   * CSS Styles
   */
  static getStyles() {
    return `<style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }

        .dashboard {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .dashboard-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .dashboard-header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .timestamp {
            margin-top: 15px;
            opacity: 0.8;
            font-size: 0.9em;
        }

        section {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        h2 {
            color: #2d3748;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }

        h3 {
            color: #4a5568;
            margin-bottom: 15px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
        }

        .stat-card {
            background: linear-gradient(135deg, #f6f8fb 0%, #e9ecef 100%);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            transition: transform 0.2s;
        }

        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        .stat-card.success {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        }

        .stat-card.failure {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        }

        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }

        .stat-label {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }

        .filters {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: flex-end;
        }

        .filter-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }

        .filter-group label {
            font-size: 0.9em;
            font-weight: 500;
            color: #555;
        }

        select, input[type="number"] {
            padding: 8px 12px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 1em;
            min-width: 150px;
        }

        select:focus, input:focus {
            outline: none;
            border-color: #667eea;
        }

        .btn, .btn-reset, .btn-small {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.2s;
        }

        .btn {
            background: #667eea;
            color: white;
        }

        .btn:hover {
            background: #5568d3;
        }

        .btn-reset {
            background: #e0e0e0;
            color: #333;
        }

        .btn-small {
            padding: 5px 10px;
            font-size: 0.85em;
            background: #667eea;
            color: white;
        }

        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
        }

        .chart-container {
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
        }

        .results-toolbar {
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
        }

        .table-container {
            overflow-x: auto;
        }

        .results-table {
            width: 100%;
            border-collapse: collapse;
        }

        .results-table thead {
            background: #f7fafc;
        }

        .results-table th {
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #2d3748;
            border-bottom: 2px solid #e2e8f0;
            cursor: pointer;
        }

        .results-table th:hover {
            background: #edf2f7;
        }

        .results-table td {
            padding: 12px;
            border-bottom: 1px solid #e2e8f0;
        }

        .results-table tr:hover {
            background: #f7fafc;
        }

        .score {
            font-weight: bold;
        }

        .score.excellent { color: #22c55e; }
        .score.good { color: #3b82f6; }
        .score.fair { color: #f59e0b; }
        .score.poor { color: #ef4444; }

        .stats-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }

        .stats-table th,
        .stats-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }

        .stats-table th {
            background: #f7fafc;
            font-weight: 600;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .metric-card {
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }

        @media (max-width: 768px) {
            .charts-grid {
                grid-template-columns: 1fr;
            }

            .filters {
                flex-direction: column;
                align-items: stretch;
            }
        }
    </style>`;
  }

  /**
   * JavaScript functionality
   */
  static getJavaScript(data) {
    return `
        const allResults = ${JSON.stringify(data.results)};

        function applyFilters() {
            const provider = document.getElementById('provider-filter').value;
            const variant = document.getElementById('variant-filter').value;
            const category = document.getElementById('category-filter').value;
            const minScore = parseFloat(document.getElementById('score-filter').value) || 0;

            const rows = document.querySelectorAll('.result-row');

            rows.forEach(row => {
                const matchProvider = !provider || row.dataset.provider === provider;
                const matchVariant = !variant || row.dataset.variant === variant;
                const matchCategory = !category || row.dataset.category === category;
                const matchScore = parseFloat(row.dataset.score) >= minScore;

                row.style.display = matchProvider && matchVariant && matchCategory && matchScore ? '' : 'none';
            });
        }

        function resetFilters() {
            document.getElementById('provider-filter').value = '';
            document.getElementById('variant-filter').value = '';
            document.getElementById('category-filter').value = '';
            document.getElementById('score-filter').value = '';
            applyFilters();
        }

        function sortTable(columnIndex) {
            const table = document.getElementById('results-table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            rows.sort((a, b) => {
                const aVal = a.cells[columnIndex].textContent;
                const bVal = b.cells[columnIndex].textContent;

                const aNum = parseFloat(aVal);
                const bNum = parseFloat(bVal);

                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return bNum - aNum;
                }

                return aVal.localeCompare(bVal);
            });

            rows.forEach(row => tbody.appendChild(row));
        }

        function viewDetails(index) {
            const result = allResults[index];
            alert(JSON.stringify(result, null, 2));
        }

        function exportToCSV() {
            let csv = 'Task,Provider,Variant,Category,Score,Duration,Accuracy,Quality\\n';

            allResults.forEach(r => {
                csv += [
                    r.taskName,
                    r.provider,
                    r.variant,
                    r.category,
                    r.evaluation.totalScore,
                    r.duration,
                    r.evaluation.scores.accuracy * 100,
                    r.evaluation.scores.codeQuality * 100
                ].join(',') + '\\n';
            });

            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'benchmark-results.csv';
            a.click();
        }

        function exportToJSON() {
            const json = JSON.stringify(allResults, null, 2);
            const blob = new Blob([json], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'benchmark-results.json';
            a.click();
        }
    `;
  }

  /**
   * Helper methods
   */
  static groupBy(results, key) {
    return results.reduce((groups, result) => {
      const value = result[key];
      if (!groups[value]) groups[value] = [];
      groups[value].push(result);
      return groups;
    }, {});
  }

  static calculateGroupStats(results) {
    const scores = results.map(r => r.evaluation.totalScore);
    const durations = results.map(r => r.duration);

    return {
      score: StatisticalAnalyzer.calculateStats(scores),
      duration: StatisticalAnalyzer.calculateStats(durations)
    };
  }

  static calculateStatsForGroups(groups) {
    const stats = {};

    for (const [name, results] of Object.entries(groups)) {
      const scores = results.map(r => r.evaluation.totalScore);
      stats[name] = {
        score: StatisticalAnalyzer.calculateStats(scores),
        ci: StatisticalAnalyzer.confidenceInterval(scores, 0.95)
      };
    }

    return stats;
  }
}
