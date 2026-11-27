#!/usr/bin/env node
// Blitzen workspace test runner: unit tests by default; `--browser` adds real-Chromium workflows.
//
// Each file runs in its own process with a time limit so a stuck browser cannot hang the run.
// `--list` prints the selected files without running them.

import { spawnSync } from 'node:child_process';
import { readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const TEST_ROOT = fileURLToPath(new URL('.', import.meta.url));
const FILE_TIME_LIMIT_MS = 180000;
const SUITES = Object.freeze({ unit: 'unit', browser: 'browser' });
// Test files are ES modules under either extension (`.test.js` with the package type, or `.test.mjs`).
const TEST_FILE = /\.test\.[cm]?js$/;
const listOnly = process.argv.includes('--list');
const channelIndex = process.argv.indexOf('--browser-channel');
const browserChannel = channelIndex === -1 ? null : process.argv[channelIndex + 1];
if (channelIndex !== -1 && (!browserChannel || browserChannel.startsWith('--'))) {
  throw new Error('--browser-channel requires a channel');
}
const env = { ...process.env,
  ...(browserChannel ? {
    BLITZEN_TEST_BROWSER_CHANNEL: browserChannel,
    FAWN_WORKSPACE_TEST_BROWSER_CHANNEL: browserChannel,
  } : {}) };

const suites = process.argv.includes('--browser') ? [SUITES.unit, SUITES.browser] : [SUITES.unit];
let failures = 0, ran = 0;
for (const suite of suites) {
  const directory = `${TEST_ROOT}${suite}`;
  for (const file of readdirSync(directory).filter((name) => TEST_FILE.test(name)).sort()) {
    if (listOnly) { console.log(`${suite}/${file}`); continue; }
    ran++;
    const result = spawnSync(process.execPath, [`${directory}/${file}`], {
      stdio: 'inherit',
      timeout: FILE_TIME_LIMIT_MS,
      killSignal: 'SIGKILL',
      env,
    });
    if (result.status !== 0) {
      failures++;
      console.error(`FAIL: ${suite}/${file} (${result.signal ?? `exit ${result.status}`})`);
    }
  }
}
if (!listOnly) console.log(`run-tests: ${ran} files, ${ran - failures} passed, ${failures} failed`);
process.exit(failures === 0 ? 0 : 1);
