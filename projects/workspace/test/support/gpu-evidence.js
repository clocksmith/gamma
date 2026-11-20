import { createHash } from 'node:crypto';
import { closeSync, fsyncSync, mkdirSync, openSync, renameSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';

function atomicWrite(path, bytes) {
  const temporary = path + '.tmp';
  const descriptor = openSync(temporary, 'wx', 0o600);
  try { writeFileSync(descriptor, bytes); fsyncSync(descriptor); } finally { closeSync(descriptor); }
  renameSync(temporary, path);
  if (process.platform !== 'win32') {
    const directory = openSync(dirname(path), 'r');
    try { fsyncSync(directory); } finally { closeSync(directory); }
  }
}

/** Retain exact page bytes and complete per-stage snapshots before acknowledging them. */
function createGpuEvidence(output, result) {
  mkdirSync(join(output, 'checkpoints'));
  mkdirSync(join(output, 'raw-page-reports'));
  result.checkpoints = [];
  result.rawPageReports = [];
  const checkpoint = (phase, adapter = null) => {
    const stage = { sequence: result.checkpoints.length + 1, phase, adapter, at: new Date().toISOString() };
    result.checkpoints.push(stage);
    result.lastCheckpoint = stage;
    const bytes = JSON.stringify(result, null, 2) + '\n';
    atomicWrite(join(output, 'checkpoints', String(stage.sequence).padStart(4, '0') + '.json'), bytes);
    atomicWrite(join(output, 'result.json'), bytes);
  };
  return {
    checkpoint,
    receive(adapter, bytes) {
      if (!/^[a-z]+$/.test(adapter)) throw new Error('invalid evidence adapter');
      const path = join('raw-page-reports', `${String(result.rawPageReports.length + 1).padStart(4, '0')}-${adapter}.body`);
      atomicWrite(join(output, path), bytes);
      const record = { adapter, path, byteLength: bytes.length,
        sha256: createHash('sha256').update(bytes).digest('hex'), parsed: false };
      result.rawPageReports.push(record);
      checkpoint('page-report-received', adapter);
      try {
        const value = JSON.parse(bytes.toString('utf8'));
        record.parsed = true;
        checkpoint('page-report-parsed', adapter);
        return value;
      } catch (error) {
        record.error = String(error);
        checkpoint('page-report-invalid', adapter);
        throw error;
      }
    },
  };
}

export { createGpuEvidence };
