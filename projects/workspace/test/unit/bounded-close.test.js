// Releasing a workspace is bounded, and what it reports is what was established: a browser is
// "graceful", "forced" or "already-exited" only when no process remains on the profile, and
// anything that could not be shown to have exited is "unresolved".
import assert from 'node:assert/strict';
import { closeWithin, profileBrowserPids } from '../../src/adapters/bounded-close.js';

const listing = [
  '  101 /Applications/Google Chrome.app/Contents/MacOS/Google Chrome --headless --user-data-dir=/state/profiles/a --remote-debugging-pipe',
  '  102 /Applications/Google Chrome.app/Contents/Frameworks/Helper (Renderer) --type=renderer --user-data-dir=/state/profiles/a',
  '  103 /Applications/Google Chrome.app/Contents/MacOS/Google Chrome --user-data-dir=/state/profiles/a-other',
  '  104 /Applications/Google Chrome.app/Contents/MacOS/Google Chrome --user-data-dir=/state/profiles/b',
  '  105 /usr/bin/chrome --user-data-dir=/state/profiles/a',
].join('\n');
if (process.platform !== 'win32') {
  assert.deepEqual(profileBrowserPids('/state/profiles/a', { list: () => listing }), [101, 105]);
  assert.deepEqual(profileBrowserPids('/state/profiles/none', { list: () => listing }), []);
}

// A small process table: `alive` is what a listing shows; `kill` removes or refuses.
function table(pids, { refuse = {}, immortal = [] } = {}) {
  const alive = new Set(pids), signals = [];
  return { signals, alive,
    findPids: () => [...alive],
    kill: (pid, signal) => {
      signals.push([pid, signal]);
      if (refuse[pid]) throw Object.assign(Error(refuse[pid]), { code: refuse[pid] });
      if (!immortal.includes(pid)) alive.delete(pid);
    } };
}
const fast = { profileDir: '/state/profiles/a', timeoutMs: 30, settleMs: 20, exitWaitMs: 60, pollMs: 5, canVerify: true };
const never = { close: () => new Promise(() => {}) };

// The close completes and the process is gone: graceful, nothing signalled.
let t = table([101]);
assert.deepEqual(await closeWithin({ close: async () => { t.alive.clear(); } }, { ...fast, ...t }), { release: 'graceful', survivors: [], errors: [] });
assert.deepEqual(t.signals, []);

// A close that rejects is not a graceful close. With the browser still there it is ended and verified.
t = table([101]);
let result = await closeWithin({ close: async () => { throw Error('Target closed unexpectedly'); } }, { ...fast, ...t });
assert.equal(result.release, 'forced');
assert.deepEqual(t.signals, [[101, 'SIGKILL']]);
assert.deepEqual(result.errors, [{ step: 'close', message: 'Target closed unexpectedly' }], 'the failed close stays on the record');

// A close that rejects because the browser already died: nothing to signal, and it says so.
t = table([]);
result = await closeWithin({ close: async () => { throw Error('Browser has been closed'); } }, { ...fast, ...t });
assert.equal(result.release, 'already-exited');
assert.deepEqual(t.signals, []);

// The deadline passes: every main browser on the profile is ended, exit is verified, the wait is bounded.
t = table([101, 105]);
const started = performance.now();
result = await closeWithin(never, { ...fast, ...t });
assert.deepEqual(result, { release: 'forced', survivors: [], errors: [] });
assert.deepEqual(t.signals, [[101, 'SIGKILL'], [105, 'SIGKILL']]);
assert.ok(performance.now() - started < 2000);

// It exited between the listing and the signal (ESRCH): acceptable, and not reported as forced.
t = table([101], { refuse: { 101: 'ESRCH' } });
t.kill = (pid, signal) => { t.signals.push([pid, signal]); t.alive.delete(pid); throw Object.assign(Error('no such process'), { code: 'ESRCH' }); };
result = await closeWithin(never, { ...fast, ...t });
assert.deepEqual(result, { release: 'already-exited', survivors: [], errors: [] });

// The signal is not permitted: the browser is still there, so the release is unresolved, never forced.
t = table([101], { refuse: { 101: 'EPERM' } });
result = await closeWithin(never, { ...fast, ...t });
assert.equal(result.release, 'unresolved');
assert.deepEqual(result.survivors, [101]);
assert.deepEqual(result.errors.map(({ step, pid, code }) => ({ step, pid, code })), [{ step: 'signal', pid: 101, code: 'EPERM' }]);

// The signal is delivered but the process does not go away within the wait: unresolved.
t = table([101, 105], { immortal: [105] });
result = await closeWithin(never, { ...fast, ...t });
assert.equal(result.release, 'unresolved');
assert.deepEqual(result.survivors, [105]);

// The process listing fails: nothing can be established.
result = await closeWithin(never, { ...fast, findPids: () => { throw Error('ps unavailable'); }, kill: () => { throw Error('must not signal blind'); } });
assert.equal(result.release, 'unresolved');
assert.deepEqual(result.errors, [{ step: 'list', message: 'ps unavailable' }]);

// Where exit cannot be verified at all, only a completed close counts.
assert.equal((await closeWithin({ close: async () => {} }, { ...fast, canVerify: false, findPids: () => { throw Error('unused'); } })).release, 'graceful');
result = await closeWithin(never, { ...fast, canVerify: false });
assert.equal(result.release, 'unresolved');
assert.match(result.errors[0].message, /cannot be verified/);

// The adapter gives up a workspace only once its browser is accounted for.
{
  const { createPlaywrightAdapter } = await import('../../src/adapters/playwright-adapter.js');
  const { loadServiceConfig } = await import('../../src/config.js');
  const adapter = createPlaywrightAdapter({ config: loadServiceConfig(), profileRoot: '/state/profiles', artifactRoot: '/state/artifacts' });
  const entry = name => ({ context: { name }, profileDir: `/state/profiles/${name}`, page: null, pages: new Map() });
  adapter._workspaces.set('settled', entry('settled')); adapter._workspaces.set('stuck', entry('stuck'));
  const asked = [];
  const releaseBrowser = async (context, options) => { asked.push([context.name, options.profileDir, options.timeoutMs]);
    return context.name === 'stuck' ? { release: 'unresolved', survivors: [4242], errors: [{ step: 'signal', pid: 4242, code: 'EPERM', message: 'not permitted' }] }
      : { release: 'forced', survivors: [], errors: [] }; };
  const released = await adapter.close({ timeoutMs: 7, releaseBrowser });
  assert.deepEqual(asked, [['settled', '/state/profiles/settled', 7], ['stuck', '/state/profiles/stuck', 7]]);
  assert.deepEqual(released, [{ workspaceId: 'settled', release: 'forced' },
    { workspaceId: 'stuck', release: 'unresolved', survivors: [4242], errors: [{ step: 'signal', pid: 4242, code: 'EPERM', message: 'not permitted' }] }]);
  assert.deepEqual([...adapter._workspaces.keys()], ['stuck'], 'an unresolved browser stays owned and can be released again');
  assert.deepEqual(await adapter.close({ timeoutMs: 7, releaseBrowser: async () => ({ release: 'already-exited', survivors: [], errors: [] }) }),
    [{ workspaceId: 'stuck', release: 'already-exited' }]);
  assert.equal(adapter._workspaces.size, 0);
}
console.log('ok: release outcomes are verified against the process table; rejected closes, refused signals and survivors are never reported as clean');
