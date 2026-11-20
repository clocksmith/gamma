// Real Chromium: one clean run per arm of each differentiation suite completes, judged by the fixture's records.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const RUNNER = fileURLToPath(new URL('../../qualification/differentiate.js', import.meta.url));
const RUN_TIME_LIMIT_MS = 120000;
const browserArgs = process.env.FAWN_WORKSPACE_TEST_BROWSER_CHANNEL
  ? ['--browser-channel', process.env.FAWN_WORKSPACE_TEST_BROWSER_CHANNEL] : [];

const SUITES = Object.freeze({ differentiation: 'agent-clean', revalidatedDifferentiation: 'helpdesk-clean' });

for (const [suite, scenario] of Object.entries(SUITES)) {
  const outDir = join(mkdtempSync(join(tmpdir(), 'fawn-differentiation-test-')), 'result');
  const ran = spawnSync(process.execPath, [RUNNER, '--suite', suite, '--out', outDir, '--scenarios', scenario, '--repetitions', '1', ...browserArgs], {
    encoding: 'utf8',
    timeout: RUN_TIME_LIMIT_MS,
    killSignal: 'SIGKILL',
  });
  assert.equal(ran.status, 0, `differentiation process failed (${ran.signal ?? ran.status})\n${ran.stdout}\n${ran.stderr}`);
  const result = JSON.parse(readFileSync(join(outDir, 'differentiation.json'), 'utf8'));
  assert.equal(result.scope, 'subset');
  assert.equal(result.productAdvantage.established, false, 'a subset never establishes product advantage');
  assert.equal(result.sameBrowserBinary, true);
  for (const row of result.rows) assert.equal(row.taskSuccess, true, `${suite} ${row.arm}: ${JSON.stringify(row.details)}\n${ran.stdout}`);
  assert.deepEqual(result.rows.map((row) => row.arm).sort(), ['control', 'treatment']);
}
console.log('ok: clean runs of both differentiation suites on both arms');
