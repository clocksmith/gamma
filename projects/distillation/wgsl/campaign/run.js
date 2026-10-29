#!/usr/bin/env node
// Launch a campaign tool or test inside the Doppler-namespace view.
//
//   node run.js tools/<tool>.js [args...]   run one campaign tool
//   node run.js --test [tests/...test.js]   run campaign tests (all when none named)
//
// Paths are Doppler repository paths, exactly as the frozen policies use them.
// The launch contract (Doppler and Gamma revisions) goes to stderr.

import { spawnSync } from 'node:child_process';
import { readdirSync } from 'node:fs';
import { join, relative } from 'node:path';

import { CAMPAIGN_ROOT, NAMESPACE_ROOT, buildNamespace } from './namespace.js';

function discoverTests(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) return discoverTests(path);
    return entry.name.endsWith('.test.js') ? [relative(CAMPAIGN_ROOT, path)] : [];
  });
}

function run(args) {
  const env = { ...process.env };
  delete env.NODE_TEST_CONTEXT;
  const result = spawnSync(process.execPath, args, { cwd: NAMESPACE_ROOT, stdio: 'inherit', env });
  if (result.error) console.error(result.error.stack || String(result.error));
  return result.status ?? 1;
}

const argv = process.argv.slice(2);
if (!argv.length) {
  console.error('usage: node run.js tools/<tool>.js [args...] | node run.js --test [tests/...]');
  process.exit(2);
}
const receipt = buildNamespace();
console.error(`[campaign-namespace] ${JSON.stringify(receipt)}`);

if (argv[0] !== '--test') {
  process.exitCode = run(argv);
} else {
  // Doppler's node test bootstrap supplies WebGPU usage constants and the
  // file:// fetch shim, as in Doppler's own runner.
  const files = (argv.length > 1 ? argv.slice(1) : discoverTests(join(CAMPAIGN_ROOT, 'tests'))).sort();
  const failed = [];
  for (const file of files) {
    const status = run([
      '--test', '--test-force-exit', '--test-reporter=dot',
      '--import', join(NAMESPACE_ROOT, 'tools', 'node-test-file-bootstrap.js'),
      file,
    ]);
    console.log(`${status === 0 ? 'pass' : 'FAIL'} ${file}`);
    if (status !== 0) failed.push(file);
  }
  console.log(`\n${files.length - failed.length}/${files.length} test files passed`);
  if (failed.length) {
    console.log(`failed:\n${failed.map((file) => `  ${file}`).join('\n')}`);
    process.exitCode = 1;
  }
}
