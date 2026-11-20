// Tests name their stock control explicitly. Selecting a Fawn profile exercises the same
// product admission boundary without altering the frozen service configuration.
import { loadClientServiceConfig } from '../../src/client/browser-selection.js';

export function testBrowserSelection(directory) {
  const browserConfig = process.env.BLITZEN_TEST_BROWSER_CONFIG ?? process.env.FAWN_WORKSPACE_TEST_BROWSER_CONFIG;
  const selection = browserConfig ? { browserConfig, browserChannel: 'fawn' }
    : { browserChannel: process.env.BLITZEN_TEST_BROWSER_CHANNEL ?? process.env.FAWN_WORKSPACE_TEST_BROWSER_CHANNEL ?? 'chrome' };
  return { selection, config: loadClientServiceConfig({ directory, ...selection, headless: true }) };
}
