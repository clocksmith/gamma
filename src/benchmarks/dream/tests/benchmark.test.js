/**
 * Validation Tests for DREAM Benchmark Suite
 * Tests the benchmark infrastructure itself to ensure accurate measurements
 */

import { strict as assert } from 'assert';
import { Evaluator } from '../evaluator/evaluator.js';
import { StatisticalAnalyzer } from '../utils/statistical-analyzer.js';
import { ReportGenerator } from '../reports/report-generator.js';
import { hashCode, analyzeCodeVariation, calculateVariance } from '../utils/code-similarity.js';

// Test runner
async function runTests() {
  const tests = [];
  let passed = 0;
  let failed = 0;

  function test(name, fn) {
    tests.push({ name, fn });
  }

  // ============================================
  // Statistical Analyzer Tests
  // ============================================

  test('StatisticalAnalyzer.calculateStats returns correct mean', () => {
    const values = [2, 4, 6, 8, 10];
    const stats = StatisticalAnalyzer.calculateStats(values);
    assert.strictEqual(stats.mean, 6);
    assert.strictEqual(stats.count, 5);
  });

  test('StatisticalAnalyzer.calculateStats returns correct median', () => {
    const values = [1, 2, 3, 4, 5];
    const stats = StatisticalAnalyzer.calculateStats(values);
    assert.strictEqual(stats.median, 3);
  });

  test('StatisticalAnalyzer.calculateStats handles single value', () => {
    const stats = StatisticalAnalyzer.calculateStats([42]);
    assert.strictEqual(stats.mean, 42);
    assert.strictEqual(stats.count, 1);
    assert.strictEqual(stats.stdDev, 0);
  });

  test('StatisticalAnalyzer.calculateStats handles empty array', () => {
    const stats = StatisticalAnalyzer.calculateStats([]);
    assert.strictEqual(stats, null);
  });

  test('StatisticalAnalyzer.percentile returns correct values', () => {
    const sorted = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    assert.strictEqual(StatisticalAnalyzer.percentile(sorted, 50), 5.5);
    assert.strictEqual(StatisticalAnalyzer.percentile(sorted, 0), 1);
    assert.strictEqual(StatisticalAnalyzer.percentile(sorted, 100), 10);
  });

  test('StatisticalAnalyzer.confidenceInterval returns valid bounds', () => {
    const values = [10, 12, 11, 13, 9, 11, 10, 12];
    const ci = StatisticalAnalyzer.confidenceInterval(values, 0.95);
    assert.ok(ci.lower < ci.mean);
    assert.ok(ci.upper > ci.mean);
    assert.ok(ci.marginOfError > 0);
  });

  test('StatisticalAnalyzer.tTest detects significant difference', () => {
    const group1 = [10, 11, 12, 10, 11];
    const group2 = [20, 21, 22, 20, 21];
    const result = StatisticalAnalyzer.tTest(group1, group2);
    assert.ok(result.isSignificant);
    assert.ok(Math.abs(result.meanDiff) > 5);
  });

  test('StatisticalAnalyzer.tTest detects no significant difference', () => {
    const group1 = [10, 11, 12, 10, 11];
    const group2 = [10.1, 11.1, 12.1, 10.1, 11.1];
    const result = StatisticalAnalyzer.tTest(group1, group2);
    assert.ok(!result.isSignificant);
  });

  test('StatisticalAnalyzer.correlation returns valid coefficient', () => {
    const x = [1, 2, 3, 4, 5];
    const y = [2, 4, 6, 8, 10]; // Perfect positive correlation
    const result = StatisticalAnalyzer.correlation(x, y);
    assert.ok(result.coefficient > 0.99);
    assert.strictEqual(result.strength, 'very strong');
  });

  test('StatisticalAnalyzer.detectOutliers finds outliers', () => {
    const values = [10, 11, 12, 11, 10, 100]; // 100 is outlier
    const stats = StatisticalAnalyzer.calculateStats(values);
    assert.ok(stats.outliers.length > 0);
    assert.ok(stats.outliers.some(o => o.value === 100));
  });

  // ============================================
  // Code Similarity Tests
  // ============================================

  test('hashCode produces consistent hashes', () => {
    const code = 'function foo() { return 42; }';
    const hash1 = hashCode(code);
    const hash2 = hashCode(code);
    assert.strictEqual(hash1, hash2);
  });

  test('hashCode produces different hashes for different code', () => {
    const hash1 = hashCode('function foo() { return 1; }');
    const hash2 = hashCode('function bar() { return 2; }');
    assert.notStrictEqual(hash1, hash2);
  });

  test('calculateVariance returns correct statistics', () => {
    const values = [10, 20, 30, 40, 50];
    const result = calculateVariance(values);
    assert.strictEqual(result.mean, 30);
    assert.strictEqual(result.min, 10);
    assert.strictEqual(result.max, 50);
    assert.ok(result.stdDev > 0);
  });

  test('analyzeCodeVariation detects identical code', () => {
    const samples = [
      { code: 'const x = 1;', hash: hashCode('const x = 1;') },
      { code: 'const x = 1;', hash: hashCode('const x = 1;') },
      { code: 'const x = 1;', hash: hashCode('const x = 1;') }
    ];
    const result = analyzeCodeVariation(samples);
    assert.strictEqual(result.duplicateRate, 1);
    assert.strictEqual(result.uniqueOutputs, 1);
  });

  test('analyzeCodeVariation detects different code', () => {
    const samples = [
      { code: 'const x = 1;', hash: hashCode('const x = 1;') },
      { code: 'const x = 2;', hash: hashCode('const x = 2;') },
      { code: 'const x = 3;', hash: hashCode('const x = 3;') }
    ];
    const result = analyzeCodeVariation(samples);
    assert.strictEqual(result.duplicateRate, 0);
    assert.strictEqual(result.uniqueOutputs, 3);
  });

  // ============================================
  // Evaluator Tests
  // ============================================

  test('Evaluator extracts code from markdown', () => {
    const evaluator = new Evaluator({}, null);
    const content = 'Here is the code:\n```javascript\nfunction test() {}\n```\nDone.';
    const code = evaluator.extractCode(content, 'javascript');
    assert.ok(code.includes('function test()'));
  });

  test('Evaluator calculates complexity metrics', () => {
    const evaluator = new Evaluator({}, null);
    const code = `
      function test(x) {
        if (x > 0) {
          for (let i = 0; i < x; i++) {
            if (i % 2 === 0) {
              console.log(i);
            }
          }
        }
      }
    `;
    const metrics = evaluator.calculateComplexityMetrics(code);
    assert.ok(metrics.cyclomaticComplexity > 1);
    assert.ok(metrics.maxNestingDepth >= 3);
  });

  test('Evaluator calculates Levenshtein distance', () => {
    const evaluator = new Evaluator({}, null);
    const dist1 = evaluator.calculateLevenshteinDistance('kitten', 'sitting');
    assert.strictEqual(dist1, 3);

    const dist2 = evaluator.calculateLevenshteinDistance('abc', 'abc');
    assert.strictEqual(dist2, 0);
  });

  test('Evaluator estimates cost correctly', () => {
    const evaluator = new Evaluator({}, null);
    const cost = evaluator.estimateCost({ inputTokens: 1000, outputTokens: 500 });
    assert.ok(cost.totalCostUSD > 0);
    assert.ok(cost.inputCostUSD < cost.outputCostUSD); // Output typically costs more
  });

  test('Evaluator checks requirements correctly', () => {
    const evaluator = new Evaluator({}, null);
    const code = 'export async function fibonacci(n) { return n; }';
    const task = { requirements: ['function', 'export', 'async', 'fibonacci'] };
    const result = evaluator.evaluateCompleteness(code, task, 'javascript');
    assert.strictEqual(result.score, 1);
    assert.strictEqual(result.passedCount, 4);
  });

  // ============================================
  // Report Generator Tests
  // ============================================

  test('ReportGenerator.generateSummary calculates correct totals', () => {
    const results = [
      { success: true },
      { success: true },
      { success: false, skipped: false },
      { success: false, skipped: true }
    ];
    const summary = ReportGenerator.generateSummary(results);
    assert.strictEqual(summary.total, 4);
    assert.strictEqual(summary.passed, 2);
    assert.strictEqual(summary.failed, 1);
    assert.strictEqual(summary.skipped, 1);
  });

  test('ReportGenerator groups results correctly', () => {
    const generator = new ReportGenerator();
    const results = [
      { taskName: 'test1', provider: 'gpt4', variant: 'js', success: true },
      { taskName: 'test1', provider: 'gpt4', variant: 'js', success: true },
      { taskName: 'test1', provider: 'gpt4', variant: 'ts', success: true }
    ];
    const groups = generator.groupResults(results);
    assert.strictEqual(groups.size, 2);
    assert.strictEqual(groups.get('test1|gpt4|js').runs.length, 2);
    assert.strictEqual(groups.get('test1|gpt4|ts').runs.length, 1);
  });

  test('ReportGenerator computes metric stats correctly', () => {
    const generator = new ReportGenerator();
    const stats = generator.computeMetricStats([10, 20, 30], 'ms');
    assert.strictEqual(stats.n, 3);
    assert.strictEqual(stats.mean, 20);
    assert.strictEqual(stats.min, 10);
    assert.strictEqual(stats.max, 30);
    assert.strictEqual(stats.unit, 'ms');
  });

  test('ReportGenerator handles empty results', () => {
    const generator = new ReportGenerator();
    const report = generator.generateComprehensiveReport([]);
    assert.strictEqual(report.summary.total, 0);
  });

  // ============================================
  // Run all tests
  // ============================================

  console.log('\n🧪 Running DREAM Benchmark Validation Tests\n');
  console.log('═'.repeat(60));

  for (const { name, fn } of tests) {
    try {
      await fn();
      passed++;
      console.log(`✅ ${name}`);
    } catch (error) {
      failed++;
      console.log(`❌ ${name}`);
      console.log(`   Error: ${error.message}`);
    }
  }

  console.log('═'.repeat(60));
  console.log(`\n📊 Results: ${passed} passed, ${failed} failed, ${tests.length} total`);
  console.log(`   Pass rate: ${(passed / tests.length * 100).toFixed(1)}%\n`);

  if (failed > 0) {
    process.exit(1);
  }
}

// Run tests
runTests().catch(console.error);
