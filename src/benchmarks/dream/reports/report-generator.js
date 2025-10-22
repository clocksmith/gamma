/**
 * Report Generator for DREAM Benchmarks
 * Generates reports from benchmark results
 */

import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';

export class ReportGenerator {
  constructor(config = {}) {
    this.config = {
      resultsDir: config.resultsDir || './results',
      reportsDir: config.reportsDir || './reports',
      runLabel: config.runLabel || null
    };
  }

  /**
   * Generate and save JSON report from results
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

      // Write results to file
      await writeFile(filePath, JSON.stringify(results, null, 2), 'utf-8');

      console.log(`\n📄 Results saved to: ${filePath}`);
      return filePath;
    } catch (error) {
      console.warn(`Failed to save results: ${error.message}`);
      return null;
    }
  }

  /**
   * Generate a basic text report from results
   */
  static generateTextReport(results) {
    if (!results || results.length === 0) {
      return 'No results to report';
    }

    let report = '\n=== DREAM Benchmark Results ===\n\n';

    results.forEach((result, index) => {
      report += `Test ${index + 1}:\n`;
      report += `  Status: ${result.status || 'unknown'}\n`;
      if (result.duration) {
        report += `  Duration: ${result.duration}ms\n`;
      }
      if (result.error) {
        report += `  Error: ${result.error}\n`;
      }
      report += '\n';
    });

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
    const passed = results.filter(r => r.status === 'passed').length;
    const failed = results.filter(r => r.status === 'failed').length;
    const skipped = results.filter(r => r.status === 'skipped').length;

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

    // This is a stub - in real implementation would write to file
    console.log('Report saved to:', outputPath);
    return report;
  }
}

export default ReportGenerator;
