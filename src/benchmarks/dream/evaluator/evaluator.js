/**
 * Evaluator
 * Evaluates LLM responses against expected outputs and criteria
 */

import { execSync } from 'child_process';
import { writeFileSync, unlinkSync, mkdirSync, rmdirSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';
import { PlaywrightEvaluator } from './playwright-evaluator.js';

export class Evaluator {
  constructor(evaluationConfig, playwrightEvaluator) {
    this.config = evaluationConfig;
    this.playwrightEvaluator = playwrightEvaluator;
  }

  async evaluate(task, response, variant, duration) {
    const scores = {
      accuracy: 0,
      performance: 0,
      codeQuality: 0,
      completeness: 0
    };

    const code = this.extractCode(response.content, variant);
    const codeMetrics = this.calculateCodeMetrics(code, response, duration);

    if (task.interactions || task.expectedElements) {
      const playwrightResult = await this.playwrightEvaluator.evaluateUIComponent(code, task, variant);
      scores.accuracy = playwrightResult.overallScore;
    } else {
      if (task.testCases) {
        scores.accuracy = await this.evaluateTestCases(code, task.testCases, variant);
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

    scores.performance = this.evaluatePerformance(response.usage);
    scores.codeQuality = await this.evaluateCodeQuality(code, variant);
    scores.completeness = this.evaluateCompleteness(response.content, task);

    const totalScore = Object.entries(scores).reduce((total, [criterion, score]) => {
      const weight = this.config?.weights?.[criterion] || 0;
      return total + (score * weight);
    }, 0) * 100;

    return {
      scores,
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
    const tempDir = join(tmpdir(), `benchmark-${Date.now()}`);
    mkdirSync(tempDir, { recursive: true });

    try {
      const isTs = variant === 'typescript';
      const codeExt = isTs ? '.ts' : '.mjs';
      const runnerExt = isTs ? '.ts' : '.mjs';

      const codeFile = join(tempDir, `module${codeExt}`);
      writeFileSync(codeFile, code);

      const runnerFile = join(tempDir, `runner${runnerExt}`);
      const runnerCode = this._createTestRunnerCode(testCases, codeExt);
      writeFileSync(runnerFile, runnerCode);

      const command = isTs ? `npx tsx ${runnerFile}` : `node ${runnerFile}`;
      execSync(command, { cwd: tempDir, stdio: 'pipe', encoding: 'utf-8' });
      return 1.0; // All tests passed
    } catch (error) {
      console.warn(`One or more test cases failed to execute or pass.`);
      return 0; // Assume all failed if the runner throws
    } finally {
      rmdirSync(tempDir, { recursive: true, force: true });
    }
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

  evaluatePerformance(usage) {
    if (!usage) return 0.5;
    const totalTokens = usage.total_tokens || (usage.input_tokens + usage.output_tokens);
    if (totalTokens < 500) return 1.0;
    if (totalTokens < 1000) return 0.9;
    if (totalTokens < 2000) return 0.7;
    if (totalTokens < 3000) return 0.5;
    return 0.3;
  }

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
    if (lines.length < 3) return true;
    const indentPattern = /^(\s+)/;
    const indents = lines.map(line => line.match(indentPattern)?.[1].length || 0).filter(len => len > 0);
    if (indents.length < 2) return true;
    const commonIndent = indents.reduce((a, b) => a < b ? a : b);
    if (commonIndent === 0) return true;
    return indents.every(indent => indent % commonIndent === 0);
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

  evaluateCompleteness(response, task) {
    const content = response.toLowerCase();
    if (!task.requirements || task.requirements.length === 0) return 0.5;
    const met = task.requirements.filter(req => content.includes(req.toLowerCase()));
    let score = met.length / task.requirements.length;
    if (response.length < 100) score *= 0.5;
    return Math.min(score, 1.0);
  }
}
