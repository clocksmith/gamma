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
import { hashCode, analyzeCodeVariation, calculateVariance } from '../utils/code-similarity.js';

// Playwright is optional - only needed for UI component testing
// Don't import if playwright is not installed to avoid module parsing errors
import { PlaywrightEvaluator } from '../evaluator/playwright-evaluator.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export class BenchmarkRunner {
  constructor(config = BenchmarkConfig) {
    this.config = config;

    // Initialize LLM client with temperature from config
    const llmOptions = {
      temperature: config.temperature ?? 1.0
    };
    this.llmClient = config.dryRun
      ? new MockLLMClient(config.providers, llmOptions)
      : new LLMClient(config.providers, llmOptions);

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
    this.runGroups = new Map(); // Track runs by task+provider+variant for statistics
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
   * Build a prompt from task definition.
   * Supports both dimension objects and legacy variant strings.
   *
   * @param {Object} task - The task object
   * @param {string|Object} variantOrDimensions - Either a variant string or dimensions object
   * @returns {string|null} - The built prompt or null if not found
   */
  buildPrompt(task, variantOrDimensions) {
    let dimensions;

    // Handle both string and object inputs
    if (typeof variantOrDimensions === 'string') {
      // Parse legacy variant string
      dimensions = BenchmarkConfig.parseVariantString(variantOrDimensions);
      if (!dimensions) {
        // Try legacy variants structure
        if (task.variants && task.variants[variantOrDimensions]) {
          return task.variants[variantOrDimensions];
        }
        return null;
      }
    } else if (typeof variantOrDimensions === 'object') {
      dimensions = variantOrDimensions;
    } else {
      return null;
    }

    // Extract dimensions
    const { language, promptLevel, framework, codeStyle } = dimensions;

    // Check if task has new promptLevels structure
    if (task.promptLevels && typeof task.promptLevels === 'object') {
      const level = promptLevel || 'expert';

      // Check if this level exists in promptLevels
      if (task.promptLevels[level]) {
        const basePrompt = task.promptLevels[level];

        // Get language-specific instructions if available
        const langInstructions = task.languageInstructions?.[language] || '';

        // Perform template substitution
        // Replace {languageSpecific} placeholder with language instructions
        let finalPrompt = basePrompt.replace('{languageSpecific}', langInstructions);

        // Add framework-specific instructions if needed
        if (framework && task.frameworkInstructions?.[framework]) {
          finalPrompt += '\n' + task.frameworkInstructions[framework];
        }

        // Add code style instructions if needed
        if (codeStyle && task.codeStyleInstructions?.[codeStyle]) {
          finalPrompt += '\n' + task.codeStyleInstructions[codeStyle];
        }

        return finalPrompt;
      }
    }

    // Fallback to legacy variants structure for backward compatibility
    const variantString = typeof variantOrDimensions === 'string'
      ? variantOrDimensions
      : BenchmarkConfig.toVariantString(dimensions);

    if (task.variants && task.variants[variantString]) {
      return task.variants[variantString];
    }

    return null;
  }

  /**
   * Run a single benchmark task multiple times as configured.
   * Tracks code variation across runs for statistical analysis.
   */
  async runTask(task, provider, variant) {
    const allRunResults = [];
    const codeSamples = [];

    // Run multiple times
    for (let i = 1; i <= this.config.runs; i++) {
      const result = await this._executeSingleRun(task, provider, variant, i);
      allRunResults.push(result);

      // Collect code samples for variation analysis
      if (result.success && result.code) {
        codeSamples.push({
          code: result.code,
          run: i,
          hash: hashCode(result.code)
        });
      }
    }

    // Analyze code variation if we have multiple runs
    if (this.config.runs > 1 && codeSamples.length > 1) {
      const variation = analyzeCodeVariation(codeSamples);

      // Add variation analysis to each result
      allRunResults.forEach(result => {
        if (result.success) {
          result.codeVariation = variation;
        }
      });

      // Store in run groups for summary statistics
      const groupKey = `${task.name}_${provider.name}_${typeof variant === 'string' ? variant : BenchmarkConfig.toVariantString(variant)}`;
      this.runGroups.set(groupKey, {
        task: task.name,
        provider: provider.name,
        variant: typeof variant === 'string' ? variant : BenchmarkConfig.toVariantString(variant),
        runs: allRunResults,
        codeVariation: variation
      });
    }

    this.results.push(...allRunResults);
  }

  /**
   * Executes a single benchmark run. Internal method.
   */
  async _executeSingleRun(task, provider, variant, runNumber) {
    const startTime = Date.now();
    const runIdentifier = this.config.runs > 1 ? ` [Run ${runNumber}/${this.config.runs}]` : '';

    // Parse variant dimensions (supports both string and object)
    const dimensions = typeof variant === 'string'
      ? BenchmarkConfig.parseVariantString(variant)
      : variant;

    const variantString = typeof variant === 'string'
      ? variant
      : BenchmarkConfig.toVariantString(variant);

    console.log(`\n[${provider.name}] [${variantString}]${runIdentifier} Running: ${task.name}`);

    const language = dimensions?.language || (variantString.includes('typescript') ? 'typescript' : 'javascript');

    try {
      const prompt = this.buildPrompt(task, variant);
      if (!prompt) {
        if (this.config.output.verbose) {
          console.log(`  → Skipping ${variantString} (not defined for this task)`);
        }
        return {
          taskName: task.name,
          category: task.category,
          biasLevel: task.biasLevel,
          provider: provider.name,
          variant: variantString,
          dimensions,  // Add parsed dimensions
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

      // Generate auto-rating for code quality
      const autoRating = await this.generateAutoRating(provider, evaluation.code, task, variant);
      if (autoRating) {
        evaluation.benchmarks.autoRater = autoRating;
      }

      // Save generated code to file
      const codePath = await this.saveGeneratedCode(
        task,
        provider,
        variant,
        runNumber,
        evaluation.code
      );

      const result = {
        taskName: task.name,
        category: task.category,
        biasLevel: task.biasLevel,
        provider: provider.name,
        variant: variantString,
        dimensions,  // Add parsed dimensions
        language,
        run: runNumber,
        duration,
        benchmarks: evaluation.benchmarks,
        code: evaluation.code,  // Store code for variation analysis
        codeHash: hashCode(evaluation.code),  // Add code hash
        codePath,  // Add file path to result
        response: this.config.saveResponses ? response : null,
        timestamp: new Date().toISOString(),
        success: true
      };

      // Print results summary
      console.log(`✓ Completed in ${duration}ms`);
      console.log(`  Tests: ${evaluation.benchmarks.testsPassed}/${evaluation.benchmarks.testsTotal}`);
      if (evaluation.benchmarks.runtimePerformance && evaluation.benchmarks.runtimePerformance.length > 0) {
        const avgTime = evaluation.benchmarks.runtimePerformance.reduce((sum, r) => sum + (r.meanTimeMs || 0), 0) / evaluation.benchmarks.runtimePerformance.length;
        console.log(`  Runtime: ${avgTime.toFixed(2)}ms avg`);
      }
      if (autoRating) {
        console.log(`  Auto-rater: ${(autoRating.score * 100).toFixed(1)}%`);
      }
      if (codePath) {
        console.log(`  Code: ${codePath}`);
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
        variant: variantString,
        dimensions,  // Add parsed dimensions
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

    console.log('\n═══════════════════════════════════════════════════════════');
    console.log('                    BENCHMARK SUMMARY                      ');
    console.log('═══════════════════════════════════════════════════════════\n');

    console.log('📊 Run Results:');
    console.log(`   Total Runs: ${this.results.length}`);
    console.log(`   ✅ Successful: ${successful.length}`);
    console.log(`   ⏭️  Skipped: ${skipped.length}`);
    console.log(`   ❌ Failed: ${failed.length}`);

    if (successful.length > 0) {
      // Calculate aggregate metrics
      const metrics = {
        testAccuracy: [],
        runtimePerformance: [],
        codeSize: [],
        codeCost: [],
        complexity: [],
        autoRater: []
      };

      successful.forEach(r => {
        if (r.benchmarks) {
          // Test accuracy
          if (r.benchmarks.testsTotal > 0) {
            metrics.testAccuracy.push(r.benchmarks.accuracyScore);
          }

          // Runtime performance
          if (r.benchmarks.runtimePerformance && r.benchmarks.runtimePerformance.length > 0) {
            const avgTime = r.benchmarks.runtimePerformance.reduce((sum, p) => sum + (p.meanTimeMs || 0), 0) / r.benchmarks.runtimePerformance.length;
            metrics.runtimePerformance.push(avgTime);
          }

          // Code size
          if (r.benchmarks.codeSizeMetrics) {
            metrics.codeSize.push(r.benchmarks.codeSizeMetrics.codeLines);
            metrics.codeCost.push(r.benchmarks.codeSizeMetrics.estimatedCostUSD.totalCostUSD);
          }

          // Complexity
          if (r.benchmarks.complexity) {
            metrics.complexity.push(r.benchmarks.complexity.cyclomaticComplexity);
          }

          // Auto-rater
          if (r.benchmarks.autoRater && r.benchmarks.autoRater.score !== undefined) {
            metrics.autoRater.push(r.benchmarks.autoRater.score);
          }
        }
      });

      console.log('\n📊 Individual Benchmark Metrics:');

      // Test Accuracy
      if (metrics.testAccuracy.length > 0) {
        const avgAccuracy = metrics.testAccuracy.reduce((a, b) => a + b, 0) / metrics.testAccuracy.length;
        console.log(`\n   ✓ Test Accuracy: ${(avgAccuracy * 100).toFixed(1)}%`);
        console.log(`     (based on ${metrics.testAccuracy.length} runs with tests)`);
      }

      // Runtime Performance
      if (metrics.runtimePerformance.length > 0) {
        const runtimeStats = calculateVariance(metrics.runtimePerformance);
        console.log(`\n   ⚡ Runtime Performance:`);
        console.log(`     Average: ${runtimeStats.mean.toFixed(2)}ms`);
        console.log(`     Range: ${runtimeStats.min.toFixed(2)}ms - ${runtimeStats.max.toFixed(2)}ms`);
        if (metrics.runtimePerformance.length > 1) {
          console.log(`     Std Dev: ${runtimeStats.stdDev.toFixed(2)}ms (CV: ${(runtimeStats.coefficientOfVariation * 100).toFixed(1)}%)`);
        }
      }

      // Code Size & Cost
      if (metrics.codeSize.length > 0) {
        const avgSize = metrics.codeSize.reduce((a, b) => a + b, 0) / metrics.codeSize.length;
        const totalCost = metrics.codeCost.reduce((a, b) => a + b, 0);
        console.log(`\n   📏 Code Size & Cost:`);
        console.log(`     Average code lines: ${avgSize.toFixed(0)}`);
        console.log(`     Total estimated cost: $${totalCost.toFixed(4)}`);
      }

      // Complexity
      if (metrics.complexity.length > 0) {
        const avgComplexity = metrics.complexity.reduce((a, b) => a + b, 0) / metrics.complexity.length;
        console.log(`\n   🔀 Cyclomatic Complexity: ${avgComplexity.toFixed(1)} avg`);
      }

      // Auto-rater
      if (metrics.autoRater.length > 0) {
        const avgAutoRater = metrics.autoRater.reduce((a, b) => a + b, 0) / metrics.autoRater.length;
        console.log(`\n   🤖 Auto-rater (LLM code quality): ${(avgAutoRater * 100).toFixed(1)}%`);
        console.log(`     (based on ${metrics.autoRater.length} LLM evaluations)`);
      }

      // Code variation analysis (if multiple runs)
      if (this.config.runs > 1 && this.runGroups.size > 0) {
        console.log('\n📊 Code Variation Analysis (Multiple Runs):');

        let totalGroups = 0;
        let totalIdentical = 0;
        let avgDuplicateRate = 0;
        let avgSimilarity = 0;

        this.runGroups.forEach((group, key) => {
          if (group.codeVariation) {
            totalGroups++;
            avgDuplicateRate += group.codeVariation.duplicateRate;
            avgSimilarity += group.codeVariation.avgSimilarity;
            if (group.codeVariation.duplicateRate === 1.0) {
              totalIdentical++;
            }
          }
        });

        if (totalGroups > 0) {
          avgDuplicateRate /= totalGroups;
          avgSimilarity /= totalGroups;

          console.log(`   Total benchmark groups: ${totalGroups}`);
          console.log(`   Groups with identical outputs: ${totalIdentical} (${((totalIdentical / totalGroups) * 100).toFixed(1)}%)`);
          console.log(`   Average duplicate rate: ${(avgDuplicateRate * 100).toFixed(1)}%`);
          console.log(`   Average code similarity: ${(avgSimilarity * 100).toFixed(1)}%`);

          if (avgDuplicateRate > 0.5) {
            console.log(`\n   ⚠️  High duplicate rate detected!`);
            console.log(`      Consider increasing --temperature for more variation`);
          }
        }

        // Show top groups with variation
        const groupsWithVariation = Array.from(this.runGroups.entries())
          .filter(([_, group]) => group.codeVariation && group.codeVariation.duplicateRate < 0.9)
          .sort((a, b) => a[1].codeVariation.avgSimilarity - b[1].codeVariation.avgSimilarity)
          .slice(0, 5);

        if (groupsWithVariation.length > 0) {
          console.log(`\n   Top benchmarks with code variation:`);
          groupsWithVariation.forEach(([key, group]) => {
            const v = group.codeVariation;
            console.log(`     ${group.task} (${group.variant}):`);
            console.log(`       ${v.uniqueOutputs}/${v.totalSamples} unique outputs, ${(v.avgSimilarity * 100).toFixed(1)}% avg similarity`);
          });
        }
      }

      // Per-variant breakdown
      const variantStats = successful.reduce((acc, r) => {
        if (!acc[r.variant]) {
          acc[r.variant] = { testAccuracy: [], runtimeMs: [], codeLines: [], autoRater: [], runs: 0 };
        }
        acc[r.variant].runs++;
        if (r.benchmarks) {
          if (r.benchmarks.testsTotal > 0) {
            acc[r.variant].testAccuracy.push(r.benchmarks.accuracyScore);
          }
          if (r.benchmarks.runtimePerformance && r.benchmarks.runtimePerformance.length > 0) {
            const avgTime = r.benchmarks.runtimePerformance.reduce((sum, p) => sum + (p.meanTimeMs || 0), 0) / r.benchmarks.runtimePerformance.length;
            acc[r.variant].runtimeMs.push(avgTime);
          }
          if (r.benchmarks.codeSizeMetrics) {
            acc[r.variant].codeLines.push(r.benchmarks.codeSizeMetrics.codeLines);
          }
          if (r.benchmarks.autoRater && r.benchmarks.autoRater.score !== undefined) {
            acc[r.variant].autoRater.push(r.benchmarks.autoRater.score);
          }
        }
        return acc;
      }, {});

      console.log('\n🔬 Per-Variant Metrics:');
      Object.entries(variantStats)
        .sort((a, b) => {
          const avgA = a[1].testAccuracy.length > 0 ? a[1].testAccuracy.reduce((s, v) => s + v, 0) / a[1].testAccuracy.length : 0;
          const avgB = b[1].testAccuracy.length > 0 ? b[1].testAccuracy.reduce((s, v) => s + v, 0) / b[1].testAccuracy.length : 0;
          return avgB - avgA;
        })
        .forEach(([variant, stats]) => {
          const avgAcc = stats.testAccuracy.length > 0 ? (stats.testAccuracy.reduce((a, b) => a + b, 0) / stats.testAccuracy.length * 100) : null;
          const avgRuntime = stats.runtimeMs.length > 0 ? stats.runtimeMs.reduce((a, b) => a + b, 0) / stats.runtimeMs.length : null;
          const avgLines = stats.codeLines.length > 0 ? stats.codeLines.reduce((a, b) => a + b, 0) / stats.codeLines.length : null;
          const avgAutoRater = stats.autoRater.length > 0 ? (stats.autoRater.reduce((a, b) => a + b, 0) / stats.autoRater.length * 100) : null;

          console.log(`\n   ${variant} (${stats.runs} runs):`);
          if (avgAcc !== null) console.log(`     Accuracy: ${avgAcc.toFixed(1)}%`);
          if (avgRuntime !== null) console.log(`     Runtime: ${avgRuntime.toFixed(2)}ms`);
          if (avgLines !== null) console.log(`     Code size: ${avgLines.toFixed(0)} lines`);
          if (avgAutoRater !== null) console.log(`     Auto-rater: ${avgAutoRater.toFixed(1)}%`);
        });

      // Language comparison
      const languageStats = successful.reduce((acc, r) => {
        const lang = r.variant.includes('typescript') ? 'typescript' : 'javascript';
        if (!acc[lang]) {
          acc[lang] = { testAccuracy: [], runtimeMs: [], codeLines: [] };
        }
        if (r.benchmarks) {
          if (r.benchmarks.testsTotal > 0) {
            acc[lang].testAccuracy.push(r.benchmarks.accuracyScore);
          }
          if (r.benchmarks.runtimePerformance && r.benchmarks.runtimePerformance.length > 0) {
            const avgTime = r.benchmarks.runtimePerformance.reduce((sum, p) => sum + (p.meanTimeMs || 0), 0) / r.benchmarks.runtimePerformance.length;
            acc[lang].runtimeMs.push(avgTime);
          }
          if (r.benchmarks.codeSizeMetrics) {
            acc[lang].codeLines.push(r.benchmarks.codeSizeMetrics.codeLines);
          }
        }
        return acc;
      }, {});

      const jsStats = languageStats.javascript;
      const tsStats = languageStats.typescript;

      if (jsStats && tsStats) {
        console.log('\n🆚 JavaScript vs TypeScript:');

        const jsAvgAcc = jsStats.testAccuracy.length > 0 ? jsStats.testAccuracy.reduce((a, b) => a + b, 0) / jsStats.testAccuracy.length : null;
        const tsAvgAcc = tsStats.testAccuracy.length > 0 ? tsStats.testAccuracy.reduce((a, b) => a + b, 0) / tsStats.testAccuracy.length : null;

        if (jsAvgAcc !== null && tsAvgAcc !== null) {
          console.log(`   Accuracy: TS ${(tsAvgAcc * 100).toFixed(1)}% vs JS ${(jsAvgAcc * 100).toFixed(1)}%`);
        }

        const jsAvgRuntime = jsStats.runtimeMs.length > 0 ? jsStats.runtimeMs.reduce((a, b) => a + b, 0) / jsStats.runtimeMs.length : null;
        const tsAvgRuntime = tsStats.runtimeMs.length > 0 ? tsStats.runtimeMs.reduce((a, b) => a + b, 0) / tsStats.runtimeMs.length : null;

        if (jsAvgRuntime !== null && tsAvgRuntime !== null) {
          console.log(`   Runtime: TS ${tsAvgRuntime.toFixed(2)}ms vs JS ${jsAvgRuntime.toFixed(2)}ms`);
        }

        const jsAvgLines = jsStats.codeLines.length > 0 ? jsStats.codeLines.reduce((a, b) => a + b, 0) / jsStats.codeLines.length : null;
        const tsAvgLines = tsStats.codeLines.length > 0 ? tsStats.codeLines.reduce((a, b) => a + b, 0) / tsStats.codeLines.length : null;

        if (jsAvgLines !== null && tsAvgLines !== null) {
          console.log(`   Code size: TS ${tsAvgLines.toFixed(0)} vs JS ${jsAvgLines.toFixed(0)} lines`);
        }
      }
    }

    const { prompt, completion, total } = this.tokenUsage;
    if (prompt || completion || total) {
      console.log('\n🔢 Token Usage:');
      console.log(`   Prompt tokens:     ${prompt.toLocaleString().padStart(10)}`);
      console.log(`   Completion tokens: ${completion.toLocaleString().padStart(10)}`);
      console.log(`   Total tokens:      ${total.toLocaleString().padStart(10)}`);

      // Estimate cost (approximate, varies by provider)
      const estimatedCost = (prompt * 0.000003 + completion * 0.000015).toFixed(4);
      console.log(`   Estimated cost:    ~$${estimatedCost} (GPT-4 rates)`);
    }

    console.log('\n═══════════════════════════════════════════════════════════');
  }
}
