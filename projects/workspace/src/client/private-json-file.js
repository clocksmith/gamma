// POSIX private JSON transactions shared by the local cache and sealed registry.
import { randomUUID } from 'node:crypto';
import { closeSync, constants, fsyncSync, fstatSync, lstatSync, mkdirSync, openSync,
  readFileSync, renameSync, unlinkSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';

export function privateStat(stat, directory = false) {
  if (typeof process.getuid !== 'function' || !(directory ? stat.isDirectory() : stat.isFile())
    || stat.uid !== process.getuid() || (stat.mode & 0o077)) {
    throw Object.assign(Error('Storage must be owner-only and owned by this process user'), { code: 'workflow-store-private' });
  }
}
export class PrivateJsonFile {
  constructor(path, { maxBytes, lockWaitMs, lockRetryMs }) {
    if ([maxBytes, lockWaitMs, lockRetryMs].some(n => !Number.isSafeInteger(n) || n < 1)) throw Error('Invalid private file limits');
    this.path = resolve(path); this.directory = dirname(this.path);
    this.maxBytes = maxBytes; this.lockWaitMs = lockWaitMs; this.lockRetryMs = lockRetryMs;
    this.lockPath = this.path + '.lock';
    mkdirSync(this.directory, { recursive: true, mode: 0o700 });
    privateStat(lstatSync(this.directory), true);
  }
  read(empty) {
    let fd;
    try { fd = openSync(this.path, constants.O_RDONLY | constants.O_NOFOLLOW); }
    catch (e) { if (e.code === 'ENOENT') return structuredClone(empty); throw e; }
    try {
      const stat = fstatSync(fd); privateStat(stat);
      if (stat.size > this.maxBytes) throw Object.assign(Error('Storage byte limit'), { code: 'workflow-store-limit' });
      return JSON.parse(readFileSync(fd, 'utf8'));
    } finally { closeSync(fd); }
  }
  write(state) {
    const bytes = JSON.stringify(state) + '\n';
    if (Buffer.byteLength(bytes) > this.maxBytes) throw Object.assign(Error('Storage byte limit'), { code: 'workflow-store-limit' });
    const temporary = `${this.path}.${randomUUID()}.tmp`;
    const fd = openSync(temporary, 'wx', 0o600);
    try { writeFileSync(fd, bytes); fsyncSync(fd); }
    catch (error) { unlinkSync(temporary); throw error; }
    finally { closeSync(fd); }
    try {
      renameSync(temporary, this.path);
      const dir = openSync(this.directory, 'r');
      try { fsyncSync(dir); } finally { closeSync(dir); }
    } finally { try { unlinkSync(temporary); } catch (e) { if (e.code !== 'ENOENT') throw e; } }
  }
  async transaction(update) {
    const deadline = performance.now() + this.lockWaitMs;
    let fd;
    for (;;) {
      try { fd = openSync(this.lockPath, 'wx', 0o600); break; }
      catch (error) {
        if (error.code !== 'EEXIST') throw error;
        if (performance.now() >= deadline) throw Object.assign(Error('Publisher locked; no browser action retried'), { code: 'workflow-store-busy' });
        await delay(Math.min(this.lockRetryMs, Math.max(1, deadline - performance.now())));
      }
    }
    try { writeFileSync(fd, JSON.stringify({ pid: process.pid })); fsyncSync(fd); return await update(); }
    finally { closeSync(fd); unlinkSync(this.lockPath); }
  }
}
