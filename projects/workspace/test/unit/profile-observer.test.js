import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, realpathSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const profile = realpathSync.native(mkdtempSync(join(tmpdir(), 'fawn-profile-observer-')));
try {
  const script = `
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {once} from 'node:events';
import {processesUsing} from ${JSON.stringify(new URL('../../qualification/process-inspection.js', import.meta.url).href)};
import {waitForProfileRelease} from ${JSON.stringify(new URL('../../qualification/identity.js', import.meta.url).href)};
const profile=${JSON.stringify(profile)};
assert.ok(!processesUsing(profile).includes(process.pid), 'the node -e observer must not claim its own string literal');
const child=fork('-e',['process.on("message",()=>process.disconnect());process.send("ready");',profile],{stdio:['ignore','ignore','inherit','ipc']});
const exited=once(child,'exit');
try {
  await once(child,'message');
  assert.ok(processesUsing(profile).includes(child.pid),'a real child naming the same profile must remain visible');
} finally {child.send('stop');assert.equal((await exited)[0],0);}
await waitForProfileRelease(profile);
console.log('observed child released; verifier and ancestors excluded');
`;
  const control = spawnSync(process.execPath, ['--input-type=module', '-e', script], { encoding: 'utf8', timeout: 15000 });
  assert.equal(control.status, 0, control.stdout + control.stderr);
  assert.match(control.stdout, /observed child released/);
  console.log('ok: inline profile observer does not match itself, real owned children still block release');
} finally { rmSync(profile, { recursive: true }); }
