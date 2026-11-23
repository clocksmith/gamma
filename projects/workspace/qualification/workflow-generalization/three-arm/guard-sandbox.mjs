// Runs a model-written guard on one route (clocksmith/deco#88, same-model
// three-arm test). The guard is code we did not write, so it runs in a
// container with no network, a read-only file system, no capabilities and a
// time limit. Its only way to the application is `get`, which the runner
// performs through the decision surface: read-only, as the approver, a few
// reads. Anything other than a clean "write" is a stop.
import { spawn } from 'node:child_process';
import { randomBytes } from 'node:crypto';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HOST_SCRIPT = join(dirname(fileURLToPath(import.meta.url)), 'guard-host.mjs');
export const GUARD_IMAGE = 'node:22-alpine';

/**
 * `guardDir` holds guard.mjs, which exports `async decide({ familyId, project,
 * workPackageId, workHours, workDuration, get })` and resolves to { decision: 'write' | 'stop', reason }.
 * `get(path)` resolves to what the decision surface returned.
 */
export function runGuard({ guardDir, route, get, timeoutMs = 20000, image = GUARD_IMAGE, spawnProcess = spawn }) {
  const nonce = randomBytes(16).toString('hex');
  const name = `gammatron-guard-${nonce.slice(0, 12)}`;
  const started = Date.now();
  const args = ['run', '--rm', '-i', '--name', name, '--network', 'none', '--read-only', '--cap-drop', 'ALL',
    '--security-opt', 'no-new-privileges', '--pids-limit', '64', '--memory', '256m', '--cpus', '1', '--user', '65534:65534',
    '-v', `${resolve(guardDir)}:/guard:ro`, '-v', `${HOST_SCRIPT}:/host/guard-host.mjs:ro`,
    image, 'node', '/host/guard-host.mjs'];
  return new Promise(done => {
    const child = spawnProcess('docker', args, { stdio: ['pipe', 'pipe', 'pipe'] });
    let reads = 0;
    let settled = false;
    let buffer = '';
    let stderr = '';
    const finish = result => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      child.stdin.destroy();
      spawnProcess('docker', ['rm', '-f', name], { stdio: 'ignore' }).on('error', () => {});
      done(Object.freeze({ reads, wallMs: Date.now() - started, ...result }));
    };
    const stop = reason => finish({ decision: 'stop', reason, error: reason });
    const timer = setTimeout(() => stop(`guard did not answer within ${timeoutMs} ms`), timeoutMs);
    child.on('error', error => stop(`guard sandbox could not start: ${error.code ?? error.message}`));
    child.stdin.on('error', () => {});
    child.stderr.on('data', chunk => { if (stderr.length < 4000) stderr += chunk; });
    child.stdout.on('data', chunk => {
      buffer += chunk;
      if (buffer.length > 1_000_000) return stop('guard wrote too much output');
      for (let cut; (cut = buffer.indexOf('\n')) !== -1; buffer = buffer.slice(cut + 1)) {
        const line = buffer.slice(0, cut);
        if (!line.startsWith(`${nonce} `)) continue;
        let message;
        try { message = JSON.parse(line.slice(nonce.length + 1)); } catch { continue; }
        if (message.type === 'get') {
          reads += 1;
          Promise.resolve(get(String(message.path))).catch(error => ({ ok: false, refused: String(error?.message ?? error) }))
            .then(result => { if (!settled) child.stdin.write(`${nonce} ${JSON.stringify({ type: 'got', id: message.id, result })}\n`); });
        } else if (message.type === 'decision') {
          finish({ decision: message.decision === 'write' ? 'write' : 'stop', reason: message.reason ?? null, error: null });
        } else if (message.type === 'error') {
          finish({ decision: 'stop', reason: 'guard raised an error', error: String(message.message).slice(0, 1200) });
        }
      }
    });
    child.on('close', code => stop(`guard exited without an answer (status ${code})${stderr ? `: ${stderr.trim().split('\n').pop().slice(0, 300)}` : ''}`));
    child.stdin.write(JSON.stringify({ nonce, route }) + '\n');
  });
}
