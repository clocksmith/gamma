// Bounded release of one persistent-profile browser.
//
// Closing a Playwright persistent context on stock Chrome can take many seconds, sometimes minutes,
// once the browser has been running for about half a minute. Playwright does force-kill the browser
// 30 s after the close request, but then waits for the child's standard streams to close, and
// Chrome's updater and crash handler, which outlive the kill, hold them open (traced 2026-11-17; see
// docs/status/fawn-workspace.md). Releasing a workspace must not depend on that: ask for a graceful
// close, wait a fixed time, then end the browser that owns this profile and stop waiting. Workspace state lives in the journal,
// which is already safe against process death; a forced exit can lose the profile's last
// unflushed site data (for example a cookie set moments before closing).
import { execFileSync } from 'node:child_process';

/** Main browser processes (not renderers or helpers) launched with exactly this profile directory. */
export function profileBrowserPids(profileDir, { list = () => execFileSync('ps', ['-axo', 'pid=,command='], { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 }) } = {}) {
  if (process.platform === 'win32') return [];
  const flag = `--user-data-dir=${profileDir}`;
  return list().split('\n').flatMap((line) => {
    const match = /^\s*(\d+)\s+(.*)$/.exec(line);
    if (!match || match[2].includes(' --type=')) return [];
    const at = match[2].indexOf(flag), next = match[2][at + flag.length];
    return at >= 0 && (next === undefined || next === ' ') ? [Number(match[1])] : [];
  });
}

const pause = (ms) => new Promise((resolve) => { setTimeout(resolve, ms); });

/**
 * Release one persistent-profile browser and say what was established about its exit.
 *
 *   graceful        the close completed and no browser remains on the profile
 *   already-exited  the close failed or ran out of time, yet no browser was found on the profile
 *   forced          a browser on the profile was signalled and is verified gone
 *   unresolved      a browser on the profile could not be shown to have exited
 *
 * `survivors` lists process ids still present; `errors` lists what could not be done. Only a process
 * that no longer exists (ESRCH) is an acceptable signalling failure. The caller keeps owning an
 * unresolved browser.
 */
export async function closeWithin(context, { profileDir, timeoutMs, settleMs = 1000, exitWaitMs = 2000, pollMs = 50,
  findPids = profileBrowserPids, kill = process.kill.bind(process), canVerify = process.platform !== 'win32' }) {
  const errors = [];
  let timer;
  const closing = context.close().then(() => ({ state: 'closed' }), (error) => ({ state: 'rejected', error }));
  const first = await Promise.race([closing, new Promise((resolve) => { timer = setTimeout(() => resolve({ state: 'deadline' }), timeoutMs); })]);
  clearTimeout(timer);
  if (first.state === 'rejected') errors.push({ step: 'close', message: String(first.error?.message ?? first.error) });
  if (!canVerify) {
    // Without a process listing nothing beyond a completed close can be established.
    if (first.state === 'closed') return { release: 'graceful', survivors: [], errors };
    errors.push({ step: 'verify', message: 'browser exit cannot be verified on this platform' });
    return { release: 'unresolved', survivors: [], errors };
  }
  const present = () => {
    try { return findPids(profileDir); }
    catch (error) { errors.push({ step: 'list', message: String(error?.message ?? error) }); return null; }
  };
  let pids = present();
  if (pids === null) return { release: 'unresolved', survivors: [], errors };
  if (!pids.length) return { release: first.state === 'closed' ? 'graceful' : 'already-exited', survivors: [], errors };
  let signalled = 0;
  for (const pid of pids) {
    try { kill(pid, 'SIGKILL'); signalled += 1; }
    catch (error) {
      // It exited between the listing and the signal. Anything else is a failure to end it.
      if (error?.code !== 'ESRCH') errors.push({ step: 'signal', pid, code: error?.code ?? null, message: String(error?.message ?? error) });
    }
  }
  for (const deadline = Date.now() + exitWaitMs; ;) {
    pids = present();
    if (pids === null) return { release: 'unresolved', survivors: [], errors };
    if (!pids.length || Date.now() >= deadline) break;
    await pause(pollMs);
  }
  // Playwright's close does not always settle after its browser is ended, so it is given a short
  // grace period and then abandoned; the process it was waiting for is accounted for above.
  await Promise.race([closing, new Promise((resolve) => { timer = setTimeout(resolve, settleMs); })]);
  clearTimeout(timer);
  if (pids.length) return { release: 'unresolved', survivors: pids, errors };
  return { release: signalled ? 'forced' : 'already-exited', survivors: [], errors };
}
