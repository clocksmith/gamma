/**
 * Main Benchmark Runner
 * Orchestrates running benchmarks across different LLMs and language variants
 */

import { readdir, readFile } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';
import { BenchmarkConfig } from '../config.js';
import { LLMClient } from './llm-client.js';
import { MockLLMClient } from './mock-llm-client.js';
import { Evaluator } from '../evaluator/evaluator.js';
import { ReportGenerator } from '../reports/report-generator.js';
import { PlaywrightEvaluator } from '../evaluator/playwright-evaluator.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export class BenchmarkRunner {
  constructor(config = BenchmarkConfig) {
    this.config = config;
    this.llmClient = config.dryRun
      ? new MockLLMClient(config.providers)
      : new LLMClient(config.providers);
    this.playwrightEvaluator = new PlaywrightEvaluator(config.playwrightConfig, { reportsDir: config.reportsDirectory });
    this.evaluator = new Evaluator(config.evaluation, this.playwrightEvaluator);
    this.reportGenerator = new ReportGenerator({ 
      resultsDir: config.resultsDirectory, 
      reportsDir: config.reportsDirectory 
    });
    this.results = [];
  }

  runPythonVisualizer(resultsFilePath) {
    console.log('\n🐍 Running Python visualizer...');
    try {
      const command = `python3 benchmark/analyze_results.py \"${resultsFilePath}\" --visualize --reports-dir ${this.config.reportsDirectory}`;
      execSync(command, { stdio: 'inherit' });
      console.log('✓ Python visualization complete.');
    } catch (error) {
      console.warn(`
⚠️  Python visualization failed. 
    Error: ${error.message}
    Please ensure you have Python 3 installed, along with the required libraries in benchmark/requirements.txt (pip install -r benchmark/requirements.txt)`);
    }
  }

  /**
   * Load all benchmark tasks from the tasks directory
   */
  async loadTasks() {
    const tasks = [];
    const tasksDir = join(__dirname, '../tasks');

    for (const [category, categoryConfig] of Object.entries(this.config.categories)) {
      if (!categoryConfig.enabled) continue;

      const categoryPath = join(tasksDir, category);
      try {
        const files = await readdir(categoryPath);

        for (const file of files) {
          if (file.endsWith('.json')) {
            const taskPath = join(categoryPath, file);
            const taskData = JSON.parse(await readFile(taskPath, 'utf-8'));
            tasks.push({
              ...taskData,
              category,
              weight: categoryConfig.weight,
              timeout: categoryConfig.timeout
            });
          }
        }
      } catch (err) {
        console.warn(`Warning: Could not load tasks from ${category}: ${err.message}`);
      }
    }

    return tasks;
  }

  /**
   * Run a single benchmark task multiple times as configured.
   */
  async runTask(task, provider, variant) {
    const allRunResults = [];
    for (let i = 1; i <= this.config.runs; i++) {
      const result = await this._executeSingleRun(task, provider, variant, i);
      allRunResults.push(result);
    }
    this.results.push(...allRunResults);
  }

  /**
   * Executes a single benchmark run. Internal method.
   */
  async _executeSingleRun(task, provider, variant, runNumber) {
    const startTime = Date.now();
    const runIdentifier = this.config.runs > 1 ? ` [Run ${runNumber}/${this.config.runs}]` : '';
    console.log(`\n[${provider.name}] [${variant}]${runIdentifier} Running: ${task.name}`);

    try {
      const prompt = task.variants[variant];
      if (!prompt) {
        if (this.config.output.verbose) {
          console.log(`  → Skipping ${variant} (not defined for this task)`);
        }
        return {
          taskName: task.name,
          category: task.category,
          provider: provider.name,
          variant,
          run: runNumber,
          duration: 0,
          error: `Variant not defined for this task`,
          timestamp: new Date().toISOString(),
          success: false,
          skipped: true
        };
      }

      const response = await Promise.race([
        this.llmClient.complete(provider, prompt),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Timeout')), task.timeout)
        )
      ]);

      const endTime = Date.now();
      const duration = endTime - startTime;

      const evaluation = await this.evaluator.evaluate(
        task,
        response,
        variant,
        duration
      );

      const result = {
        taskName: task.name,
        category: task.category,
        provider: provider.name,
        variant,
        run: runNumber,
        duration,
        evaluation,
        response: this.config.saveResponses ? response : null,
        timestamp: new Date().toISOString(),
        success: true
      };

      console.log(`✓ Completed in ${duration}ms - Score: ${evaluation.totalScore.toFixed(2)}`);
      return result;
    } catch (error) {
      const endTime = Date.now();
      const duration = endTime - startTime;

      const result = {
        taskName: task.name,
        category: task.category,
        provider: provider.name,
        variant,
        run: runNumber,
        duration,
        error: error.message,
        timestamp: new Date().toISOString(),
        success: false
      };

      console.log(`✗ Failed: ${error.message}`);
      return result;
    }
  }

  /**
   * Run all benchmarks
   */
  async runAll() {
    console.log('=== LLM TypeScript/JavaScript Benchmark Suite ===\n');
    await this.playwrightEvaluator.initialize();
    try {
      console.log('Loading tasks...');

      const tasks = await this.loadTasks();
      if (this.config.timeout) {
        console.log(`Applying custom global timeout: ${this.config.timeout}ms`);
        tasks.forEach(task => task.timeout = this.config.timeout);
      }
      console.log(`Loaded ${tasks.length} tasks across ${Object.keys(this.config.categories).length} categories\n`);

      const totalRuns = tasks.length * this.config.providers.length * this.config.variants.length;
      let completed = 0;

      for (const task of tasks) {
        for (const provider of this.config.providers) {
          for (const variant of this.config.variants) {
            await this.runTask(task, provider, variant);
            completed++;
            console.log(`Progress: ${completed}/${totalRuns} (${((completed/totalRuns)*100).toFixed(1)}%)`);
          }
        }
      }

      console.log('\n=== Generating Reports ===');
      const resultsFilePath = await this.reportGenerator.generate(this.results);

      console.log('\n=== Benchmark Complete ===');
      this.printSummary();

      if (resultsFilePath) {
        this.runPythonVisualizer(resultsFilePath);
      }

      return this.results;
    } finally {
      await this.playwrightEvaluator.close();
    }
  }

  /**
   * Run benchmarks for specific filters
   */
  async run(filters = {}) {
    await this.playwrightEvaluator.initialize();
    try {
      const tasks = await this.loadTasks();
      let filteredTasks = tasks;

      if (filters.category) {
        filteredTasks = filteredTasks.filter(t => t.category === filters.category);
      }
          if (filters.taskName) {
            filteredTasks = filteredTasks.filter(t => t.name === filters.taskName);
          }
      
          // Apply timeout override if provided
          if (filters.timeout) {
            console.log(`\nApplying custom timeout: ${filters.timeout}ms`);
            filteredTasks.forEach(task => task.timeout = filters.timeout);
          }
      const providers = (filters.providers && filters.providers.length > 0)
        ? this.config.providers.filter(p => filters.providers.includes(p.name))
        : this.config.providers;

      const variants = (filters.variants && filters.variants.length > 0)
        ? filters.variants
        : this.config.variants;

      for (const task of filteredTasks) {
        for (const provider of providers) {
          for (const variant of variants) {
            await this.runTask(task, provider, variant);
          }
        }
      }

      const resultsFilePath = await this.reportGenerator.generate(this.results);
      this.printSummary();

      if (resultsFilePath) {
        this.runPythonVisualizer(resultsFilePath);
      }

      return this.results;
    } finally {
      await this.playwrightEvaluator.close();
    }
  }

  /**
   * Print summary statistics to the console.
   * This is refactored to handle multiple runs per benchmark correctly.
   */
  printSummary() {
    const successful = this.results.filter(r => r.success);
    const skipped = this.results.filter(r => r.skipped);
    const failed = this.results.filter(r => !r.success && !r.skipped);

    console.log('\n--- Summary ---');
    console.log(`Total Runs (all iterations): ${this.results.length}`);
    console.log(`Successful: ${successful.length}`);
    console.log(`Skipped: ${skipped.length}`);
    console.log(`Failed: ${failed.length}`);

    if (successful.length > 0) {
      // Group results to calculate stats per benchmark permutation
      const grouped = successful.reduce((acc, r) => {
        const key = `${r.provider}|${r.variant}|${r.taskName}`;
        if (!acc[key]) acc[key] = [];
        acc[key].push(r);
        return acc;
      }, {});

      const benchmarkStats = Object.values(grouped).map(group => {
        const N = group.length;
        const meanScore = group.reduce((sum, r) => sum + r.evaluation.totalScore, 0) / N;
        const meanDuration = group.reduce((sum, r) => sum + r.duration, 0) / N;
        return { 
          provider: group[0].provider,
          variant: group[0].variant,
          meanScore,
          meanDuration
        };
      });

      const overallAvgScore = benchmarkStats.reduce((sum, s) => sum + s.meanScore, 0) / benchmarkStats.length;
      const overallAvgDuration = benchmarkStats.reduce((sum, s) => sum + s.meanDuration, 0) / benchmarkStats.length;

      console.log(`Average Score (Mean of Means): ${overallAvgScore.toFixed(2)}/100`);
      console.log(`Average Duration (Mean of Means): ${overallAvgDuration.toFixed(0)}ms`);

      // Breakdown by variant
      console.log('\n--- By Variant ---');
      const variants = [...new Set(benchmarkStats.map(s => s.variant))];
      for (const variant of variants) {
        const variantStats = benchmarkStats.filter(s => s.variant === variant);
        if (variantStats.length > 0) {
          const variantAvg = variantStats.reduce((sum, s) => sum + s.meanScore, 0) / variantStats.length;
          console.log(`${variant}: ${variantAvg.toFixed(2)}/100 (${variantStats.length} benchmarks)`);
        }
      }

      // Breakdown by provider
      console.log('\n--- By Provider ---');
      const providers = [...new Set(benchmarkStats.map(s => s.provider))];
      for (const provider of providers) {
        const providerStats = benchmarkStats.filter(s => s.provider === provider);
        if (providerStats.length > 0) {
          const providerAvg = providerStats.reduce((sum, s) => sum + s.meanScore, 0) / providerStats.length;
          console.log(`${provider}: ${providerAvg.toFixed(2)}/100 (${providerStats.length} benchmarks)`);
        }
      }
    }
  }
}
