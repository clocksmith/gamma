/**
 * Advanced Code Metrics Calculator
 * Provides creative and sophisticated code analysis metrics
 */

import { parseSync } from '@babel/core';

export class AdvancedMetrics {
  /**
   * Calculate cyclomatic complexity of code
   * Measures the number of linearly independent paths through the code
   */
  static calculateCyclomaticComplexity(code) {
    try {
      let complexity = 1; // Base complexity

      // Count decision points
      const patterns = [
        /\bif\b/g,
        /\belse\s+if\b/g,
        /\bfor\b/g,
        /\bwhile\b/g,
        /\bcase\b/g,
        /\bcatch\b/g,
        /\b\&\&\b/g,
        /\b\|\|\b/g,
        /\?\s*.*?\s*:/g, // Ternary operators
      ];

      for (const pattern of patterns) {
        const matches = code.match(pattern);
        if (matches) {
          complexity += matches.length;
        }
      }

      return {
        complexity,
        rating: this.complexityRating(complexity)
      };
    } catch (error) {
      return { complexity: 0, rating: 'unknown', error: error.message };
    }
  }

  /**
   * Rate complexity level
   */
  static complexityRating(complexity) {
    if (complexity <= 5) return 'simple';
    if (complexity <= 10) return 'moderate';
    if (complexity <= 20) return 'complex';
    return 'very complex';
  }

  /**
   * Calculate type safety score for TypeScript/JSDoc code
   */
  static calculateTypeSafetyScore(code, variant) {
    const metrics = {
      score: 0,
      details: {
        hasTypeAnnotations: false,
        typeAnnotationCoverage: 0,
        hasInterfaces: false,
        hasEnums: false,
        hasGenerics: false,
        strictNullChecks: false,
        noImplicitAny: false
      }
    };

    // TypeScript-specific patterns
    if (variant.includes('typescript')) {
      // Type annotations
      const typeAnnotations = code.match(/:\s*\w+(\[\]|<.*?>)?/g) || [];
      metrics.details.typeAnnotationCoverage = typeAnnotations.length;
      metrics.details.hasTypeAnnotations = typeAnnotations.length > 0;

      // Interfaces
      metrics.details.hasInterfaces = /interface\s+\w+/.test(code);

      // Enums
      metrics.details.hasEnums = /enum\s+\w+/.test(code);

      // Generics
      metrics.details.hasGenerics = /<[A-Z]\w*(?:,\s*[A-Z]\w*)*>/.test(code);

      // Strict null checks (presence of ? or ! operators)
      metrics.details.strictNullChecks = /\?\.|!\.|\?:/.test(code);

      // No implicit any (explicit types on parameters)
      const functionParams = code.match(/\([^)]*\)/g) || [];
      const typedParams = functionParams.filter(p => p.includes(':')).length;
      metrics.details.noImplicitAny = functionParams.length > 0 &&
        typedParams / functionParams.length > 0.8;

      // Calculate score
      let score = 0;
      if (metrics.details.hasTypeAnnotations) score += 30;
      if (metrics.details.hasInterfaces) score += 20;
      if (metrics.details.hasEnums) score += 10;
      if (metrics.details.hasGenerics) score += 15;
      if (metrics.details.strictNullChecks) score += 10;
      if (metrics.details.noImplicitAny) score += 15;
      metrics.score = Math.min(score, 100);

    } else if (variant.includes('jsdoc')) {
      // JSDoc type annotations
      const jsdocTypes = code.match(/@(?:param|returns?|type)\s+\{[^}]+\}/g) || [];
      metrics.details.typeAnnotationCoverage = jsdocTypes.length;
      metrics.details.hasTypeAnnotations = jsdocTypes.length > 0;

      // Calculate score for JSDoc
      metrics.score = Math.min(jsdocTypes.length * 20, 70); // Max 70 for JSDoc
    }

    return metrics;
  }

  /**
   * Calculate maintainability index
   * Based on Halstead volume, cyclomatic complexity, and lines of code
   */
  static calculateMaintainabilityIndex(code) {
    const loc = code.split('\n').filter(line => line.trim().length > 0).length;
    const cyclomaticComplexity = this.calculateCyclomaticComplexity(code).complexity;
    const halsteadVolume = this.calculateHalsteadVolume(code);

    // Maintainability Index formula (simplified)
    // MI = 171 - 5.2 * ln(V) - 0.23 * CC - 16.2 * ln(LOC)
    const mi = 171 -
      5.2 * Math.log(halsteadVolume || 1) -
      0.23 * cyclomaticComplexity -
      16.2 * Math.log(loc || 1);

    const normalized = Math.max(0, Math.min(100, mi));

    return {
      index: normalized,
      rating: this.maintainabilityRating(normalized),
      components: {
        linesOfCode: loc,
        cyclomaticComplexity,
        halsteadVolume
      }
    };
  }

  /**
   * Rate maintainability
   */
  static maintainabilityRating(index) {
    if (index >= 85) return 'highly maintainable';
    if (index >= 65) return 'maintainable';
    if (index >= 50) return 'moderately maintainable';
    return 'difficult to maintain';
  }

  /**
   * Calculate Halstead complexity measures
   */
  static calculateHalsteadVolume(code) {
    // Count operators and operands
    const operators = code.match(/[+\-*/%=<>!&|^~?:;,.\[\]{}()]/g) || [];
    const operands = code.match(/\b[a-zA-Z_$][a-zA-Z0-9_$]*\b/g) || [];

    const uniqueOperators = new Set(operators).size;
    const uniqueOperands = new Set(operands).size;

    const n1 = uniqueOperators;
    const n2 = uniqueOperands;
    const N1 = operators.length;
    const N2 = operands.length;

    // Program vocabulary
    const n = n1 + n2;
    // Program length
    const N = N1 + N2;

    // Volume
    const V = N * Math.log2(n || 1);

    return V;
  }

  /**
   * Analyze code readability using various heuristics
   */
  static analyzeReadability(code) {
    const lines = code.split('\n').filter(line => line.trim());
    const avgLineLength = lines.reduce((sum, line) => sum + line.length, 0) / (lines.length || 1);

    // Comment ratio
    const commentLines = lines.filter(line => {
      const trimmed = line.trim();
      return trimmed.startsWith('//') || trimmed.startsWith('/*') || trimmed.startsWith('*');
    }).length;
    const commentRatio = commentLines / (lines.length || 1);

    // Nesting depth
    const maxNesting = this.calculateMaxNestingDepth(code);

    // Identifier length (good names are descriptive)
    const identifiers = code.match(/\b[a-zA-Z_$][a-zA-Z0-9_$]*\b/g) || [];
    const avgIdentifierLength = identifiers.reduce((sum, id) => sum + id.length, 0) /
      (identifiers.length || 1);

    // Calculate readability score (0-100)
    let score = 50; // Base score

    // Adjust for average line length (prefer 40-80 chars)
    if (avgLineLength >= 40 && avgLineLength <= 80) score += 15;
    else if (avgLineLength < 40 || avgLineLength > 120) score -= 10;

    // Adjust for comments
    if (commentRatio >= 0.1 && commentRatio <= 0.3) score += 15;
    else if (commentRatio < 0.05) score -= 10;

    // Adjust for nesting depth
    if (maxNesting <= 3) score += 10;
    else if (maxNesting > 5) score -= 15;

    // Adjust for identifier length
    if (avgIdentifierLength >= 5 && avgIdentifierLength <= 15) score += 10;
    else if (avgIdentifierLength < 3) score -= 10;

    return {
      score: Math.max(0, Math.min(100, score)),
      metrics: {
        avgLineLength: avgLineLength.toFixed(1),
        commentRatio: (commentRatio * 100).toFixed(1) + '%',
        maxNestingDepth: maxNesting,
        avgIdentifierLength: avgIdentifierLength.toFixed(1)
      },
      rating: score >= 75 ? 'highly readable' :
              score >= 60 ? 'readable' :
              score >= 40 ? 'moderately readable' : 'hard to read'
    };
  }

  /**
   * Calculate maximum nesting depth
   */
  static calculateMaxNestingDepth(code) {
    let maxDepth = 0;
    let currentDepth = 0;

    for (const char of code) {
      if (char === '{') {
        currentDepth++;
        maxDepth = Math.max(maxDepth, currentDepth);
      } else if (char === '}') {
        currentDepth--;
      }
    }

    return maxDepth;
  }

  /**
   * Analyze code for potential bugs and code smells
   */
  static analyzeBugRisk(code) {
    const issues = [];
    let riskScore = 0;

    // Check for common issues
    const checks = [
      { pattern: /==(?!=)/g, issue: 'Loose equality (==) used instead of strict (===)', risk: 2 },
      { pattern: /var\s+/g, issue: 'var keyword used instead of let/const', risk: 1 },
      { pattern: /eval\(/g, issue: 'eval() usage detected (security risk)', risk: 5 },
      { pattern: /console\.log/g, issue: 'console.log() left in code', risk: 1 },
      { pattern: /TODO|FIXME|HACK/gi, issue: 'TODO/FIXME comments found', risk: 2 },
      { pattern: /\bcatch\s*\(\s*\w*\s*\)\s*\{\s*\}/g, issue: 'Empty catch blocks', risk: 3 },
      { pattern: /parseInt\([^,)]+\)/g, issue: 'parseInt without radix', risk: 2 },
      { pattern: /\+\+|\-\-/g, issue: 'Increment/decrement operators (potential confusion)', risk: 1 },
      { pattern: /with\s*\(/g, issue: 'with statement (deprecated)', risk: 4 },
      { pattern: /arguments\.callee/g, issue: 'arguments.callee usage (deprecated)', risk: 3 }
    ];

    for (const check of checks) {
      const matches = code.match(check.pattern);
      if (matches) {
        issues.push({
          issue: check.issue,
          count: matches.length,
          risk: check.risk
        });
        riskScore += matches.length * check.risk;
      }
    }

    return {
      riskScore,
      riskLevel: riskScore === 0 ? 'low' :
                 riskScore < 10 ? 'moderate' :
                 riskScore < 20 ? 'high' : 'critical',
      issues,
      issueCount: issues.length
    };
  }

  /**
   * Analyze test coverage indicators
   * (Heuristic based on presence of test-like code)
   */
  static analyzeTestCoverage(code) {
    const testPatterns = [
      /\btest\(/gi,
      /\bit\(/gi,
      /\bdescribe\(/gi,
      /\bexpect\(/gi,
      /\bassert/gi,
      /console\.assert/gi
    ];

    const testIndicators = testPatterns.reduce((sum, pattern) => {
      const matches = code.match(pattern);
      return sum + (matches ? matches.length : 0);
    }, 0);

    const hasTests = testIndicators > 0;
    const estimatedCoverage = Math.min(testIndicators * 15, 100);

    return {
      hasTests,
      testIndicatorCount: testIndicators,
      estimatedCoverage,
      rating: estimatedCoverage >= 80 ? 'excellent' :
              estimatedCoverage >= 60 ? 'good' :
              estimatedCoverage >= 30 ? 'fair' : 'poor'
    };
  }

  /**
   * Calculate code duplication score
   */
  static analyzeCodeDuplication(code) {
    const lines = code.split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 10); // Only consider significant lines

    const duplicates = new Map();
    const lineCount = lines.length;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (duplicates.has(line)) {
        duplicates.set(line, duplicates.get(line) + 1);
      } else {
        duplicates.set(line, 1);
      }
    }

    const duplicatedLines = Array.from(duplicates.values())
      .filter(count => count > 1)
      .reduce((sum, count) => sum + count, 0);

    const duplicationRatio = lineCount > 0 ? duplicatedLines / lineCount : 0;

    return {
      duplicationRatio: (duplicationRatio * 100).toFixed(2) + '%',
      duplicatedLineCount: duplicatedLines,
      totalLines: lineCount,
      rating: duplicationRatio < 0.05 ? 'minimal' :
              duplicationRatio < 0.15 ? 'acceptable' :
              duplicationRatio < 0.30 ? 'concerning' : 'high'
    };
  }

  /**
   * Analyze dependency complexity
   */
  static analyzeDependencies(code) {
    // Count imports
    const importStatements = code.match(/^import\s+.*?from\s+['"][^'"]+['"]/gm) || [];
    const requireStatements = code.match(/require\s*\(['"][^'"]+['"]\)/g) || [];

    const totalDependencies = importStatements.length + requireStatements.length;

    // Analyze types of dependencies
    const externalDeps = [...importStatements, ...requireStatements].filter(dep =>
      !dep.includes('./') && !dep.includes('../')
    ).length;

    const internalDeps = totalDependencies - externalDeps;

    return {
      total: totalDependencies,
      external: externalDeps,
      internal: internalDeps,
      complexity: totalDependencies < 5 ? 'simple' :
                  totalDependencies < 15 ? 'moderate' :
                  totalDependencies < 30 ? 'complex' : 'very complex'
    };
  }

  /**
   * Comprehensive code analysis combining all metrics
   */
  static analyzeCode(code, variant) {
    return {
      complexity: this.calculateCyclomaticComplexity(code),
      typeSafety: this.calculateTypeSafetyScore(code, variant),
      maintainability: this.calculateMaintainabilityIndex(code),
      readability: this.analyzeReadability(code),
      bugRisk: this.analyzeBugRisk(code),
      testCoverage: this.analyzeTestCoverage(code),
      duplication: this.analyzeCodeDuplication(code),
      dependencies: this.analyzeDependencies(code),
      timestamp: new Date().toISOString()
    };
  }
}
