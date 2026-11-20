// Fawn workspace — durable journal
//
// Append-only, hash-chained JSONL. Each record is fsynced before the caller acts on it, so a
// record without its terminator was never acted on and is the only damage repaired on open.

import { createHash } from 'node:crypto';
import {
  closeSync,
  existsSync,
  fsyncSync,
  mkdirSync,
  openSync,
  readFileSync,
  rmSync,
  truncateSync,
  writeFileSync,
  writeSync,
} from 'node:fs';
import { join } from 'node:path';
import { REJECTION_CODES, workspaceError } from './errors.js';

const GENESIS_HASH = '0'.repeat(64);
const RECORD_TERMINATOR = '\n';
const FIRST_SEQUENCE = 1;
const PROCESS_PROBE_SIGNAL = 0;

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  if (value && typeof value === 'object') {
    const keys = Object.keys(value).filter((key) => value[key] !== undefined).sort();
    return `{${keys.map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function sha256Hex(text) {
  return createHash('sha256').update(text).digest('hex');
}

function recordHash(prevHash, entry) {
  return sha256Hex(`${prevHash}${canonicalJson(entry)}`);
}

function isProcessAlive(pid) {
  try {
    process.kill(pid, PROCESS_PROBE_SIGNAL);
    return true;
  } catch (error) {
    return error.code === 'EPERM';
  }
}

function acquireLock(lockPath) {
  if (existsSync(lockPath)) {
    let holder = null;
    try {
      holder = JSON.parse(readFileSync(lockPath, 'utf8'));
    } catch {
      throw workspaceError(REJECTION_CODES.JOURNAL_LOCKED, 'unreadable journal lock', { lockPath });
    }
    if (!Number.isInteger(holder?.pid) || isProcessAlive(holder.pid)) {
      throw workspaceError(REJECTION_CODES.JOURNAL_LOCKED, 'journal held by a live process', {
        lockPath,
        holder,
      });
    }
    rmSync(lockPath);
    writeFileSync(lockPath, JSON.stringify({ pid: process.pid }), { flag: 'wx' });
    return { recoveredFromPid: holder.pid };
  }
  writeFileSync(lockPath, JSON.stringify({ pid: process.pid }), { flag: 'wx' });
  return null;
}

function corrupt(filePath, lineNumber, reason) {
  return workspaceError(REJECTION_CODES.JOURNAL_CORRUPT, `${filePath}:${lineNumber}: ${reason}`, {
    filePath,
    lineNumber,
    reason,
  });
}

function verifyRecords(filePath, lines) {
  const records = [];
  let prevHash = GENESIS_HASH;
  lines.forEach((line, index) => {
    const lineNumber = index + 1;
    let record;
    try {
      record = JSON.parse(line);
    } catch {
      throw corrupt(filePath, lineNumber, 'terminated record is not JSON');
    }
    const { seq, type, at, body, prevHash: storedPrev, hash } = record;
    if (seq !== FIRST_SEQUENCE + index) throw corrupt(filePath, lineNumber, `sequence ${seq}`);
    if (storedPrev !== prevHash) throw corrupt(filePath, lineNumber, 'chain break');
    if (recordHash(prevHash, { seq, type, at, body }) !== hash) {
      throw corrupt(filePath, lineNumber, 'hash mismatch');
    }
    prevHash = hash;
    records.push(record);
  });
  return { records, lastHash: prevHash };
}

/**
 * Verify journal text without opening it for writing: every terminated record must chain.
 */
function parseJournalText(filePath, text) {
  const terminatedEnd = text.lastIndexOf(RECORD_TERMINATOR) + 1;
  const tornTail = text.slice(terminatedEnd);
  const lines = terminatedEnd === 0 ? [] : text.slice(0, terminatedEnd - 1).split(RECORD_TERMINATOR);
  const { records, lastHash } = verifyRecords(filePath, lines);
  return { records, lastHash, tornTail, terminatedBytes: Buffer.byteLength(text.slice(0, terminatedEnd)) };
}

/** Read and verify a journal file read-only, as an evidence validator does. */
function readVerifiedJournal(filePath) {
  const { records, tornTail } = parseJournalText(filePath, readFileSync(filePath, 'utf8'));
  return { records, tornTailBytes: Buffer.byteLength(tornTail) };
}

class Journal {
  constructor({ filePath, lockPath, fd, records, lastHash, recovery }) {
    this._filePath = filePath;
    this._lockPath = lockPath;
    this._fd = fd;
    this._records = records;
    this._lastHash = lastHash;
    this.recovery = recovery;
  }

  /**
   * Open or create a journal, verifying every terminated record before returning.
   * @param {{directory: string, fileName: string, lockFileName: string}} options
   */
  static open({ directory, fileName, lockFileName }) {
    mkdirSync(directory, { recursive: true });
    const filePath = join(directory, fileName);
    const lockPath = join(directory, lockFileName);
    const lockRecovery = acquireLock(lockPath);
    try {
      const text = existsSync(filePath) ? readFileSync(filePath, 'utf8') : '';
      const { records, lastHash, tornTail, terminatedBytes } = parseJournalText(filePath, text);
      if (tornTail.length > 0) truncateSync(filePath, terminatedBytes);
      const fd = openSync(filePath, 'a');
      const recovery = {
        lockRecoveredFromPid: lockRecovery?.recoveredFromPid ?? null,
        tornTail: tornTail.length > 0
          ? { discardedBytes: Buffer.byteLength(tornTail), discardedHash: sha256Hex(tornTail) }
          : null,
      };
      return new Journal({ filePath, lockPath, fd, records, lastHash, recovery });
    } catch (error) {
      rmSync(lockPath, { force: true });
      throw error;
    }
  }

  get records() {
    return this._records;
  }

  /**
   * Durably append one record; returns only after fsync.
   * @param {string} type
   * @param {object} body
   */
  append(type, body) {
    if (this._fd === null) throw new Error('journal is closed');
    // Hash the JSON representation that is actually persisted, including null array holes.
    // Optional undefined object fields disappear in JSON; hashing them before encoding corrupts replay.
    const persistedBody = JSON.parse(JSON.stringify(body, (_key, value) => {
      if (['function', 'symbol', 'bigint'].includes(typeof value) || (typeof value === 'number' && !Number.isFinite(value))) {
        throw new TypeError('Journal records require finite JSON values');
      }
      return value;
    }));
    const entry = { seq: this._records.length + FIRST_SEQUENCE, type, at: new Date().toISOString(), body: persistedBody };
    const hash = recordHash(this._lastHash, entry);
    const record = { ...entry, prevHash: this._lastHash, hash };
    writeSync(this._fd, `${JSON.stringify(record)}${RECORD_TERMINATOR}`);
    fsyncSync(this._fd);
    this._lastHash = hash;
    this._records.push(record);
    return record;
  }

  close() {
    if (this._fd === null) return;
    closeSync(this._fd);
    this._fd = null;
    rmSync(this._lockPath, { force: true });
  }
}

export { Journal, canonicalJson, readVerifiedJournal, sha256Hex };
