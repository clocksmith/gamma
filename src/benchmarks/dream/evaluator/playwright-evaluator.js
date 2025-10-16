import { chromium } from 'playwright';
import { writeFileSync, unlinkSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

export class PlaywrightEvaluator {
  constructor() {
    this.browser = null;
  }

  async initialize() {
    this.browser = await chromium.launch();
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
    }
  }

  async evaluateUIComponent(code, task, variant) {
    if (!this.browser) {
      throw new Error('PlaywrightEvaluator not initialized');
    }

    const context = await this.browser.newContext();
    const page = await context.newPage();

    const tempDir = tmpdir();
    const htmlFile = join(tempDir, `benchmark-${Date.now()}.html`);
    const scriptFile = join(tempDir, `benchmark-${Date.now()}.js`);

    try {
      // Create a simple HTML file
      const html = `
        <!DOCTYPE html>
        <html>
          <head>
            <title>Benchmark</title>
          </head>
          <body>
            <script src="./${scriptFile.split('/').pop()}"></script>
          </body>
        </html>
      `;
      writeFileSync(htmlFile, html);
      writeFileSync(scriptFile, code);

      await page.goto(`file://${htmlFile}`);

      // The test logic from the task will be executed here
      const testResult = await page.evaluate(async (testCases) => {
        let passed = 0;
        for (const testCase of testCases) {
          try {
            // This is a simplified version. We need a more robust way to execute the test.
            const result = await new Function(testCase.test)();
            if (result) {
              passed++;
            }
          } catch (e) {
            console.error(e);
          }
        }
        return { passed, total: testCases.length };
      }, task.testCases);

      const overallScore = testResult.passed / testResult.total;

      return { overallScore };
    } finally {
      await page.close();
      await context.close();
      unlinkSync(htmlFile);
      unlinkSync(scriptFile);
    }
  }
}