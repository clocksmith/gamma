import assert from 'node:assert/strict';
import { fork } from 'node:child_process';
import { once } from 'node:events';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { descendants, inspectBrowserProcesses, waitForProfileRelease } from '../../qualification/identity.js';

const root = mkdtempSync(join(tmpdir(), 'fawn-process-inspection-'));
const host = fork(fileURLToPath(new URL('../support/process-inspection-host.js', import.meta.url)), [root],
  { stdio: ['ignore', 'ignore', 'inherit', 'ipc'] });
const exited = once(host, 'exit');
try {
  const [ready] = await once(host, 'message');
  assert.equal(ready.ready, true);
  assert.ok(descendants(host.pid).includes(ready.pid));
  const profile = join(root, 'owned-profile');
  mkdirSync(profile);
  writeFileSync(join(profile, 'DevToolsActivePort'), '12345\n/devtools/browser/test\n');
  const listening = inspectBrowserProcesses(host.pid, root);
  assert.equal(listening.processCount, 1);
  assert.equal(listening.executables.length, 1);
  assert.match(listening.executables[0].sha256, /^[a-f0-9]{64}$/);
  assert.equal(listening.processes[0].pid, ready.pid);
  assert.equal(listening.processes[0].parentPid, host.pid);
  assert.ok(listening.processes[0].commandLine.includes('--listener'));
  assert.ok(listening.processes[0].commandLine.includes(root));
  assert.equal(listening.listeningTcpSockets, 1, 'a real child-owned listener must be detected');
  assert.equal(listening.devToolsActivePortFiles, 1, 'a real nested port file must be detected');
  const closed = once(host, 'message');
  host.send('close-listener');
  assert.equal((await closed)[0].listenerClosed, true);
  rmSync(profile, { recursive: true });
  const closedInspection = inspectBrowserProcesses(host.pid, root);
  assert.equal(closedInspection.listeningTcpSockets, 0);
  assert.equal(closedInspection.devToolsActivePortFiles, 0);
} finally {
  host.send('stop');
  assert.equal((await exited)[0], 0);
  await waitForProfileRelease(root);
}
console.log('ok: observed descendant images, real listener rejection and profile release');
