#!/usr/bin/env node

/**
 * DREAM Benchmark CLI
 * Enhanced command-line interface with advanced features
 */

import { BenchmarkRunner } from './runner/benchmark-runner.js';
import { BenchmarkConfig } from './config.js';
import { PresetManager } from './presets.js';
import { HistoricalTracker } from './utils/historical-tracker.js';
import { DashboardGenerator } from './utils/dashboard-generator.js';
import { StatisticalAnalyzer } from './utils/statistical-analyzer.js';
import { AdvancedMetrics } from './utils/advanced-metrics.js';

class DreamCLI {
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
      output: './benchmark/reports/dream-dashboard.html'
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
    console.log('🚀 DREAM Benchmark Suite');
    console.log('Dynamic, Robust, Extensive, Accurate Metrics\n');

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

    console.log(`\nAnalyzing ${successfulResults.length} results...\n`);

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
      console.log(`\n--- ${variant} ---`);

      // Average complexity
      const avgComplexity = metricsArray.reduce((sum, m) =>
        sum + m.complexity.complexity, 0) / metricsArray.length;
      console.log(`Avg Cyclomatic Complexity: ${avgComplexity.toFixed(1)}`);

      // Average maintainability
      const avgMaintainability = metricsArray.reduce((sum, m) =>
        sum + m.maintainability.index, 0) / metricsArray.length;
      console.log(`Avg Maintainability Index: ${avgMaintainability.toFixed(1)}/100`);

      // Type safety score
      if (metricsArray.length > 0) {
        const avgTypeSafety = metricsArray.reduce((sum, m) =>
          sum + m.typeSafety.score, 0) / metricsArray.length;
        console.log(`Avg Type Safety Score: ${avgTypeSafety.toFixed(1)}/100`);
      }

      // Bug risk
      const avgBugRisk = metricsArray.reduce((sum, m) =>
        sum + m.bugRisk.riskScore, 0) / metricsArray.length;
      console.log(`Avg Bug Risk Score: ${avgBugRisk.toFixed(1)}`);
    }
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

    console.log('Usage: dream-cli.js run --preset <preset-name>');
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
DREAM Benchmark CLI - Dynamic, Robust, Extensive, Accurate Metrics

USAGE:
  dream-cli.js <command> [options]

COMMANDS:
  run              Run benchmarks (default)
  presets          List available presets
  history          Show benchmark history
  compare          Compare recent results
  analyze          Analyze trends
  help             Show this help

OPTIONS:
  --preset, -p <name>        Use a benchmark preset
  --provider <name>          Run only specified provider(s)
  --variant, -v <name>       Run only specified variant(s)
  --category, -c <name>      Run only specified category(s)
  --task, -t <name>          Run only specified task
  --runs, -r <n>             Number of runs per test
  --timeout <ms>             Timeout per test in milliseconds
  --compare                  Compare with historical baseline
  --historical               Save results to history
  --advanced-metrics, -am    Compute advanced code metrics
  --no-dashboard             Skip dashboard generation
  --output, -o <path>        Output path for dashboard
  --dry-run, --mock          Use mock LLM responses
  --quiet, -q                Suppress verbose output
  --help, -h                 Show this help

EXAMPLES:
  # Quick test with preset
  dream-cli.js run --preset quick

  # Comprehensive test with history tracking
  dream-cli.js run --preset comprehensive --historical --compare

  # Custom configuration
  dream-cli.js run --variant typescript --provider openai-gpt4 --runs 5

  # Advanced analysis
  dream-cli.js run --preset quality --advanced-metrics

  # Compare historical results
  dream-cli.js compare

  # Analyze trends
  dream-cli.js analyze

AVAILABLE PRESETS:
  quick              Fast smoke test
  comprehensive      Full test suite
  performance        Speed-focused tests
  quality            Quality-focused tests
  typeSafety         TypeScript vs JavaScript comparison
  providerComparison Compare LLM providers
  stress             Large, complex tasks
  regression         Regression testing
  costOptimized      Balance cost and performance
  webComponents      Web component testing
  ci                 CI/CD pipeline tests

For more information, visit: https://github.com/yourusername/dream-benchmark
`);
  }
}

// Run CLI
if (import.meta.url === `file://${process.argv[1]}`) {
  const cli = new DreamCLI();
  cli.run().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export { DreamCLI };
