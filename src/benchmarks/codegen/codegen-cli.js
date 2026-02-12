#!/usr/bin/env node

/**
 * Codegen Benchmark CLI
 * Enhanced command-line interface with advanced features
 */

import { BenchmarkRunner } from './runner/benchmark-runner.js';
import { BenchmarkConfig } from './config.js';
import { PresetManager } from './presets.js';
import { HistoricalTracker } from './utils/historical-tracker.js';
import { DashboardGenerator } from './utils/dashboard-generator.js';
import { StatisticalAnalyzer } from './utils/statistical-analyzer.js';
import { AdvancedMetrics } from './utils/advanced-metrics.js';

class CodegenCLI {
  constructor() {
    this.args = process.argv.slice(2);
    this.options = this.parseArgs();
  }

  parseArgs() {
    const options = {
      command: 'run',
      preset: null,
      providers: [],
      variants: [],
      categories: [],
      task: null,
      runs: null,
      timeout: null,
      compare: false,
      dashboard: true,
      historical: false,
      advancedMetrics: false,
      dryRun: false,
      verbose: true,
      output: './benchmark/reports/codegen-dashboard.html'
    };

    for (let i = 0; i < this.args.length; i++) {
      const arg = this.args[i];

      switch (arg) {
        case 'run':
          options.command = 'run';
          break;
        case 'presets':
          options.command = 'presets';
          break;
        case 'history':
          options.command = 'history';
          break;
        case 'compare':
          options.command = 'compare';
          break;
        case 'analyze':
          options.command = 'analyze';
          break;

        case '--preset':
        case '-p':
          options.preset = this.args[++i];
          break;

        case '--provider':
          options.providers.push(this.args[++i]);
          break;

        case '--variant':
        case '-v':
          options.variants.push(this.args[++i]);
          break;

        case '--category':
        case '-c':
          options.categories.push(this.args[++i]);
          break;

        case '--task':
        case '-t':
          options.task = this.args[++i];
          break;

        case '--runs':
        case '-r':
          options.runs = parseInt(this.args[++i], 10);
          break;

        case '--timeout':
          options.timeout = parseInt(this.args[++i], 10);
          break;

        case '--compare':
          options.compare = true;
          break;

        case '--no-dashboard':
          options.dashboard = false;
          break;

        case '--historical':
          options.historical = true;
          break;

        case '--advanced-metrics':
        case '-am':
          options.advancedMetrics = true;
          break;

        case '--dry-run':
        case '--mock':
          options.dryRun = true;
          break;

        case '--quiet':
        case '-q':
          options.verbose = false;
          break;

        case '--output':
        case '-o':
          options.output = this.args[++i];
          break;

        case '--help':
        case '-h':
          options.command = 'help';
          break;

        default:
          if (!arg.startsWith('-')) {
            options.command = arg;
          }
      }
    }

    return options;
  }

  async run() {
    try {
      switch (this.options.command) {
        case 'run':
          await this.runBenchmarks();
          break;

        case 'presets':
          this.listPresets();
          break;

        case 'history':
          await this.showHistory();
          break;

        case 'compare':
          await this.compareResults();
          break;

        case 'analyze':
          await this.analyzeResults();
          break;

        case 'help':
        default:
          this.showHelp();
          break;
      }
    } catch (error) {
      console.error('Error:', error.message);
      if (this.options.verbose) {
        console.error(error.stack);
      }
      process.exit(1);
    }
  }

  async runBenchmarks() {
    console.log('🚀 Codegen Benchmark Suite');
    console.log('TS/JS Prompt Ladder Benchmarks\n');

    // Apply preset if specified
    let config = { ...BenchmarkConfig };
    if (this.options.preset) {
      console.log(`📋 Using preset: ${this.options.preset}`);
      config = PresetManager.applyPreset(config, this.options.preset);

      // Show estimates
      const report = PresetManager.generatePresetReport(this.options.preset);
      if (report) {
        console.log(`⏱️  Estimated runtime: ${report.runtime.estimatedTimeMinutes} minutes`);
        console.log(`💰 Estimated cost: $${report.cost.estimatedCost}\n`);
      }
    }

    // Apply CLI overrides
    if (this.options.runs) config.runs = this.options.runs;
    if (this.options.timeout) config.timeout = this.options.timeout;
    if (this.options.dryRun) config.dryRun = true;
    if (this.options.providers.length > 0) {
      config.providers = config.providers.filter(p =>
        this.options.providers.includes(p.name)
      );
    }
    if (this.options.variants.length > 0) {
      config.variants = this.options.variants;
    }

    // Initialize runner
    const runner = new BenchmarkRunner(config);

    // Build filters
    const filters = {};
    if (this.options.categories.length > 0) {
      filters.categories = this.options.categories;
    }
    if (this.options.task) {
      filters.taskName = this.options.task;
    }

    // Run benchmarks
    const results = await runner.run(filters);

    // Save to history
    if (this.options.historical) {
      console.log('\n💾 Saving to history...');
      const tracker = new HistoricalTracker();
      await tracker.saveResults(results, {
        preset: this.options.preset,
        cli_options: this.options
      });
    }

    // Compare with baseline
    if (this.options.compare) {
      console.log('\n📊 Comparing with historical baseline...');
      const tracker = new HistoricalTracker();
      const comparison = await tracker.compareWithBaseline(results);

      if (comparison.hasBaseline) {
        if (comparison.regressions.length > 0) {
          console.log(tracker.generateRegressionReport(comparison.regressions));
        } else {
          console.log('✓ No regressions detected');
        }
      }
    }

    // Generate dashboard
    if (this.options.dashboard) {
      console.log('\n🎨 Generating interactive dashboard...');
      await DashboardGenerator.generate(results, this.options.output);
      console.log(`✓ Dashboard: ${this.options.output}`);
    }

    // Advanced metrics
    if (this.options.advancedMetrics) {
      console.log('\n🔬 Computing advanced metrics...');
      await this.computeAdvancedMetrics(results);
    }

    console.log('\n✅ Benchmark complete!');
  }

  async computeAdvancedMetrics(results) {
    const successfulResults = results.filter(r => r.success && r.response);

    if (successfulResults.length === 0) {
      console.log('No successful results to analyze');
      return;
    }

    console.log('\n╔══════════════════════════════════════════════════════════════════════════════╗');
    console.log('║                      ADVANCED METRICS ANALYSIS                                ║');
    console.log('╚══════════════════════════════════════════════════════════════════════════════╝\n');
    console.log(`Analyzing ${successfulResults.length} successful results...\n`);

    // Analyze by variant
    const byVariant = {};
    for (const result of successfulResults) {
      if (!byVariant[result.variant]) {
        byVariant[result.variant] = [];
      }

      // Extract code from response
      const code = result.evaluation?.details?.code || '';
      if (code) {
        const metrics = AdvancedMetrics.analyzeCode(code, result.variant);
        byVariant[result.variant].push(metrics);
      }
    }

    // Print summary for each variant
    for (const [variant, metricsArray] of Object.entries(byVariant)) {
      console.log(`\n🔍 ${variant}`);
      console.log('─'.repeat(78));

      if (metricsArray.length === 0) {
        console.log('   No code samples to analyze');
        continue;
      }

      // Complexity metrics
      const avgComplexity = metricsArray.reduce((sum, m) => sum + m.complexity.complexity, 0) / metricsArray.length;
      const complexityRating = metricsArray[0].complexity.rating;
      console.log(`\n   Cyclomatic Complexity:`);
      console.log(`      Average:  ${avgComplexity.toFixed(1)} (${complexityRating})`);
      console.log(`      Range:    ${Math.min(...metricsArray.map(m => m.complexity.complexity))} - ${Math.max(...metricsArray.map(m => m.complexity.complexity))}`);

      // Maintainability
      const avgMaintainability = metricsArray.reduce((sum, m) => sum + m.maintainability.index, 0) / metricsArray.length;
      const maintRating = metricsArray[0].maintainability.rating;
      console.log(`\n   Maintainability Index:`);
      console.log(`      Score:    ${avgMaintainability.toFixed(1)}/100 (${maintRating})`);
      console.log(`      LOC:      ${Math.round(metricsArray.reduce((sum, m) => sum + m.maintainability.components.linesOfCode, 0) / metricsArray.length)} avg lines`);

      // Type safety
      const avgTypeSafety = metricsArray.reduce((sum, m) => sum + m.typeSafety.score, 0) / metricsArray.length;
      console.log(`\n   Type Safety:`);
      console.log(`      Score:    ${avgTypeSafety.toFixed(1)}/100`);
      if (variant.includes('typescript')) {
        const avgTypeAnnotations = metricsArray.reduce((sum, m) => sum + m.typeSafety.details.typeAnnotationCoverage, 0) / metricsArray.length;
        console.log(`      Coverage: ${avgTypeAnnotations.toFixed(1)} type annotations avg`);
      }

      // Readability
      const avgReadability = metricsArray.reduce((sum, m) => sum + m.readability.score, 0) / metricsArray.length;
      const readRating = metricsArray[0].readability.rating;
      console.log(`\n   Readability:`);
      console.log(`      Score:    ${avgReadability.toFixed(1)}/100 (${readRating})`);
      const avgLineLength = metricsArray.reduce((sum, m) => sum + parseFloat(m.readability.metrics.avgLineLength), 0) / metricsArray.length;
      console.log(`      Avg Line: ${avgLineLength.toFixed(1)} chars`);

      // Bug risk
      const avgBugRisk = metricsArray.reduce((sum, m) => sum + m.bugRisk.riskScore, 0) / metricsArray.length;
      const riskLevel = metricsArray[0].bugRisk.riskLevel;
      const totalIssues = metricsArray.reduce((sum, m) => sum + m.bugRisk.issueCount, 0);
      console.log(`\n   Bug Risk:`);
      console.log(`      Score:    ${avgBugRisk.toFixed(1)} (${riskLevel} risk)`);
      console.log(`      Issues:   ${totalIssues} total across all samples`);

      // Test coverage
      const avgTestCoverage = metricsArray.reduce((sum, m) => sum + m.testCoverage.estimatedCoverage, 0) / metricsArray.length;
      const testRating = metricsArray[0].testCoverage.rating;
      console.log(`\n   Test Coverage (estimated):`);
      console.log(`      Score:    ${avgTestCoverage.toFixed(1)}% (${testRating})`);
      console.log(`      Has Tests: ${metricsArray.filter(m => m.testCoverage.hasTests).length}/${metricsArray.length} samples`);

      // Code duplication
      const avgDuplication = metricsArray.reduce((sum, m) =>
        sum + parseFloat(m.duplication.duplicationRatio), 0) / metricsArray.length;
      const dupRating = metricsArray[0].duplication.rating;
      console.log(`\n   Code Duplication:`);
      console.log(`      Ratio:    ${avgDuplication.toFixed(2)}% (${dupRating})`);

      // Dependencies
      const avgDeps = metricsArray.reduce((sum, m) => sum + m.dependencies.total, 0) / metricsArray.length;
      const depComplexity = metricsArray[0].dependencies.complexity;
      console.log(`\n   Dependencies:`);
      console.log(`      Average:  ${avgDeps.toFixed(1)} imports (${depComplexity})`);
    }

    console.log('\n' + '═'.repeat(78) + '\n');
  }

  listPresets() {
    console.log('📋 Available Benchmark Presets\n');

    const presets = PresetManager.listPresets();

    for (const preset of presets) {
      console.log(`${preset.key}`);
      console.log(`  ${preset.name}`);
      console.log(`  ${preset.description}`);

      const report = PresetManager.generatePresetReport(preset.key);
      if (report) {
        console.log(`  Runtime: ~${report.runtime.estimatedTimeMinutes} min | Cost: ~$${report.cost.estimatedCost}`);
      }
      console.log();
    }

    console.log('Usage: codegen-cli.js run --preset <preset-name>');
  }

  async showHistory() {
    console.log('📜 Benchmark History\n');

    const tracker = new HistoricalTracker();
    const history = await tracker.loadHistory();

    if (history.length === 0) {
      console.log('No historical data found');
      return;
    }

    console.log(`Found ${history.length} benchmark runs:\n`);

    for (const entry of history.slice(-10)) {
      const date = new Date(entry.timestamp).toLocaleString();
      const summary = entry.summary;

      console.log(`${date}`);
      console.log(`  Tests: ${summary.successful}/${summary.count} successful`);
      if (summary.scores) {
        console.log(`  Avg Score: ${summary.scores.mean.toFixed(1)}`);
      }
      console.log(`  Commit: ${entry.metadata.git_commit?.substring(0, 8) || 'unknown'}`);
      console.log();
    }
  }

  async compareResults() {
    console.log('📊 Comparing Recent Results\n');

    const tracker = new HistoricalTracker();
    const history = await tracker.loadHistory();

    if (history.length < 2) {
      console.log('Need at least 2 historical runs for comparison');
      return;
    }

    // Compare last two runs
    const latest = history[history.length - 1];
    const previous = history[history.length - 2];

    console.log(`Comparing:`);
    console.log(`  Latest: ${new Date(latest.timestamp).toLocaleString()}`);
    console.log(`  Previous: ${new Date(previous.timestamp).toLocaleString()}\n`);

    const comparison = await tracker.compareResults(latest.results, [previous]);

    for (const comp of comparison.slice(0, 10)) {
      console.log(`${comp.taskName} (${comp.variant})`);
      console.log(`  Score: ${comp.current.score.mean.toFixed(1)} -> ${comp.comparison.scoreChange.trend}`);
      console.log(`  Duration: ${comp.current.duration.mean.toFixed(0)}ms -> ${comp.comparison.durationChange.trend}`);
      console.log();
    }
  }

  async analyzeResults() {
    console.log('🔬 Advanced Results Analysis\n');

    const tracker = new HistoricalTracker();
    const trendAnalysis = await tracker.analyzeTrends('score', 'variant');

    if (!trendAnalysis.hasEnoughData) {
      console.log(trendAnalysis.message);
      return;
    }

    console.log(`Analysis period: ${trendAnalysis.period.dataPoints} runs\n`);

    for (const [variant, analysis] of Object.entries(trendAnalysis.trends)) {
      console.log(analysis.summary);
      if (analysis.trend) {
        console.log(`  Slope: ${analysis.trend.slope.toFixed(3)}`);
        console.log(`  R²: ${analysis.trend.rSquared.toFixed(3)}`);
        console.log(`  Change: ${analysis.trend.percentChange.toFixed(1)}%`);
      }
      console.log();
    }
  }

  showHelp() {
    console.log(`
╔══════════════════════════════════════════════════════════════════════════════╗
║                        Codegen Benchmark CLI                                  ║
║                    TS/JS Prompt Ladder Benchmarks                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

USAGE:
  codegen-cli.js <command> [options]

COMMANDS:
  run              Run benchmarks (default)
  presets          List available presets
  history          Show benchmark history
  compare          Compare recent results
  analyze          Analyze trends
  help             Show this help

OPTIONS:
  --preset, -p <name>        Use a benchmark preset
  --provider <name>          Run only specified provider(s) (multiple allowed)
  --variant, -v <name>       Run only specified variant(s) (multiple allowed)
  --category, -c <name>      Run only specified category(s) (multiple allowed)
  --task, -t <name>          Run only specified task
  --runs, -r <n>             Number of runs per test (default: 1)
  --timeout <ms>             Timeout per test in milliseconds (default: 30000)
  --compare                  Compare with historical baseline
  --historical               Save results to history database
  --advanced-metrics, -am    Compute advanced code metrics (see below)
  --no-dashboard             Skip dashboard generation
  --output, -o <path>        Output path for dashboard (default: ./reports/codegen-dashboard.html)
  --dry-run, --mock          Use mock LLM responses (no API calls)
  --quiet, -q                Suppress verbose output
  --help, -h                 Show this help

METRICS CALCULATED:

  📊 Core Scores:
     • Total Score (0-100)      - Weighted combination of all metrics
     • Accuracy (0-1)           - Correctness of generated code
     • Code Quality (0-1)       - Overall code quality assessment
     • Completeness (0-1)       - How complete the solution is
     • Auto-Rater (0-1)         - AI-based quality assessment

  🔬 Advanced Metrics (--advanced-metrics flag):
     • Cyclomatic Complexity    - Code path complexity (1-50+)
     • Maintainability Index    - Ease of maintenance (0-100)
     • Halstead Volume          - Code complexity measure
     • Type Safety Score        - TypeScript/JSDoc type coverage (0-100)
     • Readability Score        - Code readability (0-100)
     • Bug Risk Score           - Potential bug indicators (0-100)
     • Test Coverage            - Estimated test coverage (0-100)
     • Code Duplication         - Duplicate code percentage
     • Dependency Complexity    - Import/require complexity

  ⏱️  Performance Metrics:
     • Duration (ms)            - Time to generate code
     • Token Usage              - Prompt, completion, and total tokens
     • Estimated Cost           - Approximate API cost

  📈 Statistical Analysis:
     • Mean, Median, Std Dev    - Score distributions
     • 95% Confidence Intervals - Statistical confidence
     • Provider Comparison      - Model performance comparison
     • Variant Comparison       - Language variant comparison
     • Historical Trends        - Performance over time

EXAMPLES:
  # Quick test with default settings
  codegen-cli.js run --preset quick

  # Comprehensive test with history tracking and advanced metrics
  codegen-cli.js run --preset comprehensive --historical --compare --advanced-metrics

  # Custom configuration (TypeScript only, specific provider)
  codegen-cli.js run --variant typescript-expert --provider openai-gpt4 --runs 5

  # Advanced analysis with all metrics
  codegen-cli.js run --preset quality --advanced-metrics --output ./my-results.html

  # Compare historical results
  codegen-cli.js compare

  # Analyze trends over time
  codegen-cli.js analyze

  # Run specific category with multiple variants
  codegen-cli.js run --category algorithms --variant typescript-expert --variant javascript-beginner

AVAILABLE PRESETS:
  quick              Fast smoke test (2-3 min, ~$0.10)
  comprehensive      Full test suite (15-20 min, ~$1.50)
  performance        Speed-focused tests (5 min, ~$0.30)
  quality            Quality-focused tests (10 min, ~$0.80)
  typeSafety         TypeScript vs JavaScript comparison (8 min, ~$0.50)
  providerComparison Compare LLM providers (12 min, ~$1.00)
  stress             Large, complex tasks (20 min, ~$2.00)
  regression         Regression testing (10 min, ~$0.60)
  costOptimized      Balance cost and performance (6 min, ~$0.25)
  webComponents      Web component testing (8 min, ~$0.40)
  ci                 CI/CD pipeline tests (5 min, ~$0.20)

DEFAULTS:
  • Dashboard:     Enabled (disable with --no-dashboard)
  • Verbose:       Enabled (disable with --quiet)
  • Runs:          1 per test (increase with --runs)
  • Timeout:       30000ms per test (adjust with --timeout)
  • Output:        ./benchmark/reports/codegen-dashboard.html

OUTPUT FILES:
  • Dashboard:     Interactive HTML report with charts
  • Results JSON:  Raw benchmark data (./results/<timestamp>/results.json)
  • Generated Code: ./results/<timestamp>/src/*.js|ts
  • History DB:    ./benchmark/history/benchmark_history.json (if --historical)

For more information: see the repo README.
`);
  }
}

// Run CLI
if (import.meta.url === `file://${process.argv[1]}`) {
  const cli = new CodegenCLI();
  cli.run().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export { CodegenCLI };
