// The runner must run every test file in each suite directory, whatever its module extension.

import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const TEST_ROOT = fileURLToPath(new URL('..', import.meta.url));
const listed = spawnSync(process.execPath, [`${TEST_ROOT}run-tests.js`, '--browser', '--list'], { encoding: 'utf8', timeout: 10000 });
assert.equal(listed.status, 0, listed.stderr);
const selected = listed.stdout.split('\n').filter(Boolean).sort();
const expected = ['unit', 'browser'].flatMap(suite => readdirSync(`${TEST_ROOT}${suite}`)
  .filter(name => /\.test\.[cm]?js$/.test(name)).map(name => `${suite}/${name}`)).sort();
assert.ok(expected.some(name => name.endsWith('.test.mjs')), 'the suite holds .test.mjs files');
assert.deepEqual(selected, expected);
console.log(`run-tests selection: ${selected.length} files`);
