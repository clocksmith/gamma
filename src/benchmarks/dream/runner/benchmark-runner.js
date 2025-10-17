/**
 * Main Benchmark Runner
 * Orchestrates running benchmarks across different LLMs and language variants
 */

import { readdir, readFile, mkdir, writeFile } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';
import { BenchmarkConfig } from '../config.js';
import { LLMClient } from './llm-client.js';
import { MockLLMClient } from './mock-llm-client.js';
import { Evaluator } from '../evaluator/evaluator.js';
import { ReportGenerator } from '../reports/report-generator.js';

// Playwright is optional - only needed for UI component testing
// Don't import if playwright is not installed to avoid module parsing errors
import { PlaywrightEvaluator } from '../evaluator/playwright-evaluator.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export class BenchmarkRunner {
  constructor(config = BenchmarkConfig) {
    this.config = config;
    this.llmClient = config.dryRun
      ? new MockLLMClient(config.providers)
      : new LLMClient(config.providers);

    this.playwrightEvaluator = null;
    this.playwrightReady = false;
    this.playwrightUnavailable = false;

    this.evaluator = new Evaluator(config.evaluation, null);
    this.evaluator.setDryRun(Boolean(config.dryRun));
    this.reportGenerator = new ReportGenerator({
      resultsDir: config.resultsDirectory,
      reportsDir: config.reportsDirectory
    });
    this.results = [];
    this.tokenUsage = { prompt: 0, completion: 0, total: 0 };
    this.runLabel = null;
    this.runResultsDir = null;
    this.runReportsDir = null;
  }

  /**
   * Save generated code to file
   */
  async saveGeneratedCode(task, provider, variant, runNumber, code) {
    try {
      const baseDir = this.runResultsDir || (this.config.resultsDirectory || './results');
      const srcDir = join(baseDir, 'src');
      await mkdir(srcDir, { recursive: true });

      // Determine file extension
      const isTs = variant.includes('typescript');
      const ext = isTs ? 'ts' : 'js';

      // Create filename: taskName_provider_variant_runN.ext
      const sanitizedProvider = provider.name.replace(/[^a-z0-9-]/gi, '_');
      const sanitizedVariant = variant.replace(/[^a-z0-9-]/gi, '_');
      const filename = `${task.name}_${sanitizedProvider}_${sanitizedVariant}_run${runNumber}.${ext}`;
      const filePath = join(srcDir, filename);

      // Write code to file
      await writeFile(filePath, code, 'utf-8');

      return filePath;
    } catch (error) {
      console.warn(`Failed to save code: ${error.message}`);
      return null;
    }
  }

  runPythonVisualizer(resultsFilePath) {
    console.log('\n🐍 Running Python visualizer...');
    try {
      const scriptPath = join(__dirname, '../analyze_results.py');
      const reportsDir = this.runReportsDir || this.config.reportsDirectory;
      const command = `python3 \"${scriptPath}\" \"${resultsFilePath}\" --visualize --reports-dir ${reportsDir}`;
      execSync(command, { stdio: 'inherit' });
      console.log('✓ Python visualization complete.');
    } catch (error) {
      console.warn(`
⚠️  Python visualization failed.
    Error: ${error.message}
    Please ensure you have Python 3 installed, along with the required libraries (pip install pandas matplotlib seaborn scipy)`);
    }
  }

  /**
   * Load all benchmark tasks from the tasks directory
   * Normalizes category names using the resolver and adds bias level metadata
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

            // Resolve category name (handles aliases like 'ui-components' -> '5-react-component-library')
            const taskCategory = taskData.category || category;
            const resolvedCategory = this.config.resolveCategory(taskCategory);
            const resolvedConfig = this.config.categories[resolvedCategory] || categoryConfig;

            tasks.push({
              ...taskData,
              category: resolvedCategory,
              originalCategory: taskCategory, // Preserve original for reference
              biasLevel: resolvedConfig.biasLevel || 'unknown',
              weight: resolvedConfig.weight,
              timeout: resolvedConfig.timeout
            });
          }
        }
      } catch (err) {
        console.warn(`Warning: Could not load tasks from ${category}: ${err.message}`);
      }
    }

    return tasks;
  }

  _requiresBrowser(task) {
    if (!task) return false;
    if (Array.isArray(task.requirements) && task.requirements.includes('browser')) {
      return true;
    }
    return false;
  }

  async _preparePlaywright(tasks, includeBrowser) {
    const needsBrowser = includeBrowser && tasks.some(task => this._requiresBrowser(task));
    if (!needsBrowser) {
      this.evaluator.playwrightEvaluator = null;
      return false;
    }

    if (this.playwrightUnavailable) {
      if (this.config.output?.verbose) {
        console.warn('⚠️  Playwright previously failed to launch; browser-based tasks will be skipped.');
      }
      this.evaluator.playwrightEvaluator = null;
      return false;
    }

    if (this.playwrightReady && this.playwrightEvaluator) {
      this.evaluator.playwrightEvaluator = this.playwrightEvaluator;
      return true;
    }

    if (!this.playwrightEvaluator) {
      this.playwrightEvaluator = new PlaywrightEvaluator();
    }

    try {
      await this.playwrightEvaluator.initialize();
      this.playwrightReady = true;
      this.evaluator.playwrightEvaluator = this.playwrightEvaluator;
      return true;
    } catch (error) {
      console.warn('⚠️  Playwright initialization failed. Browser-centric tasks will be skipped.');
      if (this.config.output?.verbose) {
        console.warn(`    ${error.message}`);
      }
      this.playwrightUnavailable = true;
      this.playwrightReady = false;
      this.evaluator.playwrightEvaluator = null;
      return false;
    }
  }

  async _cleanupPlaywright() {
    if (this.playwrightReady && this.playwrightEvaluator) {
      try {
        await this.playwrightEvaluator.close();
      } catch (error) {
        if (this.config.output?.verbose) {
          console.warn(`⚠️  Failed to close Playwright: ${error.message}`);
        }
      }
    }
    this.playwrightReady = false;
    this.evaluator.playwrightEvaluator = null;
  }

  _resetTokenUsage() {
    this.tokenUsage = { prompt: 0, completion: 0, total: 0 };
  }

  _updateTokenUsage(usage) {
    if (!usage) return;

    const prompt =
      usage.prompt_tokens ??
      usage.input_tokens ??
      usage.prompt_eval_count ??
      0;
    const completion =
      usage.completion_tokens ??
      usage.output_tokens ??
      usage.eval_count ??
      0;

    let total = usage.total_tokens;
    if (total == null) {
      if (
        usage.prompt_eval_count != null &&
        usage.eval_count != null
      ) {
        total = usage.prompt_eval_count + usage.eval_count;
      } else {
        total = prompt + completion;
      }
    }

    if (Number.isFinite(prompt)) {
      this.tokenUsage.prompt += Math.round(prompt);
    }
    if (Number.isFinite(completion)) {
      this.tokenUsage.completion += Math.round(completion);
    }
    if (Number.isFinite(total)) {
      this.tokenUsage.total += Math.round(total);
    }
  }

  _formatTokenTotals() {
    const { prompt, completion, total } = this.tokenUsage;
    return `prompt ${prompt}, completion ${completion}, total ${total}`;
  }

  async generateAutoRating(provider, code, task, variant) {
    if (!code || !provider) return null;
    if (this.config.dryRun) {
      return {
        score: 0.5,
        reasoning: 'Auto-rating skipped in dry-run mode.',
        issues: [],
        raw: null
      };
    }

    const requirementList = Array.isArray(task.requirements) && task.requirements.length
      ? task.requirements.join(', ')
      : 'No explicit keywords';

    const prompt = `
AUTO_RATER_EVAL
You are auditing code quality. Score strictly between 0.0 and 1.0.
Return ONLY JSON with keys: "score" (number between 0 and 1), "reasoning" (short string), "issues" (array of strings).
Penalize missing error handling, unclear naming, unnecessary complexity, or deviation from instructions.
Task: ${task.name}
Variant: ${variant}
Requirements: ${requirementList}
Code to evaluate:
\`\`\`
${code}
\`\`\`
JSON:`.trim();

    try {
      const response = await this.llmClient.complete(provider, prompt);
      if (response.usage) {
        this._updateTokenUsage(response.usage);
      }
      const parsed = this._parseAutoRating(response.content);
      return {
        ...parsed,
        raw: response.content
      };
    } catch (error) {
      console.warn(`Auto-rating failed: ${error.message}`);
      return {
        score: 0.5,
        reasoning: 'Auto-rating failed; defaulting to neutral.',
        issues: [error.message]
      };
    }
  }

  _parseAutoRating(content) {
    if (!content) {
      return { score: 0.5, reasoning: 'Empty response', issues: [] };
    }
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      return { score: 0.5, reasoning: 'No JSON found in response', issues: [content.trim().slice(0, 200)] };
    }
    try {
      const data = JSON.parse(jsonMatch[0]);
      const score = typeof data.score === 'number' ? Math.max(0, Math.min(1, data.score)) : 0.5;
      const reasoning = typeof data.reasoning === 'string' ? data.reasoning : 'No reasoning provided';
      const issues = Array.isArray(data.issues) ? data.issues : [];
      return { score, reasoning, issues };
    } catch (err) {
      return { score: 0.5, reasoning: 'Malformed JSON in auto-rating response', issues: [err.message] };
    }
  }

  async _prepareRunDirectory() {
    const baseResults = this.config.resultsDirectory || './results';
    const baseReports = this.config.reportsDirectory || './reports';
    this.runLabel = new Date().toISOString().replace(/[:.]/g, '-');
    this.runResultsDir = join(baseResults, this.runLabel);
    this.runReportsDir = join(baseReports, this.runLabel);
    await mkdir(join(this.runResultsDir, 'src'), { recursive: true });
    await mkdir(this.runReportsDir, { recursive: true });
    if (this.reportGenerator?.config) {
      this.reportGenerator.config.resultsDir = this.runResultsDir;
      this.reportGenerator.config.reportsDir = this.runReportsDir;
      this.reportGenerator.config.runLabel = this.runLabel;
    }
  }

  /**
   * Build a prompt from task definition based on variant.
   * Supports both new promptLevels structure and legacy variants structure.
   *
   * @param {Object} task - The task object
   * @param {string} variant - Variant name (e.g., "typescript-expert", "javascript-jsdoc-beginner")
   * @returns {string|null} - The built prompt or null if not found
   */
  buildPrompt(task, variant) {
    // Check if task has new promptLevels structure
    if (task.promptLevels && typeof task.promptLevels === 'object') {
      // Parse variant into language and level
      // Variants can be: "typescript-expert", "javascript-jsdoc-novice", etc.
      const parts = variant.split('-');

      // The last part is the prompt level (novice, beginner, intermediate, advanced, expert)
      const level = parts[parts.length - 1];

      // Everything before is the language (typescript, javascript, javascript-jsdoc, etc.)
      const language = parts.slice(0, -1).join('-');

      // Check if this level exists in promptLevels
      if (task.promptLevels[level]) {
        const basePrompt = task.promptLevels[level];

        // Get language-specific instructions if available
        const langInstructions = task.languageInstructions?.[language] || '';

        // Perform template substitution
        // Replace {languageSpecific} placeholder with language instructions
        const finalPrompt = basePrompt.replace('{languageSpecific}', langInstructions);

        return finalPrompt;
      }

      // If level not found, try falling back to variants (maybe it's not a level-based variant)
      if (task.variants && task.variants[variant]) {
        return task.variants[variant];
      }

      return null;
    }

    // Fallback to legacy variants structure for backward compatibility
    if (task.variants && task.variants[variant]) {
      return task.variants[variant];
    }

    return null;
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

    const language = variant.includes('typescript') ? 'typescript' : 'javascript';

    try {
      const prompt = this.buildPrompt(task, variant);
      if (!prompt) {
        if (this.config.output.verbose) {
          console.log(`  → Skipping ${variant} (not defined for this task)`);
        }
        return {
          taskName: task.name,
          category: task.category,
          biasLevel: task.biasLevel,
          provider: provider.name,
          variant,
          language,
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

      this._updateTokenUsage(response.usage);

      // Save generated code to file
      const codePath = await this.saveGeneratedCode(
        task,
        provider,
        variant,
        runNumber,
        evaluation.details.code
      );

      const autoRating = await this.generateAutoRating(provider, evaluation.details.code, task, variant);
      if (autoRating) {
        evaluation.autoRating = autoRating;
        if (!evaluation.scores) evaluation.scores = {};
        evaluation.scores.autoRater = autoRating.score;
        if (evaluation.metrics) {
          evaluation.metrics.autoRating = autoRating;
        }
      }

      const result = {
        taskName: task.name,
        category: task.category,
        biasLevel: task.biasLevel,
        provider: provider.name,
        variant,
        language,
        run: runNumber,
        duration,
        evaluation,
        codePath,  // Add file path to result
        response: this.config.saveResponses ? response : null,
        timestamp: new Date().toISOString(),
        success: true
      };

      console.log(`✓ Completed in ${duration}ms - Score: ${evaluation.totalScore.toFixed(2)}`);
      if (codePath) {
        console.log(`  Code saved to: ${codePath}`);
      }
      return result;
    } catch (error) {
      const endTime = Date.now();
      const duration = endTime - startTime;

      const result = {
        taskName: task.name,
        category: task.category,
        biasLevel: task.biasLevel,
        provider: provider.name,
        variant,
        language,
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
    this.results = [];
    this._resetTokenUsage();
    await this._prepareRunDirectory();
    console.log('Loading tasks...');

    const tasks = await this.loadTasks();
    const includeBrowser = true;
    const playwrightReady = await this._preparePlaywright(tasks, includeBrowser);
    const runnableTasks = playwrightReady ? tasks : tasks.filter(task => !this._requiresBrowser(task));

    if (!playwrightReady) {
      const skippedCount = tasks.length - runnableTasks.length;
      if (skippedCount > 0) {
        console.warn(`⚠️  Skipping ${skippedCount} browser-based task(s) because Playwright is unavailable.`);
      }
    }

    try {
      if (this.config.timeout) {
        console.log(`Applying custom global timeout: ${this.config.timeout}ms`);
        runnableTasks.forEach(task => task.timeout = this.config.timeout);
      }
      console.log(`Loaded ${runnableTasks.length} tasks across ${Object.keys(this.config.categories).length} categories\n`);

      const totalRuns = runnableTasks.length * this.config.providers.length * this.config.variants.length;
      let completed = 0;

      for (const task of runnableTasks) {
        for (const provider of this.config.providers) {
          for (const variant of this.config.variants) {
            await this.runTask(task, provider, variant);
            completed++;
            const tokenSummary = this._formatTokenTotals();
            console.log(`Progress: ${completed}/${totalRuns} (${((completed / totalRuns) * 100).toFixed(1)}%) | Tokens ${tokenSummary}`);
          }
        }
      }

      console.log('\n=== Generating Reports ===');
      const resultsFilePath = await this.reportGenerator.generate(this.results);

      console.log('\n=== Benchmark Complete ===');
      this.printSummary();

      if (resultsFilePath) {
        if (this.config.dryRun) {
          if (this.config.output?.verbose) {
            console.log('Skipping Python visualizer in dry-run mode.');
          }
        } else {
          this.runPythonVisualizer(resultsFilePath);
        }
      }

      return this.results;
    } finally {
      await this._cleanupPlaywright();
    }
  }

  /**
   * Run benchmarks for specific filters
   */
  async run(filters = {}) {
    this.results = [];
    this._resetTokenUsage();
    await this._prepareRunDirectory();

    const tasks = await this.loadTasks();
    let filteredTasks = tasks;

    if (filters.categories && filters.categories.length > 0) {
      filteredTasks = filteredTasks.filter(t => filters.categories.includes(t.category));
    }

    if (filters.category) {
      filteredTasks = filteredTasks.filter(t => t.category === filters.category);
    }

    if (filters.taskName) {
      filteredTasks = filteredTasks.filter(t => t.name === filters.taskName);
    }

    if (filters.tasks && filters.tasks.length > 0) {
      const taskNames = new Set(filters.tasks);
      filteredTasks = filteredTasks.filter(t => taskNames.has(t.name));
    }

    const includeBrowser = Boolean(filters.includeBrowser);
    const playwrightReady = await this._preparePlaywright(filteredTasks, includeBrowser);
    const runnableTasks = includeBrowser && playwrightReady
      ? filteredTasks
      : filteredTasks.filter(task => !this._requiresBrowser(task));

    if ((!includeBrowser || !playwrightReady) && filteredTasks.length !== runnableTasks.length) {
      const skippedCount = filteredTasks.length - runnableTasks.length;
      if (skippedCount > 0) {
        console.warn(`⚠️  Skipping ${skippedCount} browser-based task(s). Use --include-browser with a working Playwright setup to enable them.`);
      }
    }

    try {
      if (filters.timeout) {
        console.log(`\nApplying custom timeout: ${filters.timeout}ms`);
        runnableTasks.forEach(task => task.timeout = filters.timeout);
      }

      const providerLookup = new Map(this.config.providers.map(p => [p.name, p]));
      const requestedProviders = Array.isArray(filters.providers) ? filters.providers : [];
      const missingProviders = [];

      const providers = requestedProviders.length > 0
        ? requestedProviders.map(name => {
            const provider = providerLookup.get(name);
            if (!provider) {
              missingProviders.push(name);
            }
            return provider;
          }).filter(Boolean)
        : this.config.providers;

      if (missingProviders.length > 0) {
        console.warn(`⚠️  Unknown provider(s): ${missingProviders.join(', ')} - skipping.`);
      }

      if (providers.length === 0) {
        console.warn('⚠️  No providers selected. Nothing to run.');
        return this.results;
      }

      const variants = (filters.variants && filters.variants.length > 0)
        ? filters.variants
        : this.config.variants;

      if (variants.length === 0) {
        console.warn('⚠️  No variants selected. Nothing to run.');
        return this.results;
      }

      const totalRuns = runnableTasks.length * providers.length * variants.length;
      let completed = 0;

      for (const task of runnableTasks) {
        for (const provider of providers) {
          for (const variant of variants) {
            await this.runTask(task, provider, variant);
            completed++;
            const tokenSummary = this._formatTokenTotals();
            console.log(`Progress: ${completed}/${totalRuns} (${((completed / totalRuns) * 100).toFixed(1)}%) | Tokens ${tokenSummary}`);
          }
        }
      }

      const resultsFilePath = await this.reportGenerator.generate(this.results);
      this.printSummary();

      if (resultsFilePath) {
        if (this.config.dryRun) {
          if (this.config.output?.verbose) {
            console.log('Skipping Python visualizer in dry-run mode.');
          }
        } else {
          this.runPythonVisualizer(resultsFilePath);
        }
      }

      return this.results;
    } finally {
      await this._cleanupPlaywright();
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

      const variantAverages = successful.reduce((acc, r) => {
        if (!acc[r.variant]) acc[r.variant] = { totalScore: 0, totalRuns: 0 };
        acc[r.variant].totalScore += r.evaluation.totalScore;
        acc[r.variant].totalRuns += 1;
        return acc;
      }, {});

      const sortedVariants = Object.entries(variantAverages)
        .map(([variant, data]) => ({
          variant,
          meanScore: data.totalScore / data.totalRuns,
          runs: data.totalRuns
        }))
        .sort((a, b) => b.meanScore - a.meanScore);

      console.log('\nVariant Averages:');
      sortedVariants.forEach(({ variant, meanScore, runs }) => {
        console.log(`  ${variant}: ${meanScore.toFixed(2)} (${runs} run${runs === 1 ? '' : 's'})`);
      });

      const languageStats = successful.reduce((acc, r) => {
        const lang = r.language || (r.variant.includes('typescript') ? 'typescript' : 'javascript');
        if (!acc[lang]) {
          acc[lang] = {
            totalScore: 0,
            totalRuns: 0,
            byProvider: {}
          };
        }
        acc[lang].totalScore += r.evaluation.totalScore;
        acc[lang].totalRuns += 1;
        if (!acc[lang].byProvider[r.provider]) {
          acc[lang].byProvider[r.provider] = { totalScore: 0, totalRuns: 0 };
        }
        acc[lang].byProvider[r.provider].totalScore += r.evaluation.totalScore;
        acc[lang].byProvider[r.provider].totalRuns += 1;
        return acc;
      }, {});

      const jsStats = languageStats.javascript || { totalScore: 0, totalRuns: 0, byProvider: {} };
      const tsStats = languageStats.typescript || { totalScore: 0, totalRuns: 0, byProvider: {} };
      const jsMean = jsStats.totalRuns ? (jsStats.totalScore / jsStats.totalRuns) : null;
      const tsMean = tsStats.totalRuns ? (tsStats.totalScore / tsStats.totalRuns) : null;

      console.log('\n--- JS vs TS Comparison ---');
      if (jsMean !== null && tsMean !== null) {
        const delta = tsMean - jsMean;
        console.log(`Overall: TS ${tsMean.toFixed(2)} vs JS ${jsMean.toFixed(2)} (Δ ${delta >= 0 ? '+' : ''}${delta.toFixed(2)})`);
      } else if (jsMean !== null) {
        console.log(`Only JavaScript variants ran. Avg: ${jsMean.toFixed(2)}`);
      } else if (tsMean !== null) {
        console.log(`Only TypeScript variants ran. Avg: ${tsMean.toFixed(2)}`);
      } else {
        console.log('No comparable JavaScript/TypeScript runs recorded.');
      }

      const providerNames = new Set([
        ...Object.keys(jsStats.byProvider || {}),
        ...Object.keys(tsStats.byProvider || {})
      ]);

      if (providerNames.size > 0) {
        console.log('By provider:');
        for (const provider of providerNames) {
          const jsProvider = jsStats.byProvider?.[provider];
          const tsProvider = tsStats.byProvider?.[provider];
          const jsProviderMean = jsProvider?.totalRuns ? (jsProvider.totalScore / jsProvider.totalRuns) : null;
          const tsProviderMean = tsProvider?.totalRuns ? (tsProvider.totalScore / tsProvider.totalRuns) : null;
          if (jsProviderMean === null && tsProviderMean === null) continue;
          if (jsProviderMean !== null && tsProviderMean !== null) {
            const delta = tsProviderMean - jsProviderMean;
            console.log(`  ${provider}: TS ${tsProviderMean.toFixed(2)} vs JS ${jsProviderMean.toFixed(2)} (Δ ${delta >= 0 ? '+' : ''}${delta.toFixed(2)})`);
          } else if (jsProviderMean !== null) {
            console.log(`  ${provider}: JS only (${jsProviderMean.toFixed(2)})`);
          } else if (tsProviderMean !== null) {
            console.log(`  ${provider}: TS only (${tsProviderMean.toFixed(2)})`);
          }
        }
      }
    }

    const { prompt, completion, total } = this.tokenUsage;
    if (prompt || completion || total) {
      console.log(`Tokens used: prompt ${prompt}, completion ${completion}, total ${total}`);
    }
  }
}
