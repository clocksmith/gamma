import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { fork, spawnSync } from 'node:child_process';
import { once } from 'node:events';
import { copyFileSync, mkdtempSync, readFileSync, realpathSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { inspectBrowserProcesses, waitForProfileRelease } from '../../qualification/identity.js';
import { parseLinuxExecutableMappings, parseMacTextImages, parseWindowsModuleImages } from '../../qualification/process-inspection.js';

const sha256 = path => createHash('sha256').update(readFileSync(path)).digest('hex');
const root = realpathSync.native(mkdtempSync(join(tmpdir(), 'fawn mapped child-Ω-')));
const library = join(root, 'child module-λ.node');
const source = fileURLToPath(new URL('../support/process-inspection-module.c', import.meta.url));
if (process.env.FAWN_PROCESS_INSPECTION_MODULE) {
  // A platform owner may build the exact fixture with its configured native
  // toolchain; the observed module SHA and source SHA are emitted below.
  copyFileSync(process.env.FAWN_PROCESS_INSPECTION_MODULE, library);
} else {
  assert.notEqual(process.platform, 'win32', 'Windows owner must provide the exact compiled fixture via FAWN_PROCESS_INSPECTION_MODULE');
  const compiled = spawnSync(process.env.CC ?? 'cc',
    [process.platform === 'darwin' ? '-dynamiclib' : '-shared', '-fPIC', source, '-o', library],
    { encoding: 'utf8', timeout: 30000 });
  assert.equal(compiled.status, 0, `${compiled.stdout}\n${compiled.stderr}`);
}

// Parser controls exercise OS formats independently from the live control.
assert.deepEqual(parseLinuxExecutableMappings(
  '1000-2000 r-xp 000000 00:01 2 /tmp/a\\040b.so\n2000-3000 rw-p 000000 00:01 2 /tmp/not-code\n'
  + '3000-4000 r-xp 000000 00:01 3 /tmp/retired.so (deleted)\n'),
{ paths: ['/tmp/a b.so'], unavailable: [{ path: '/tmp/retired.so (deleted)', reason: 'deleted executable mapping' }] });
assert.throws(() => parseLinuxExecutableMappings('malformed mapping'), /unrecognized/);
assert.deepEqual([...parseMacTextImages('p12\nn/tmp/child.node\n', [12])], [[12, ['/tmp/child.node']]]);
assert.throws(() => parseMacTextImages('p13\nn/tmp/foreign.node\n', [12]), /unrequested/);
assert.throws(() => parseMacTextImages('n/tmp/no-process.node\n', [12]), /without/);
assert.deepEqual([...parseWindowsModuleImages('[{"pid":12,"paths":["C:\\\\probe.dll"]}]', [12])],
  [[12, ['C:\\probe.dll']]]);
assert.throws(() => parseWindowsModuleImages('[{"pid":13,"paths":["C:\\\\foreign.dll"]}]', [12]), /unrequested/);
assert.throws(() => parseWindowsModuleImages('[{"pid":12,"paths":[null]}]', [12]), /invalid/);

const fixture = fileURLToPath(new URL('../support/process-inspection-module-host.js', import.meta.url));
const owned = fork(fixture, ['--host', library], { stdio: ['ignore', 'ignore', 'inherit', 'ipc'] });
const unrelated = fork(fixture, ['--loaded-child', library], { stdio: ['ignore', 'ignore', 'inherit', 'ipc'] });
const ownedExit = once(owned, 'exit');
const unrelatedExit = once(unrelated, 'exit');
const unrelatedReady = once(unrelated, 'message');
let receipt;
try {
  const [ready] = await once(owned, 'message');
  const [outside] = await unrelatedReady;
  assert.equal(ready.ready, true);
  assert.equal(outside.ready, true);
  const observed = inspectBrowserProcesses(owned.pid, root);
  assert.equal(observed.processCount, 2, 'only the owned root and grandchild belong to this tree');
  assert.equal(observed.executables.length, 1, 'root image semantics remain unchanged');
  assert.equal(observed.listeningTcpSockets, 0);
  assert.equal(observed.devToolsActivePortFiles, 0);
  const module = observed.mappedCodeModules.find(entry => entry.path === realpathSync.native(library));
  assert.ok(module, 'a library loaded only in the owned grandchild must be observed');
  assert.equal(module.sha256, sha256(library));
  assert.equal(module.processes.length, 1);
  assert.equal(module.processes[0].pid, ready.modulePid);
  assert.equal(module.processes[0].parentPid, ready.browserPid);
  assert.ok(module.processes[0].startedAt);
  assert.equal(module.processes[0].executable, realpathSync.native(process.execPath));
  assert.ok(!module.processes.some(entry => [ready.browserPid, outside.modulePid].includes(entry.pid)),
    'root argv and an unrelated process loading the same file are not module proof');
  receipt = { platform: process.platform, sourceSha256: sha256(source), fixtureSha256: sha256(fixture),
    librarySha256: sha256(library), ownedRootPid: ready.browserPid, ownedModulePid: ready.modulePid,
    excludedUnrelatedPid: outside.modulePid, module, passed: true };
  if (process.platform !== 'win32') {
    rmSync(library);
    const deleted = inspectBrowserProcesses(owned.pid, root);
    assert.ok(!deleted.mappedCodeModules.some(entry => entry.path === library),
      'an unlinked loaded image must not receive a current-file identity or cached SHA');
    receipt.unlinkedImage = { verifiedCurrentFile: false, omissions: deleted.unavailableModuleMappings };
  } else {
    receipt.unlinkedImage = { status: 'not-run', reason: 'Windows loader locks the mapped fixture file' };
  }
} finally {
  owned.send('stop');
  unrelated.send('stop');
  assert.equal((await ownedExit)[0], 0);
  assert.equal((await unrelatedExit)[0], 0);
  await waitForProfileRelease(root);
  rmSync(root, { recursive: true });
}
console.log(JSON.stringify(receipt));
