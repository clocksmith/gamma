/**
 * Evaluator
 * Evaluates LLM responses against expected outputs and criteria
 */

import { execSync } from 'child_process';
import { writeFileSync, unlinkSync, mkdirSync, rmSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

// Playwright is optional - only needed for UI component testing
let PlaywrightEvaluator = null;
// Don't try to import if playwright is not available
// This avoids module parsing errors when playwright is not installed

export class Evaluator {
  constructor(evaluationConfig, playwrightEvaluator) {
    this.config = evaluationConfig;
    this.playwrightEvaluator = playwrightEvaluator;
    this.dryRun = false;
  }

  setDryRun(value) {
    this.dryRun = Boolean(value);
  }

  async evaluate(task, response, variant, duration) {
    const scores = {
      accuracy: 0,
      performance: 0,
      codeQuality: 0,
      completeness: 0
    };

    // Additional LLM benchmark metrics
    const advancedMetrics = {
      f1Score: 0,
      precision: 0,
      recall: 0,
      exactMatch: 0
    };

    const code = this.extractCode(response.content, variant);
    const codeMetrics = this.calculateCodeMetrics(code, response, duration);

    // Calculate code complexity metrics
    const complexityMetrics = this.calculateComplexityMetrics(code);
    codeMetrics.complexity = complexityMetrics;

    // Calculate edit distance and AST similarity if reference code exists
    if (task.referenceCode && task.referenceCode[variant]) {
      const refCode = task.referenceCode[variant];
      const editDistance = this.calculateLevenshteinDistance(code, refCode);
      const maxLen = Math.max(code.length, refCode.length);
      const astSimilarity = this.calculateASTSimilarity(code, refCode);

      codeMetrics.editDistance = editDistance;
      codeMetrics.editSimilarity = 1 - (editDistance / maxLen);
      codeMetrics.astSimilarity = astSimilarity;

      // Store in advanced metrics for reporting
      advancedMetrics.editSimilarity = codeMetrics.editSimilarity;
      advancedMetrics.astSimilarity = astSimilarity;
    }

    if (task.interactions || task.expectedElements) {
      if (this.playwrightEvaluator) {
        const playwrightResult = await this.playwrightEvaluator.evaluateUIComponent(code, task, variant);
        scores.accuracy = playwrightResult.overallScore;
      } else {
        console.warn('⚠️  Playwright not installed - skipping UI component evaluation');
        scores.accuracy = 0.5; // Neutral score
      }
    } else {
      if (task.testCases) {
        const testResult = await this.evaluateTestCases(code, task.testCases, variant);
        if (typeof testResult === 'object') {
          // New detailed format with F1/Precision/Recall
          scores.accuracy = testResult.accuracy;
          advancedMetrics.f1Score = testResult.f1;
          advancedMetrics.precision = testResult.precision;
          advancedMetrics.recall = testResult.recall;
          codeMetrics.testResults = {
            passed: testResult.passed,
            failed: testResult.failed,
            total: testResult.total
          };
        } else {
          // Legacy format
          scores.accuracy = testResult;
        }
      } else if (task.expectedOutput) {
        scores.accuracy = await this.evaluateAccuracy(code, task, variant);
      } else if (task.bugLocation) {
        scores.accuracy = await this.evaluateBugFinding(response.content, task.bugLocation);
      } else if (task.needleText) {
        scores.accuracy = await this.evaluateNeedleInHaystack(response.content, task.needleText, task.needleLocation);
      } else if (task.expectedAnalysis) {
        scores.accuracy = this.evaluateAnalysis(response.content, task.expectedAnalysis);
      }
    }

    const performanceResult = await this.evaluatePerformance(code, task, variant, response.usage);
    scores.performance = performanceResult.overallScore;
    const codeQualityScore = await this.evaluateCodeQuality(code, variant);
    scores.codeQuality = codeQualityScore.score;
    scores.completeness = this.evaluateCompleteness(response.content, task);

    const totalScore = Object.entries(scores).reduce((total, [criterion, score]) => {
      const weight = this.config?.[criterion]?.weight || 0;
      return total + (score * weight);
    }, 0) * 100;

    // Add runtime performance metrics if available
    if (performanceResult.runtimeMetrics) {
      codeMetrics.runtimePerformance = performanceResult.runtimeMetrics;
    }
    codeMetrics.performanceBreakdown = {
      tokenEfficiency: performanceResult.tokenScore,
      runtime: performanceResult.runtimeScore
    };
    codeMetrics.codeQualityDetails = codeQualityScore.details;

    return {
      scores,
      performanceBreakdown: {
        tokenEfficiency: performanceResult.tokenScore,
        runtime: performanceResult.runtimeScore
      },
      advancedMetrics,
      totalScore,
      metrics: codeMetrics,
      details: { code, variant }
    };
  }

  calculateCodeMetrics(code, response, duration) {
    const lines = code.split('\n');
    const nonEmptyLines = lines.filter(line => line.trim().length > 0);
    const codeOnlyLines = nonEmptyLines.filter(line => {
      const trimmed = line.trim();
      return !trimmed.startsWith('//') && !trimmed.startsWith('/*') && !trimmed.startsWith('*');
    });

    const usage = response.usage || {};
    const outputTokens = usage.completion_tokens || usage.output_tokens || 0;
    const inputTokens = usage.prompt_tokens || usage.input_tokens || 0;
    const totalTokens = usage.total_tokens || (inputTokens + outputTokens);
    const tokensPerSecond = duration ? (outputTokens / (duration / 1000)).toFixed(2) : 0;
    const totalChars = code.length;
    const codeChars = code.replace(/\/\/.*|\/\*[\s\S]*?\*\//g, '').replace(/\s/g, '').length;

    return {
      codeLength: { totalLines: lines.length, nonEmptyLines: nonEmptyLines.length, codeLines: codeOnlyLines.length, commentLines: nonEmptyLines.length - codeOnlyLines.length, totalCharacters: totalChars, codeCharacters: codeChars },
      tokenMetrics: { inputTokens, outputTokens, totalTokens, tokensPerSecond: parseFloat(tokensPerSecond), charactersPerToken: outputTokens > 0 ? (totalChars / outputTokens).toFixed(2) : 0 },
      efficiency: { timeMs: duration || 0, timeSeconds: duration ? (duration / 1000).toFixed(2) : 0, linesPerSecond: duration ? (codeOnlyLines.length / (duration / 1000)).toFixed(2) : 0 }
    };
  }

  extractCode(content, variant) {
    const codeBlockRegex = /```(?:typescript|javascript|ts|js)?\n([\s\S]*?)```/g;
    const matches = [...content.matchAll(codeBlockRegex)];
    if (matches.length > 0) {
      return matches.map(m => m[1]).join('\n\n');
    }
    return content;
  }

  _createTestRunnerCode(testCases, codeExt) {
    const testFns = testCases.map(tc => `async () => { ${tc.test} }`).join(',\n');
    return `
      import * as mod from './module${codeExt}';

      for (const key in mod) {
        global[key] = mod[key];
      }
      if (mod.default) {
        const name = mod.default.name || 'defaultExport';
        global[name] = mod.default;
      }

      const testCases = [${testFns}];

      async function runTests() {
        let passedCount = 0;
        for (let i = 0; i < testCases.length; i++) {
          try {
            await testCases[i]();
            passedCount++;
          } catch (e) {
            console.error(\`Test case \${i + 1} failed: \${e.message}\`);
          }
        }
        if (passedCount !== testCases.length) {
          console.error(\`\${testCases.length - passedCount} test(s) failed.\`);
          process.exit(1);
        }
        console.log(\`\${passedCount}/\${testCases.length} tests passed.\`);
      }

      runTests();
    `;
  }

  async evaluateTestCases(code, testCases, variant) {
    if (this.dryRun) {
      return {
        accuracy: 1.0,
        precision: 1.0,
        recall: 1.0,
        f1: 1.0,
        passed: testCases.length,
        failed: 0,
        total: testCases.length
      };
    }

    const tempDir = join(tmpdir(), `benchmark-${Date.now()}`);
    mkdirSync(tempDir, { recursive: true });

    try {
      const isTs = variant === 'typescript';
      const codeExt = isTs ? '.ts' : '.mjs';
      const runnerExt = isTs ? '.ts' : '.mjs';

      const codeFile = join(tempDir, `module${codeExt}`);
      writeFileSync(codeFile, code);

      const runnerFile = join(tempDir, `runner${runnerExt}`);
      const runnerCode = this._createTestRunnerCodeWithDetails(testCases, codeExt);
      writeFileSync(runnerFile, runnerCode);

      const command = isTs ? `npx tsx ${runnerFile}` : `node ${runnerFile}`;
      const output = execSync(command, { cwd: tempDir, stdio: 'pipe', encoding: 'utf-8' });

      // Parse detailed results for F1/Precision/Recall calculation
      try {
        const resultLine = output.split('\n').find(line => line.startsWith('RESULTS:'));
        if (resultLine) {
          const results = JSON.parse(resultLine.replace('RESULTS:', ''));
          return {
            accuracy: results.passedCount / results.totalCount,
            precision: results.passedCount / Math.max(1, results.passedCount + results.falsePositives),
            recall: results.passedCount / results.totalCount,
            f1: this._calculateF1(results.passedCount, results.totalCount, results.falsePositives),
            passed: results.passedCount,
            failed: results.failedCount,
            total: results.totalCount
          };
        }
      } catch (parseError) {
        // Fallback to simple accuracy
      }

      return { accuracy: 1.0, precision: 1.0, recall: 1.0, f1: 1.0, passed: testCases.length, failed: 0, total: testCases.length };
    } catch (error) {
      console.warn(`One or more test cases failed to execute or pass.`);
      return { accuracy: 0, precision: 0, recall: 0, f1: 0, passed: 0, failed: testCases.length, total: testCases.length };
    } finally {
      rmSync(tempDir, { recursive: true, force: true });
    }
  }

  _calculateF1(truePositives, totalPositives, falsePositives) {
    const precision = truePositives / Math.max(1, truePositives + falsePositives);
    const recall = truePositives / Math.max(1, totalPositives);
    if (precision + recall === 0) return 0;
    return (2 * precision * recall) / (precision + recall);
  }

  _createTestRunnerCodeWithDetails(testCases, codeExt) {
    const testFns = testCases.map(tc => `async () => { ${tc.test} }`).join(',\n');
    return `
      import * as mod from './module${codeExt}';

      for (const key in mod) {
        global[key] = mod[key];
      }
      if (mod.default) {
        const name = mod.default.name || 'defaultExport';
        global[name] = mod.default;
      }

      const testCases = [${testFns}];

      async function runTests() {
        let passedCount = 0;
        let failedCount = 0;
        for (let i = 0; i < testCases.length; i++) {
          try {
            await testCases[i]();
            passedCount++;
          } catch (e) {
            failedCount++;
          }
        }

        // Output detailed results
        console.log('RESULTS:' + JSON.stringify({
          passedCount,
          failedCount,
          totalCount: testCases.length,
          falsePositives: 0 // Can be enhanced if we have negative test cases
        }));

        if (passedCount !== testCases.length) {
          process.exit(1);
        }
      }

      runTests();
    `;
  }

  async evaluateAccuracy(code, task, variant) {
    // This is a simpler evaluator, you might want to deprecate or merge with evaluateTestCases
    return 0;
  }

  async evaluateBugFinding(response, bugLocation) {
    const normalizedResponse = response.toLowerCase();
    const normalizedLocation = bugLocation.toLowerCase();
    if (normalizedResponse.includes(normalizedLocation)) {
      return 1.0;
    }
    const keywords = normalizedLocation.split(/\s+/);
    const matchedKeywords = keywords.filter(kw => normalizedResponse.includes(kw));
    return matchedKeywords.length / keywords.length;
  }

  async evaluateNeedleInHaystack(response, needleText, needleLocation) {
    const normalizedResponse = response.toLowerCase();
    const normalizedNeedle = needleText.toLowerCase();
    if (normalizedResponse.includes(normalizedNeedle)) {
      if (needleLocation && normalizedResponse.includes(needleLocation.toLowerCase())) {
        return 1.0;
      }
      return 0.7;
    }
    return 0;
  }

  evaluateAnalysis(content, expectedPhrases) {
    const lowerContent = content.toLowerCase();
    let foundCount = 0;
    for (const phrase of expectedPhrases) {
      if (lowerContent.includes(phrase.toLowerCase())) {
        foundCount++;
      }
    }
    return expectedPhrases.length > 0 ? foundCount / expectedPhrases.length : 0;
  }

  /**
   * Measure actual runtime performance: CPU time and memory usage
   * Runs the generated code multiple times and measures execution metrics
   */
  async evaluateRuntimePerformance(code, task, variant) {
    if (this.dryRun) {
      return { score: 0.5, metrics: null };
    }

    // Check if task has performance benchmarks defined
    if (!task.performanceBenchmarks || task.performanceBenchmarks.length === 0) {
      return { score: 0.5, metrics: null }; // Neutral score if no benchmarks defined
    }

    const tempDir = join(tmpdir(), `benchmark-perf-${Date.now()}`);
    mkdirSync(tempDir, { recursive: true });

    try {
      const isTs = variant.includes('typescript');
      const codeExt = isTs ? '.ts' : '.mjs';
      const codeFile = join(tempDir, `module${codeExt}`);
      writeFileSync(codeFile, code);

      const results = [];

      for (const benchmark of task.performanceBenchmarks) {
        const perfCode = `
          import * as mod from './module${codeExt}';

          // Make exports available globally
          for (const key in mod) {
            global[key] = mod[key];
          }
          if (mod.default) {
            const name = mod.default.name || 'defaultExport';
            global[name] = mod.default;
          }

          const iterations = ${benchmark.iterations || 10};
          const fn = ${benchmark.setup || 'null'};

          const timings = [];
          const memoryUsages = [];

          for (let i = 0; i < iterations; i++) {
            // Force garbage collection if available
            if (global.gc) global.gc();

            const memBefore = process.memoryUsage();
            const startTime = process.hrtime.bigint();

            // Run the benchmark
            ${benchmark.code}

            const endTime = process.hrtime.bigint();
            const memAfter = process.memoryUsage();

            const durationNs = Number(endTime - startTime);
            const memoryDelta = memAfter.heapUsed - memBefore.heapUsed;

            timings.push(durationNs);
            memoryUsages.push(memoryDelta);
          }

          // Calculate statistics
          const meanTime = timings.reduce((a, b) => a + b, 0) / timings.length;
          const meanMemory = memoryUsages.reduce((a, b) => a + b, 0) / memoryUsages.length;

          console.log(JSON.stringify({
            meanTimeNs: meanTime,
            meanMemoryBytes: meanMemory,
            timings,
            memoryUsages
          }));
        `;

        const perfFile = join(tempDir, `perf${codeExt}`);
        writeFileSync(perfFile, perfCode);

        try {
          const command = isTs ? `npx tsx ${perfFile}` : `node --expose-gc ${perfFile}`;
          const output = execSync(command, { cwd: tempDir, encoding: 'utf-8', timeout: 10000 });
          const perfData = JSON.parse(output.trim());

          results.push({
            name: benchmark.name,
            meanTimeMs: perfData.meanTimeNs / 1_000_000,
            meanMemoryMB: perfData.meanMemoryBytes / (1024 * 1024),
            rawData: perfData
          });
        } catch (error) {
          // Performance test failed, return penalty score
          results.push({
            name: benchmark.name,
            meanTimeMs: Infinity,
            meanMemoryMB: Infinity,
            error: error.message
          });
        }
      }

      // Calculate score based on performance relative to baseline
      let score = 0;
      for (let i = 0; i < results.length; i++) {
        const result = results[i];
        const benchmark = task.performanceBenchmarks[i];

        if (result.error) {
          score += 0; // Failed benchmark
          continue;
        }

        // Score based on time (if baseline provided)
        if (benchmark.baselineTimeMs) {
          const timeRatio = benchmark.baselineTimeMs / result.meanTimeMs;
          const timeScore = Math.min(1.0, Math.max(0, timeRatio)); // Faster than baseline = 1.0
          score += timeScore * 0.7; // 70% weight on time
        } else {
          // Generic scoring: < 1ms = 1.0, < 10ms = 0.9, < 100ms = 0.7, < 1000ms = 0.5
          if (result.meanTimeMs < 1) score += 1.0 * 0.7;
          else if (result.meanTimeMs < 10) score += 0.9 * 0.7;
          else if (result.meanTimeMs < 100) score += 0.7 * 0.7;
          else if (result.meanTimeMs < 1000) score += 0.5 * 0.7;
          else score += 0.3 * 0.7;
        }

        // Score based on memory (if baseline provided)
        if (benchmark.baselineMemoryMB) {
          const memRatio = benchmark.baselineMemoryMB / result.meanMemoryMB;
          const memScore = Math.min(1.0, Math.max(0, memRatio)); // Less memory than baseline = 1.0
          score += memScore * 0.3; // 30% weight on memory
        } else {
          // Generic scoring: < 1MB = 1.0, < 10MB = 0.9, < 50MB = 0.7, < 100MB = 0.5
          if (result.meanMemoryMB < 1) score += 1.0 * 0.3;
          else if (result.meanMemoryMB < 10) score += 0.9 * 0.3;
          else if (result.meanMemoryMB < 50) score += 0.7 * 0.3;
          else if (result.meanMemoryMB < 100) score += 0.5 * 0.3;
          else score += 0.3 * 0.3;
        }
      }

      score = score / results.length; // Average across all benchmarks

      return { score, metrics: results };
    } catch (error) {
      console.warn(`Runtime performance evaluation failed: ${error.message}`);
      return { score: 0.5, metrics: null };
    } finally {
      rmSync(tempDir, { recursive: true, force: true });
    }
  }

  /**
   * Evaluate token efficiency (code conciseness)
   * This is what the old "performance" metric measured
   */
  evaluateTokenEfficiency(usage) {
    if (!usage) return 0.5;
    const totalTokens = usage.total_tokens || (usage.input_tokens + usage.output_tokens);
    if (totalTokens < 500) return 1.0;
    if (totalTokens < 1000) return 0.9;
    if (totalTokens < 2000) return 0.7;
    if (totalTokens < 3000) return 0.5;
    return 0.3;
  }

  /**
   * Evaluate performance - intelligently choose between runtime and token efficiency
   */
  async evaluatePerformance(code, task, variant, usage) {
    const tokenScore = this.evaluateTokenEfficiency(usage);
    let runtimeScore = null;
    let runtimeMetrics = null;

    if (task.performanceBenchmarks && task.performanceBenchmarks.length > 0) {
      const runtimeResult = await this.evaluateRuntimePerformance(code, task, variant);
      runtimeScore = runtimeResult.score;
      runtimeMetrics = runtimeResult.metrics;
    }

    const overallScore = runtimeScore !== null
      ? (tokenScore + runtimeScore) / 2
      : tokenScore;

    return {
      overallScore,
      tokenScore,
      runtimeScore,
      runtimeMetrics
    };
  }

  async evaluateCodeQuality(code, variant) {
    const docRequired = /jsdoc|tsdoc/i.test(variant);
    const naming = this.checkNaming(code);
    const indentation = this.checkIndentation(code);
    const lineLength = this.checkLineLength(code);

    const checks = {
      indentation: indentation.pass,
      descriptiveNaming: naming.pass,
      usesConstLet: !/\bvar\s+/.test(code),
      noConsoleLogging: !/console\.(log|error|warn)/.test(code),
      strictEquality: !(/[^=]==[^=]/.test(code) && !/===/.test(code)),
      errorHandling: /try\s*\{|catch\s*\(|throw\s+|reject\(/.test(code),
      documentation: docRequired ? /\/\*\*/.test(code) : true,
      lineLength: lineLength.pass
    };

    const passedChecks = Object.values(checks).filter(Boolean).length;
    const score = passedChecks / Object.keys(checks).length;

    return {
      score,
      details: {
        checks,
        namingRatio: naming.ratio,
        indentation: indentation.metadata,
        lineLength: lineLength.metadata
      }
    };
  }

  checkIndentation(code) {
    const lines = code.split('\n').filter(line => line.trim());
    if (lines.length < 3) {
      return { pass: true, metadata: { commonIndent: null } };
    }
    const indentPattern = /^(\s+)/;
    const indents = lines.map(line => line.match(indentPattern)?.[1].length || 0).filter(len => len > 0);
    if (indents.length < 2) {
      return { pass: true, metadata: { commonIndent: null } };
    }
    const commonIndent = indents.reduce((a, b) => a < b ? a : b);
    if (commonIndent === 0) {
      return { pass: true, metadata: { commonIndent: 0 } };
    }
    const aligned = indents.every(indent => indent % commonIndent === 0);
    return { pass: aligned, metadata: { commonIndent } };
  }

  checkNaming(code) {
    const varPattern = /(?:const|let|var|function)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)/g;
    const matches = [...code.matchAll(varPattern)];
    if (matches.length === 0) {
      return { pass: true, ratio: 1 };
    }
    const descriptiveNames = matches.filter(m => {
      const name = m[1];
      if (/^[ijkn]$/.test(name)) return true;
      return name.length > 2;
    });
    const ratio = descriptiveNames.length / matches.length;
    return { pass: ratio >= 0.7, ratio };
  }

  checkLineLength(code, max = 120) {
    const lines = code.split('\n');
    const longest = lines.reduce((acc, line) => Math.max(acc, line.length), 0);
    return {
      pass: longest <= max,
      metadata: { maxAllowed: max, longest }
    };
  }

  evaluateCompleteness(response, task) {
    const content = response.toLowerCase();
    if (!task.requirements || task.requirements.length === 0) return 0.5;
    const met = task.requirements.filter(req => content.includes(req.toLowerCase()));
    let score = met.length / task.requirements.length;
    if (response.length < 100) score *= 0.5;
    return Math.min(score, 1.0);
  }

  /**
   * Calculate Levenshtein distance between two strings
   */
  calculateLevenshteinDistance(str1, str2) {
    const len1 = str1.length;
    const len2 = str2.length;
    const matrix = Array(len1 + 1).fill(null).map(() => Array(len2 + 1).fill(0));

    for (let i = 0; i <= len1; i++) matrix[i][0] = i;
    for (let j = 0; j <= len2; j++) matrix[0][j] = j;

    for (let i = 1; i <= len1; i++) {
      for (let j = 1; j <= len2; j++) {
        const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
        matrix[i][j] = Math.min(
          matrix[i - 1][j] + 1,      // deletion
          matrix[i][j - 1] + 1,      // insertion
          matrix[i - 1][j - 1] + cost // substitution
        );
      }
    }

    return matrix[len1][len2];
  }

  /**
   * Calculate code complexity metrics
   * Includes: Cyclomatic Complexity, Halstead Metrics, Lines of Code metrics
   */
  calculateComplexityMetrics(code) {
    const lines = code.split('\n');
    const codeLines = lines.filter(line => {
      const trimmed = line.trim();
      return trimmed.length > 0 &&
             !trimmed.startsWith('//') &&
             !trimmed.startsWith('/*') &&
             !trimmed.startsWith('*');
    });

    // Cyclomatic Complexity - count decision points
    const decisionKeywords = /\b(if|else if|for|while|case|catch|\?\s|&&|\|\|)\b/g;
    const decisionMatches = code.match(decisionKeywords) || [];
    const cyclomaticComplexity = decisionMatches.length + 1; // Start at 1 for single path

    // Halstead Metrics
    const halstead = this._calculateHalsteadMetrics(code);

    // Maintainability Index (simplified version)
    // MI = 171 - 5.2 * ln(Halstead Volume) - 0.23 * cyclomatic - 16.2 * ln(LOC)
    const loc = codeLines.length || 1;
    const volume = halstead.volume || 1;
    const maintainabilityIndex = Math.max(0,
      171 - 5.2 * Math.log(volume) - 0.23 * cyclomaticComplexity - 16.2 * Math.log(loc)
    );

    // Nesting depth
    const maxNestingDepth = this._calculateMaxNestingDepth(code);

    // Average line length
    const avgLineLength = codeLines.length > 0
      ? codeLines.reduce((sum, line) => sum + line.trim().length, 0) / codeLines.length
      : 0;

    return {
      cyclomaticComplexity,
      halsteadDifficulty: halstead.difficulty,
      halsteadVolume: halstead.volume,
      halsteadEffort: halstead.effort,
      maintainabilityIndex: Math.round(maintainabilityIndex),
      maxNestingDepth,
      avgLineLength: Math.round(avgLineLength),
      linesOfCode: loc
    };
  }

  /**
   * Calculate Halstead complexity metrics
   */
  _calculateHalsteadMetrics(code) {
    // Operators (simplified regex for common programming operators)
    const operatorPattern = /(\+\+|--|&&|\|\||==|!=|<=|>=|=>|\+=|-=|\*=|\/=|%=|<<=|>>=|&=|\|=|\^=|[+\-*\/%<>=!&|^~?:,;.(){}[\]])/g;
    const operators = code.match(operatorPattern) || [];

    // Operands (identifiers and literals)
    const operandPattern = /\b[a-zA-Z_$][a-zA-Z0-9_$]*\b|0x[0-9a-fA-F]+|0b[01]+|\d+\.?\d*|'[^']*'|"[^"]*"|`[^`]*`/g;
    const operands = code.match(operandPattern) || [];

    // Filter out language keywords from operands
    const keywords = new Set(['if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break',
                              'continue', 'return', 'function', 'const', 'let', 'var', 'import',
                              'export', 'class', 'extends', 'new', 'this', 'super', 'static',
                              'async', 'await', 'try', 'catch', 'finally', 'throw', 'typeof',
                              'instanceof', 'void', 'delete', 'in', 'of', 'null', 'undefined',
                              'true', 'false']);

    const filteredOperands = operands.filter(op => !keywords.has(op));

    const uniqueOperators = new Set(operators);
    const uniqueOperands = new Set(filteredOperands);

    const n1 = uniqueOperators.size;  // Number of distinct operators
    const n2 = uniqueOperands.size;   // Number of distinct operands
    const N1 = operators.length;      // Total operators
    const N2 = filteredOperands.length; // Total operands

    // Avoid division by zero
    if (n1 === 0 || n2 === 0) {
      return { difficulty: 0, volume: 0, effort: 0 };
    }

    const vocabulary = n1 + n2;
    const length = N1 + N2;
    const volume = length * Math.log2(vocabulary);
    const difficulty = (n1 / 2) * (N2 / n2);
    const effort = difficulty * volume;

    return {
      difficulty: Math.round(difficulty * 100) / 100,
      volume: Math.round(volume * 100) / 100,
      effort: Math.round(effort * 100) / 100
    };
  }

  /**
   * Calculate maximum nesting depth
   */
  _calculateMaxNestingDepth(code) {
    let maxDepth = 0;
    let currentDepth = 0;

    for (let char of code) {
      if (char === '{' || char === '(') {
        currentDepth++;
        maxDepth = Math.max(maxDepth, currentDepth);
      } else if (char === '}' || char === ')') {
        currentDepth = Math.max(0, currentDepth - 1);
      }
    }

    return maxDepth;
  }

  /**
   * Calculate simplified AST-based similarity
   * This is a lightweight version - for full TSED, we'd need a proper AST parser
   */
  calculateASTSimilarity(code1, code2) {
    // Extract structural features (simplified AST representation)
    const features1 = this._extractStructuralFeatures(code1);
    const features2 = this._extractStructuralFeatures(code2);

    // Calculate feature-wise similarity
    let totalSimilarity = 0;
    let featureCount = 0;

    for (const key in features1) {
      if (features2[key] !== undefined) {
        const diff = Math.abs(features1[key] - features2[key]);
        const max = Math.max(features1[key], features2[key], 1);
        totalSimilarity += 1 - (diff / max);
        featureCount++;
      }
    }

    return featureCount > 0 ? totalSimilarity / featureCount : 0;
  }

  _extractStructuralFeatures(code) {
    return {
      functions: (code.match(/function\s+\w+/g) || []).length,
      classes: (code.match(/class\s+\w+/g) || []).length,
      loops: (code.match(/\b(for|while|do)\b/g) || []).length,
      conditionals: (code.match(/\bif\b/g) || []).length,
      imports: (code.match(/\b(import|require)\b/g) || []).length,
      exports: (code.match(/\b(export|module\.exports)\b/g) || []).length,
      arrows: (code.match(/=>/g) || []).length,
      async: (code.match(/\basync\b/g) || []).length,
      promises: (code.match(/\b(then|catch|Promise)\b/g) || []).length,
      returns: (code.match(/\breturn\b/g) || []).length,
    };
  }
}
