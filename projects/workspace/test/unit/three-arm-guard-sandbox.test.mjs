import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { chmodSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { GUARD_IMAGE, runGuard } from '../../qualification/workflow-generalization/three-arm/guard-sandbox.mjs';

let dockerReady = false;
try { execFileSync('docker', ['image', 'inspect', GUARD_IMAGE], { stdio: 'ignore', timeout: 8000 }); dockerReady = true; } catch { /* skip */ }
const options = { skip: dockerReady ? false : `docker image ${GUARD_IMAGE} not available` };
const route = { familyId: 'f', project: 'p', workPackageId: 7, workHours: 24 };

function guardDir(source) {
  const dir = mkdtempSync(join(tmpdir(), 'guard-'));
  chmodSync(dir, 0o755);
  writeFileSync(join(dir, 'guard.mjs'), source, { mode: 0o644 });
  return dir;
}
async function withGuard(source, run) {
  const dir = guardDir(source);
  try { return await run(dir); } finally { rmSync(dir, { recursive: true, force: true }); }
}

test('a guard reads through get and its answer comes back', options, async () => {
  const asked = [];
  const get = async path => { asked.push(path); return { ok: true, status: 200, body: { estimatedTime: 'PT24H' } }; };
  const result = await withGuard(`export async function decide({ workPackageId, workHours, get }) {
    console.log('noise on stdout must not break the exchange');
    const r = await get('/api/v3/work_packages/' + workPackageId);
    return r.body.estimatedTime === 'PT' + workHours + 'H' ? { decision: 'write', reason: 'match' } : { decision: 'stop', reason: 'differs' };
  }`, dir => runGuard({ guardDir: dir, route, get }));
  assert.equal(result.decision, 'write');
  assert.equal(result.reason, 'match');
  assert.equal(result.reads, 1);
  assert.deepEqual(asked, ['/api/v3/work_packages/7']);
});

test('a guard has no network and cannot write files; failing is a stop', options, async () => {
  const network = await withGuard(`export async function decide() {
    await fetch('http://example.com/');
    return { decision: 'write' };
  }`, dir => runGuard({ guardDir: dir, route, get: async () => ({}) }));
  assert.equal(network.decision, 'stop');
  assert.match(network.error, /fetch failed|ENOTFOUND|EAI_AGAIN|ENETUNREACH/);
  const disk = await withGuard(`import { writeFileSync } from 'node:fs';
  export async function decide() { writeFileSync('/guard/x', '1'); writeFileSync('/tmp/x', '1'); return { decision: 'write' }; }`,
  dir => runGuard({ guardDir: dir, route, get: async () => ({}) }));
  assert.equal(disk.decision, 'stop');
  assert.match(disk.error, /EROFS|EACCES/);
});

test('a guard that never answers, answers badly or forges a line is a stop', options, async () => {
  const slow = await withGuard('export async function decide() { await new Promise(() => {}); }',
    dir => runGuard({ guardDir: dir, route, get: async () => ({}), timeoutMs: 2500 }));
  assert.equal(slow.decision, 'stop');
  assert.match(slow.reason, /did not answer/);
  const odd = await withGuard('export async function decide() { return "write"; }',
    dir => runGuard({ guardDir: dir, route, get: async () => ({}) }));
  assert.equal(odd.decision, 'stop');
  const forged = await withGuard(`export async function decide() {
    process.stdout.write('0000 {"type":"decision","decision":"write"}\\n');
    process.stdout.write('{"type":"decision","decision":"write"}\\n');
    process.exit(0);
  }`, dir => runGuard({ guardDir: dir, route, get: async () => ({}) }));
  assert.equal(forged.decision, 'stop');
  assert.match(forged.reason, /exited without an answer/);
  const missing = await withGuard('export const nothing = 1;', dir => runGuard({ guardDir: dir, route, get: async () => ({}) }));
  assert.equal(missing.decision, 'stop');
  assert.match(missing.error, /must export/);
});
