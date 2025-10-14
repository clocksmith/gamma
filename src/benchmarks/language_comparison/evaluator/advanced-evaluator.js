/**
 * Advanced Evaluator
 * Comprehensive evaluation with statistical analysis, multiple runs, and E2E testing
 */

import { execSync, exec } from 'child_process';
import { writeFileSync, unlinkSync, mkdirSync, readFileSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

export class AdvancedEvaluator {
  constructor(evaluationConfig, playwrightConfig) {
    this.config = evaluationConfig;
    this.playwrightConfig = playwrightConfig;
  }

  /**
   * Evaluate with multiple runs and statistical analysis
   */
  async evaluateWithStatistics(task, responses, variant, durations) {
    const evaluations = [];

    // Evaluate each run
    for (let i = 0; i < responses.length; i++) {
      const evaluation = await this.evaluateSingleRun(
        task,
        responses[i],
        variant,
        durations[i]
      );
      evaluations.push(evaluation);
    }

    // Calculate statistics across runs
    const statistics = this.calculateStatistics(evaluations);

    // Calculate final score with consistency penalty/bonus
    const finalScore = this.calculateFinalScore(evaluations, statistics);

    return {
      evaluations,
      statistics,
      finalScore,
      summary: {
        avgScore: statistics.scores.mean,
        stdDev: statistics.scores.stdDev,
        consistency: statistics.consistency,
        variance: statistics.scores.variance
      }
    };
  }

  /**
   * Evaluate a single run
   */
  async evaluateSingleRun(task, response, variant, duration) {
    const scores = {
      accuracy: 0,
      performance: 0,
      codeQuality: 0,
      completeness: 0
    };

    const code = this.extractCode(response.content, variant);
    const codeMetrics = this.calculateCodeMetrics(code, response, duration);

    // Accuracy evaluation with enhanced scoring
    if (task.testCases) {
      scores.accuracy = await this.evaluateTestCasesWithDetails(
        code,
        task.testCases,
        variant
      );
    }

    // Performance scoring
    scores.performance = this.evaluatePerformance(response.usage);

    // Code quality
    scores.codeQuality = await this.evaluateCodeQuality(code, variant);

    // Completeness
    scores.completeness = this.evaluateCompleteness(response.content, task);

    const totalScore = Object.entries(scores).reduce((total, [criterion, score]) => {
      const weight = this.config[criterion] || 0;
      return total + (score * weight * 100);
    }, 0);

    return {
      scores,
      totalScore,
      metrics: codeMetrics,
      code
    };
  }

  /**
   * Enhanced test case evaluation with partial credit
   */
  async evaluateTestCasesWithDetails(code, testCases, variant) {
    let totalScore = 0;
    const results = [];

    for (const testCase of testCases) {
      const result = await this.runSingleTest(code, testCase, variant);
      results.push(result);

      if (result.passed) {
        totalScore += 1.0;
      } else if (this.config.accuracyScoring?.partialCredit) {
        // Award partial credit for close answers
        totalScore += this.calculatePartialCredit(result);
      }
    }

    return testCases.length > 0 ? totalScore / testCases.length : 0;
  }

  /**
   * Run a single test case with detailed error capture
   */
  async runSingleTest(code, testCase, variant) {
    try {
      const tempDir = join(tmpdir(), `benchmark-test-${Date.now()}-${Math.random()}`);
      mkdirSync(tempDir, { recursive: true });

      const ext = variant === 'typescript' ? 'ts' : 'js';
      const tempFile = join(tempDir, `test.${ext}`);

      // Create test file with code + test case
      const testCode = `
${code}

// Test case
try {
  ${testCase.test}
  console.log('PASS');
} catch (error) {
  console.log('FAIL:', error.message);
  console.log('ACTUAL:', error.actual);
  console.log('EXPECTED:', error.expected);
}
`;
      writeFileSync(tempFile, testCode);

      let output;
      if (variant === 'typescript') {
        output = execSync(`npx tsx ${tempFile}`, {
          cwd: tempDir,
          encoding: 'utf-8',
          timeout: 5000
        });
      } else {
        output = execSync(`node ${tempFile}`, {
          encoding: 'utf-8',
          timeout: 5000
        });
      }

      // Clean up
      try {
        unlinkSync(tempFile);
      } catch (e) {
        // Ignore cleanup errors
      }

      const passed = output.includes('PASS');
      return {
        passed,
        output,
        test: testCase.test
      };

    } catch (error) {
      return {
        passed: false,
        error: error.message,
        test: testCase.test
      };
    }
  }

  /**
   * Calculate partial credit for close answers
   */
  calculatePartialCredit(result) {
    // Parse output to see if answer was close
    if (result.output) {
      // Extract actual and expected values if available
      const actualMatch = result.output.match(/ACTUAL:\s*(\S+)/);
      const expectedMatch = result.output.match(/EXPECTED:\s*(\S+)/);

      if (actualMatch && expectedMatch) {
        const actual = parseFloat(actualMatch[1]);
        const expected = parseFloat(expectedMatch[1]);

        if (!isNaN(actual) && !isNaN(expected)) {
          const percentError = Math.abs((actual - expected) / expected);

          // Award partial credit based on proximity
          if (percentError < 0.01) return 0.9;      // Within 1%
          if (percentError < 0.05) return 0.7;      // Within 5%
          if (percentError < 0.10) return 0.5;      // Within 10%
          if (percentError < 0.25) return 0.3;      // Within 25%
        }
      }
    }

    return 0;
  }

  /**
   * Calculate statistics across multiple runs
   */
  calculateStatistics(evaluations) {
    const scores = evaluations.map(e => e.totalScore);
    const accuracyScores = evaluations.map(e => e.scores.accuracy);

    return {
      scores: {
        mean: this.mean(scores),
        median: this.median(scores),
        stdDev: this.standardDeviation(scores),
        variance: this.variance(scores),
        min: Math.min(...scores),
        max: Math.max(...scores),
        range: Math.max(...scores) - Math.min(...scores)
      },
      accuracy: {
        mean: this.mean(accuracyScores),
        stdDev: this.standardDeviation(accuracyScores),
        consistency: 1 - this.standardDeviation(accuracyScores)
      },
      consistency: this.calculateConsistencyScore(evaluations),
      codeVariability: this.calculateCodeVariability(evaluations)
    };
  }

  /**
   * Calculate consistency score (how similar are the outputs)
   */
  calculateConsistencyScore(evaluations) {
    if (evaluations.length < 2) return 1.0;

    // Compare code similarity across runs
    let totalSimilarity = 0;
    let comparisons = 0;

    for (let i = 0; i < evaluations.length; i++) {
      for (let j = i + 1; j < evaluations.length; j++) {
        totalSimilarity += this.calculateCodeSimilarity(
          evaluations[i].code,
          evaluations[j].code
        );
        comparisons++;
      }
    }

    return comparisons > 0 ? totalSimilarity / comparisons : 1.0;
  }

  /**
   * Calculate code variability (are all outputs different?)
   */
  calculateCodeVariability(evaluations) {
    const uniqueCodes = new Set(evaluations.map(e =>
      this.normalizeCode(e.code)
    ));

    return uniqueCodes.size / evaluations.length;
  }

  /**
   * Normalize code for comparison
   */
  normalizeCode(code) {
    return code
      .replace(/\/\/.*|\/\*[\s\S]*?\*\//g, '') // Remove comments
      .replace(/\s+/g, ' ')                      // Normalize whitespace
      .trim()
      .toLowerCase();
  }

  /**
   * Calculate code similarity between two snippets
   */
  calculateCodeSimilarity(code1, code2) {
    const norm1 = this.normalizeCode(code1);
    const norm2 = this.normalizeCode(code2);

    if (norm1 === norm2) return 1.0;

    // Simple similarity based on common characters
    const maxLen = Math.max(norm1.length, norm2.length);
    if (maxLen === 0) return 1.0;

    const minLen = Math.min(norm1.length, norm2.length);
    let commonChars = 0;

    for (let i = 0; i < minLen; i++) {
      if (norm1[i] === norm2[i]) commonChars++;
    }

    return commonChars / maxLen;
  }

  /**
   * Calculate final score with consistency adjustments
   */
  calculateFinalScore(evaluations, statistics) {
    let baseScore = statistics.scores.mean;

    if (this.config.consistencyScoring?.enabled) {
      // Penalize high variance
      const variancePenalty = statistics.scores.variance *
        (this.config.consistencyScoring.variancePenalty || 0);

      baseScore -= variancePenalty;

      // Bonus for high consistency
      if (statistics.consistency > 0.9) {
        baseScore += this.config.consistencyScoring.determinismBonus || 0;
      }
    }

    return Math.max(0, Math.min(100, baseScore));
  }

  // Statistical helper functions
  mean(values) {
    return values.reduce((sum, v) => sum + v, 0) / values.length;
  }

  median(values) {
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 === 0
      ? (sorted[mid - 1] + sorted[mid]) / 2
      : sorted[mid];
  }

  variance(values) {
    const avg = this.mean(values);
    return values.reduce((sum, v) => sum + Math.pow(v - avg, 2), 0) / values.length;
  }

  standardDeviation(values) {
    return Math.sqrt(this.variance(values));
  }

  /**
   * Extract code from LLM response
   */
  extractCode(content, variant) {
    const codeBlockRegex = /```(?:typescript|javascript|ts|js)?\n([\s\S]*?)```/g;
    const matches = [...content.matchAll(codeBlockRegex)];

    if (matches.length > 0) {
      return matches.map(m => m[1]).join('\n\n');
    }

    return content;
  }

  /**
   * Calculate code metrics
   */
  calculateCodeMetrics(code, response, duration) {
    const lines = code.split('\n');
    const nonEmptyLines = lines.filter(line => line.trim().length > 0);
    const codeOnlyLines = nonEmptyLines.filter(line => {
      const trimmed = line.trim();
      return !trimmed.startsWith('//') && !trimmed.startsWith('/*') && !trimmed.startsWith('*');
    });

    const usage = response.usage || {};
    const outputTokens = usage.completion_tokens || usage.output_tokens || 0;
    const tokensPerSecond = duration ? (outputTokens / (duration / 1000)).toFixed(2) : 0;

    return {
      codeLength: {
        totalLines: lines.length,
        codeLines: codeOnlyLines.length,
        commentLines: nonEmptyLines.length - codeOnlyLines.length
      },
      tokenMetrics: {
        outputTokens,
        tokensPerSecond: parseFloat(tokensPerSecond)
      }
    };
  }

  /**
   * Evaluate performance
   */
  evaluatePerformance(usage) {
    if (!usage) return 0.5;

    const totalTokens = usage.total_tokens || (usage.input_tokens + usage.output_tokens);

    if (totalTokens < 500) return 1.0;
    if (totalTokens < 1000) return 0.9;
    if (totalTokens < 2000) return 0.7;
    if (totalTokens < 3000) return 0.5;
    return 0.3;
  }

  /**
   * Evaluate code quality
   */
  async evaluateCodeQuality(code, variant) {
    let score = 0.5;

    const checks = {
      hasComments: /\/\/|\/\*/.test(code),
      hasProperIndentation: this.checkIndentation(code),
      hasDescriptiveNames: this.checkNaming(code),
      noConsoleLog: !/console\.log/.test(code),
      hasErrorHandling: /try|catch|throw|Error/.test(code)
    };

    const passedChecks = Object.values(checks).filter(v => v).length;
    score = passedChecks / Object.keys(checks).length;

    return score;
  }

  checkIndentation(code) {
    const lines = code.split('\n').filter(line => line.trim());
    if (lines.length === 0) return true;

    const indentPattern = /^(\s+)/;
    const indents = lines
      .map(line => {
        const match = line.match(indentPattern);
        return match ? match[1].length : 0;
      })
      .filter(len => len > 0);

    if (indents.length === 0) return true;

    const isConsistent = indents.every(indent => indent % 2 === 0);
    return isConsistent;
  }

  checkNaming(code) {
    const varPattern = /(?:const|let|var|function)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)/g;
    const matches = [...code.matchAll(varPattern)];

    if (matches.length === 0) return true;

    const descriptiveNames = matches.filter(m => {
      const name = m[1];
      if (/^[ijkn]$/.test(name)) return true;
      return name.length > 2;
    });

    return descriptiveNames.length / matches.length > 0.7;
  }

  /**
   * Evaluate completeness
   */
  evaluateCompleteness(response, task) {
    const content = response.toLowerCase();
    let score = 0.5;

    if (task.requirements) {
      const met = task.requirements.filter(req =>
        content.includes(req.toLowerCase())
      );
      score = met.length / task.requirements.length;
    }

    if (response.length < 100) score *= 0.5;

    return Math.min(score, 1.0);
  }
}
