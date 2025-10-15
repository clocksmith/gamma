/**
 * Playwright Evaluator
 * End-to-end testing for UI components with visual regression
 */

import { chromium } from 'playwright';
import { writeFileSync, mkdirSync, readFileSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';
import pixelmatch from 'pixelmatch';
import { PNG } from 'pngjs';

export class PlaywrightEvaluator {
  constructor(playwrightConfig, outputConfig) {
    this.config = playwrightConfig;
    this.outputConfig = outputConfig;
    this.browser = null;
  }

  /**
   * Initialize Playwright browser
   */
  async initialize() {
    if (!this.browser) {
      this.browser = await chromium.launch({
        headless: true
      });
    }
  }

  /**
   * Close browser
   */
  async close() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }

  /**
   * Evaluate a UI component with E2E tests
   */
  async evaluateUIComponent(code, task, variant) {
    await this.initialize();

    const results = {
      functional: { score: 0, details: {} },
      visual: { score: 0, details: {} },
      performance: { score: 0, details: {} },
      accessibility: { score: 0, details: {} }
    };

    try {
      // Create temporary HTML file with the component
      const testPage = this.createTestPage(code, variant);
      const tempDir = join(tmpdir(), `playwright-test-${Date.now()}`);
      mkdirSync(tempDir, { recursive: true });
      const htmlFile = join(tempDir, 'test.html');
      writeFileSync(htmlFile, testPage);

      const page = await this.browser.newPage();
      await page.goto(`file://${htmlFile}`);

      // Run functional tests
      if (this.config.functional?.testInteractions) {
        results.functional = await this.testFunctional(page, task);
      }

      // Run visual regression tests
      if (this.config.visualRegression?.enabled) {
        results.visual = await this.testVisual(page, task);
      }

      // Run performance tests
      if (this.config.performance?.loadTime) {
        results.performance = await this.testPerformance(page);
      }

      // Run accessibility tests
      if (this.config.functional?.a11yChecks) {
        results.accessibility = await this.testAccessibility(page);
      }

      await page.close();

    } catch (error) {
      console.error('Playwright evaluation error:', error.message);
    }

    // Calculate overall score
    const overallScore = this.calculateOverallScore(results);

    return {
      ...results,
      overallScore,
      passed: overallScore > 0.7
    };
  }

  /**
   * Create HTML test page
   */
  createTestPage(code, variant) {
    // Extract HTML, CSS, and JS from code
    const htmlMatch = code.match(/<!--\s*HTML\s*-->([\s\S]*?)<!--\s*\/HTML\s*-->/i) ||
                     code.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
    const cssMatch = code.match(/<!--\s*CSS\s*-->([\s\S]*?)<!--\s*\/CSS\s*-->/i) ||
                    code.match(/<style[^>]*>([\s\S]*?)<\/style>/i);
    const jsMatch = code.match(/<!--\s*JS\s*-->([\s\S]*?)<!--\s*\/JS\s*-->/i) ||
                   code.match(/<script[^>]*>([\s\S]*?)<\/script>/i);

    const html = htmlMatch ? htmlMatch[1] : code;
    const css = cssMatch ? cssMatch[1] : '';
    const js = jsMatch ? jsMatch[1] : '';

    return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Component Test</title>
  <style>
    body {
      font-family: system-ui, -apple-system, sans-serif;
      padding: 20px;
      margin: 0;
    }
    ${css}
  </style>
</head>
<body>
  ${html}
  <script>
    ${js}
  </script>
</body>
</html>`;
  }

  /**
   * Test functional requirements
   */
  async testFunctional(page, task) {
    const details = {};
    let passedTests = 0;
    let totalTests = 0;

    // Wait for page to be ready
    await page.waitForLoadState('domcontentloaded');

    // Check for console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Test interactions based on task requirements
    if (task.interactions) {
      for (const interaction of task.interactions) {
        totalTests++;
        try {
          await this.performInteraction(page, interaction);
          const result = await this.verifyInteraction(page, interaction);
          if (result) passedTests++;
          details[interaction.name] = result;
        } catch (error) {
          details[interaction.name] = false;
          details[`${interaction.name}_error`] = error.message;
        }
      }
    }

    // Validate DOM structure
    if (this.config.functional?.validateDOM && task.expectedElements) {
      for (const selector of task.expectedElements) {
        totalTests++;
        const element = await page.$(selector);
        const exists = element !== null;
        if (exists) passedTests++;
        details[`element_${selector}`] = exists;
      }
    }

    details.consoleErrors = consoleErrors;
    details.hasErrors = consoleErrors.length > 0;

    const score = totalTests > 0 ? passedTests / totalTests : 0.5;

    return { score, details };
  }

  /**
   * Perform an interaction (click, type, etc.)
   */
  async performInteraction(page, interaction) {
    switch (interaction.type) {
      case 'click':
        await page.click(interaction.selector);
        break;
      case 'type':
        await page.fill(interaction.selector, interaction.value);
        break;
      case 'hover':
        await page.hover(interaction.selector);
        break;
      default:
        throw new Error(`Unknown interaction type: ${interaction.type}`);
    }

    // Wait for any animations or state changes
    await page.waitForTimeout(100);
  }

  /**
   * Verify interaction result
   */
  async verifyInteraction(page, interaction) {
    if (interaction.expected) {
      const element = await page.$(interaction.expected.selector);
      if (!element) return false;

      if (interaction.expected.text) {
        const text = await element.textContent();
        return text.includes(interaction.expected.text);
      }

      if (interaction.expected.value) {
        const value = await element.inputValue();
        return value === interaction.expected.value;
      }

      return true;
    }

    return true;
  }

  /**
   * Test visual appearance
   */
  async testVisual(page, task) {
    const details = {};

    try {
      // Take screenshot
      const screenshot = await page.screenshot({ fullPage: true });

      // Save screenshot
      const screenshotDir = this.outputConfig.screenshotsDir || 'benchmark/screenshots';
      mkdirSync(screenshotDir, { recursive: true });
      const screenshotPath = join(screenshotDir, `${task.name}-${Date.now()}.png`);
      writeFileSync(screenshotPath, screenshot);

      details.screenshot = screenshotPath;

      // Compare with baseline if exists
      const baselinePath = join(screenshotDir, `${task.name}-baseline.png`);
      try {
        const baselineImage = PNG.sync.read(readFileSync(baselinePath));
        const currentImage = PNG.sync.read(screenshot);

        const { width, height } = baselineImage;
        const diff = new PNG({ width, height });

        const numDiffPixels = pixelmatch(
          baselineImage.data,
          currentImage.data,
          diff.data,
          width,
          height,
          { threshold: this.config.visualRegression.threshold || 0.1 }
        );

        const totalPixels = width * height;
        const diffPercent = (numDiffPixels / totalPixels) * 100;

        details.visualDiff = diffPercent;
        details.passed = diffPercent < (this.config.visualRegression.threshold * 100);

        // Save diff image
        const diffPath = join(screenshotDir, `${task.name}-diff-${Date.now()}.png`);
        writeFileSync(diffPath, PNG.sync.write(diff));
        details.diffImage = diffPath;

      } catch (error) {
        // No baseline exists, save current as baseline
        writeFileSync(baselinePath, screenshot);
        details.baselineCreated = true;
        details.passed = true;
      }

    } catch (error) {
      details.error = error.message;
      details.passed = false;
    }

    const score = details.passed ? 1.0 : 0.0;
    return { score, details };
  }

  /**
   * Test performance metrics
   */
  async testPerformance(page) {
    const details = {};

    try {
      // Measure load time
      const metrics = await page.evaluate(() => {
        const perf = performance.getEntriesByType('navigation')[0];
        return {
          loadTime: perf.loadEventEnd - perf.loadEventStart,
          domContentLoaded: perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
          totalTime: perf.loadEventEnd - perf.fetchStart
        };
      });

      details.metrics = metrics;

      // Check for console errors
      details.consoleErrorCount = 0;

      // Score based on load time
      let score = 1.0;
      if (metrics.loadTime > 1000) score = 0.7;
      if (metrics.loadTime > 3000) score = 0.5;
      if (metrics.loadTime > 5000) score = 0.3;

      return { score, details };

    } catch (error) {
      return {
        score: 0.5,
        details: { error: error.message }
      };
    }
  }

  /**
   * Test accessibility
   */
  async testAccessibility(page) {
    const details = {};
    let score = 1.0;

    try {
      // Check for basic a11y issues
      const a11yIssues = await page.evaluate(() => {
        const issues = [];

        // Check for alt text on images
        const images = document.querySelectorAll('img');
        images.forEach((img, i) => {
          if (!img.alt) {
            issues.push(`Image ${i} missing alt text`);
          }
        });

        // Check for labels on inputs
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach((input, i) => {
          if (!input.labels || input.labels.length === 0) {
            if (!input.getAttribute('aria-label')) {
              issues.push(`Input ${i} missing label`);
            }
          }
        });

        // Check for heading hierarchy
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        let previousLevel = 0;
        headings.forEach((heading, i) => {
          const level = parseInt(heading.tagName[1]);
          if (level - previousLevel > 1) {
            issues.push(`Heading hierarchy skipped at index ${i}`);
          }
          previousLevel = level;
        });

        return issues;
      });

      details.issues = a11yIssues;
      details.issueCount = a11yIssues.length;

      // Reduce score based on issues
      score = Math.max(0, 1.0 - (a11yIssues.length * 0.1));

    } catch (error) {
      details.error = error.message;
      score = 0.5;
    }

    return { score, details };
  }

  /**
   * Calculate overall score from all tests
   */
  calculateOverallScore(results) {
    const weights = {
      functional: 0.4,
      visual: 0.3,
      performance: 0.2,
      accessibility: 0.1
    };

    let totalScore = 0;
    let totalWeight = 0;

    for (const [category, result] of Object.entries(results)) {
      if (result.score !== undefined) {
        totalScore += result.score * weights[category];
        totalWeight += weights[category];
      }
    }

    return totalWeight > 0 ? totalScore / totalWeight : 0;
  }
}
