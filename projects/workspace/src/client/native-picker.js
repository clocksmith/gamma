import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { lstat, readFile } from 'node:fs/promises';
import { isAbsolute } from 'node:path';

const unavailable = Object.freeze({ status: 'selection-unavailable' });
const hex = /^[a-f0-9]{64}$/;
const MAX_BINARY = 16 * 1024 * 1024;
const MAX_EVIDENCE = 1024 * 1024;

// Operator pins the locally built, owner-controlled app binary. Only its
// private child stdout crosses the bridge. No file paths, browser auth, or
// app-global IPC capabilities are passed to the child.
export function createNativePicker({ executable, sha256, timeoutMs = 90_000 }) {
  if (typeof executable !== 'string' || !isAbsolute(executable) || !hex.test(sha256 ?? '') ||
      !Number.isSafeInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 120_000) {
    throw new TypeError('Native picker requires an absolute executable, SHA-256 pin, and bounded timeout');
  }
  let busy = false;
  return async function pick({ signal } = {}) {
    if (busy || signal?.aborted) return unavailable;
    busy = true;
    try {
      const info = await lstat(executable);
      if (!info.isFile() || info.uid !== process.getuid() || (info.mode & 0o022) || info.size > MAX_BINARY ||
          createHash('sha256').update(await readFile(executable)).digest('hex') !== sha256 || signal?.aborted) {
        return unavailable;
      }
      return await new Promise(resolve => {
        const child = spawn(executable, [], { stdio: ['ignore', 'pipe', 'ignore'], env: {} });
        let length = 0, stopped = false;
        const chunks = [];
        const stop = () => { stopped = true; child.kill('SIGKILL'); };
        const timer = setTimeout(stop, timeoutMs);
        signal?.addEventListener('abort', stop, { once: true });
        if (signal?.aborted) stop();
        child.stdout.on('data', chunk => {
          length += chunk.length;
          if (length > 256) stop();
          else chunks.push(chunk);
        });
        child.once('error', () => { stopped = true; });
        child.once('close', code => {
          clearTimeout(timer);
          signal?.removeEventListener('abort', stop);
          if (stopped || code !== 0) return resolve(unavailable);
          try {
            const value = JSON.parse(Buffer.concat(chunks).toString('utf8'));
            if (Object.keys(value).sort().join(',') !== 'byteLength,sha256,status' ||
                value.status !== 'observed' || !Number.isSafeInteger(value.byteLength) ||
                value.byteLength < 0 || value.byteLength > MAX_EVIDENCE ||
                typeof value.sha256 !== 'string' || !hex.test(value.sha256)) return resolve(unavailable);
            resolve(value);
          } catch { resolve(unavailable); }
        });
      });
    } catch { return unavailable; }
    finally { busy = false; }
  };
}
