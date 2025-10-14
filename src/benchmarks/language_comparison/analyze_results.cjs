#!/usr/bin/env node

/**
 * Benchmark Results Analyzer (JavaScript/Node.js version)
 * Analyzes and visualizes LLM benchmark results with detailed metrics
 */

const fs = require('fs');
const path = require('path');

class BenchmarkAnalyzer {
  constructor(resultsFile) {
    this.resultsFile = resultsFile;
    this.results = this.loadResults();
  }

  loadResults() {
    const data = fs.readFileSync(this.resultsFile, 'utf8');
    return JSON.parse(data);
  }

  printSummary() {
    console.log('\n' + '='.repeat(80));
    console.log(`BENCHMARK RESULTS ANALYSIS: ${path.basename(this.resultsFile)}`);
    console.log('='.repeat(80) + '\n');

    const successful = this.results.filter(r => r.success);
    const failed = this.results.filter(r => !r.success);

    console.log('📊 Overview:');
    console.log(`   Total Runs: ${this.results.length}`);
    console.log(`   ✓ Successful: ${successful.length}`);
    console.log(`   ✗ Failed: ${failed.length}`);
    console.log(`   Success Rate: ${(successful.length / this.results.length * 100).toFixed(1)}%\n`);

    if (successful.length === 0) {
      console.log('⚠️  No successful results to analyze\n');
      return;
    }

    this.printPerformanceMetrics(successful);
    this.printProviderComparison(successful);
    this.printVariantComparison(successful);
    this.printDetailedMetrics(successful);
  }

  printPerformanceMetrics(results) {
    console.log('⚡ Performance Metrics:');

    const avgDuration = results.reduce((sum, r) => sum + r.duration, 0) / results.length / 1000;

    const withMetrics = results.filter(r => r.evaluation?.metrics);
    if (withMetrics.length > 0) {
      const avgTokensPerSec = withMetrics.reduce((sum, r) =>
        sum + r.evaluation.metrics.tokenMetrics.tokensPerSecond, 0) / withMetrics.length;

      const avgOutputTokens = withMetrics.reduce((sum, r) =>
        sum + r.evaluation.metrics.tokenMetrics.outputTokens, 0) / withMetrics.length;

      const avgCodeLines = withMetrics.reduce((sum, r) =>
        sum + r.evaluation.metrics.codeLength.codeLines, 0) / withMetrics.length;

      console.log(`   Average Duration: ${avgDuration.toFixed(2)}s`);
      console.log(`   Average Tokens/Second: ${avgTokensPerSec.toFixed(2)}`);
      console.log(`   Average Output Tokens: ${avgOutputTokens.toFixed(0)}`);
      console.log(`   Average Code Lines: ${avgCodeLines.toFixed(1)}`);
    } else {
      console.log(`   Average Duration: ${avgDuration.toFixed(2)}s`);
    }
    console.log();
  }

  printProviderComparison(results) {
    console.log('🤖 Provider Comparison:');

    const providers = {};
    results.forEach(r => {
      if (!providers[r.provider]) providers[r.provider] = [];
      providers[r.provider].push(r);
    });

    const headers = ['Provider', 'Runs', 'Avg Time', 'Tok/s', 'Lines', 'Tokens'];
    const colWidths = [20, 6, 10, 8, 7, 8];

    // Print header
    const headerRow = headers.map((h, i) => h.padEnd(colWidths[i])).join(' | ');
    console.log(`   ${headerRow}`);
    console.log(`   ${'-'.repeat(headerRow.length)}`);

    // Print each provider
    Object.entries(providers).sort().forEach(([provider, providerResults]) => {
      const avgTime = providerResults.reduce((sum, r) => sum + r.duration, 0) / providerResults.length / 1000;

      const withMetrics = providerResults.filter(r => r.evaluation?.metrics);
      let row;
      if (withMetrics.length > 0) {
        const avgTps = withMetrics.reduce((sum, r) =>
          sum + r.evaluation.metrics.tokenMetrics.tokensPerSecond, 0) / withMetrics.length;
        const avgLines = withMetrics.reduce((sum, r) =>
          sum + r.evaluation.metrics.codeLength.codeLines, 0) / withMetrics.length;
        const avgTokens = withMetrics.reduce((sum, r) =>
          sum + r.evaluation.metrics.tokenMetrics.outputTokens, 0) / withMetrics.length;

        row = [
          provider.substring(0, 19),
          providerResults.length.toString(),
          `${avgTime.toFixed(2)}s`,
          avgTps.toFixed(1),
          avgLines.toFixed(1),
          avgTokens.toFixed(0)
        ];
      } else {
        row = [provider.substring(0, 19), providerResults.length.toString(),
               `${avgTime.toFixed(2)}s`, 'N/A', 'N/A', 'N/A'];
      }

      console.log(`   ${row.map((r, i) => r.padEnd(colWidths[i])).join(' | ')}`);
    });
    console.log();
  }

  printVariantComparison(results) {
    console.log('📝 Variant Comparison:');

    const variants = {};
    results.forEach(r => {
      if (!variants[r.variant]) variants[r.variant] = [];
      variants[r.variant].push(r);
    });

    const headers = ['Variant', 'Runs', 'Avg Time', 'Lines', 'Chars', 'Comments', 'Chars/Tok'];
    const colWidths = [20, 6, 10, 7, 7, 9, 10];

    // Print header
    const headerRow = headers.map((h, i) => h.padEnd(colWidths[i])).join(' | ');
    console.log(`   ${headerRow}`);
    console.log(`   ${'-'.repeat(headerRow.length)}`);

    // Print each variant
    Object.entries(variants).sort().forEach(([variant, variantResults]) => {
      const avgTime = variantResults.reduce((sum, r) => sum + r.duration, 0) / variantResults.length / 1000;

      const withMetrics = variantResults.filter(r => r.evaluation?.metrics);
      let row;
      if (withMetrics.length > 0) {
        const avgLines = withMetrics.reduce((sum, r) =>
          sum + r.evaluation.metrics.codeLength.codeLines, 0) / withMetrics.length;
        const avgChars = withMetrics.reduce((sum, r) =>
          sum + r.evaluation.metrics.codeLength.totalCharacters, 0) / withMetrics.length;
        const avgComments = withMetrics.reduce((sum, r) =>
          sum + r.evaluation.metrics.codeLength.commentLines, 0) / withMetrics.length;
        const avgCharsPerTok = withMetrics.reduce((sum, r) =>
          sum + parseFloat(r.evaluation.metrics.tokenMetrics.charactersPerToken), 0) / withMetrics.length;

        row = [
          variant.substring(0, 19),
          variantResults.length.toString(),
          `${avgTime.toFixed(2)}s`,
          avgLines.toFixed(1),
          avgChars.toFixed(0),
          avgComments.toFixed(1),
          avgCharsPerTok.toFixed(2)
        ];
      } else {
        row = [variant.substring(0, 19), variantResults.length.toString(),
               `${avgTime.toFixed(2)}s`, 'N/A', 'N/A', 'N/A', 'N/A'];
      }

      console.log(`   ${row.map((r, i) => r.padEnd(colWidths[i])).join(' | ')}`);
    });
    console.log();
  }

  printDetailedMetrics(results) {
    console.log('📋 Detailed Results:');

    results.forEach((result, i) => {
      console.log(`\n   [${i + 1}] ${result.provider} - ${result.variant} - ${result.taskName}`);
      console.log(`       Duration: ${(result.duration / 1000).toFixed(2)}s`);

      const metrics = result.evaluation?.metrics;
      if (metrics) {
        const tokenMetrics = metrics.tokenMetrics;
        const codeMetrics = metrics.codeLength;

        console.log(`       Code: ${codeMetrics.codeLines} lines, ` +
                   `${codeMetrics.totalCharacters} chars, ` +
                   `${codeMetrics.commentLines} comment lines`);
        console.log(`       Tokens: ${tokenMetrics.outputTokens} output, ` +
                   `${tokenMetrics.tokensPerSecond.toFixed(2)} tok/s, ` +
                   `${tokenMetrics.charactersPerToken} chars/tok`);
      }

      const scores = result.evaluation?.scores || {};
      if (Object.keys(scores).length > 0) {
        console.log(`       Scores: Accuracy=${(scores.accuracy || 0) * 100}%, ` +
                   `Quality=${(scores.codeQuality || 0) * 100}%, ` +
                   `Complete=${(scores.completeness || 0) * 100}%`);
      }
    });
    console.log();
  }

  exportCSV(outputFile) {
    if (!outputFile) {
      outputFile = this.resultsFile.replace('.json', '.csv');
    }

    const lines = [
      'provider,variant,task,duration_s,tokens_per_sec,code_lines,output_tokens,' +
      'total_chars,comment_lines,chars_per_token,accuracy,quality,completeness'
    ];

    this.results.forEach(r => {
      if (!r.success) return;

      const metrics = r.evaluation?.metrics || {};
      const scores = r.evaluation?.scores || {};

      if (Object.keys(metrics).length > 0) {
        const tokenM = metrics.tokenMetrics || {};
        const codeM = metrics.codeLength || {};

        lines.push([
          r.provider,
          r.variant,
          r.taskName,
          (r.duration / 1000).toFixed(2),
          (tokenM.tokensPerSecond || 0).toFixed(2),
          codeM.codeLines || 0,
          tokenM.outputTokens || 0,
          codeM.totalCharacters || 0,
          codeM.commentLines || 0,
          tokenM.charactersPerToken || 0,
          scores.accuracy || 0,
          scores.codeQuality || 0,
          scores.completeness || 0
        ].join(','));
      }
    });

    fs.writeFileSync(outputFile, lines.join('\n'));
    console.log(`✓ Exported to: ${outputFile}\n`);
  }
}

// Main
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('Usage: node analyze_results.js <results-file.json> [--csv]');
    console.log('\nExample:');
    console.log('  node analyze_results.js benchmark/results/results-2025-10-14T17-31-53-729Z.json');
    console.log('  node analyze_results.js benchmark/results/results-*.json --csv');
    process.exit(1);
  }

  let resultsFile = args[0];
  const exportCSV = args.includes('--csv');

  // Support getting the most recent file
  if (resultsFile.includes('*')) {
    const dir = path.dirname(resultsFile);
    const pattern = path.basename(resultsFile).replace('*', '');
    const files = fs.readdirSync(dir)
      .filter(f => f.includes(pattern))
      .sort()
      .reverse();

    if (files.length === 0) {
      console.error(`Error: No files matching ${resultsFile}`);
      process.exit(1);
    }

    resultsFile = path.join(dir, files[0]);
    console.log(`Using most recent: ${resultsFile}\n`);
  }

  const analyzer = new BenchmarkAnalyzer(resultsFile);
  analyzer.printSummary();

  if (exportCSV) {
    analyzer.exportCSV();
  }
}

module.exports = BenchmarkAnalyzer;
