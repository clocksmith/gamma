import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtempSync, mkdirSync, writeFileSync, symlinkSync, rmSync, realpathSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { evidencePath, caseSetMatches } from '../../qualification/evidence-input.js';

const directory = realpathSync(mkdtempSync(join(tmpdir(), 'fawn-evidence-')));
const hash = (value) => createHash('sha256').update(value).digest('hex');
try {
  const root = join(directory, 'root');
  mkdirSync(join(root, 'run'), { recursive: true });
  const file = join(root, 'run', 'journal.jsonl');
  writeFileSync(file, 'receipt');
  for (const platform of ['linux', 'darwin', 'win32']) {
    assert.equal(evidencePath(root, 'run/journal.jsonl', platform), file);
    for (const path of ['../root/run/journal.jsonl', '/run/journal.jsonl', '', 'run\0bad']) {
      assert.throws(() => evidencePath(root, path, platform));
    }
  }
  assert.equal(evidencePath(root, 'run\\journal.jsonl', 'win32'), file);
  for (const path of ['C:run\\journal.jsonl', 'C:\\run\\journal.jsonl', '\\\\server\\share\\file', 'run\\..\\run\\journal.jsonl']) {
    assert.throws(() => evidencePath(root, path, 'win32'));
  }
  assert.throws(() => evidencePath(root, 'run/journal.jsonl', 'unknown'));
  if (process.platform !== 'win32') {
    writeFileSync(join(root, 'literal\\name'), 'posix filename');
    assert.equal(evidencePath(root, 'literal\\name', 'linux'), join(root, 'literal\\name'));
    symlinkSync(directory, join(root, 'escape'));
    assert.throws(() => evidencePath(root, 'escape', 'linux'));
  }
  const current = Buffer.from('{\n  "rule": "reject", "count": 102\n}\n');
  const crlf = Buffer.from(current.toString().replaceAll('\n', '\r\n'));
  assert.equal(caseSetMatches(root, hash(current), current), true);
  assert.equal(caseSetMatches(root, hash(crlf), current), false);
  writeFileSync(join(root, 'case-set.json'), crlf);
  assert.equal(caseSetMatches(root, hash(crlf), current), true);
  assert.equal(caseSetMatches(root, hash(current), current), false);
  const changed = Buffer.from('{"rule":"accept","count":102}');
  writeFileSync(join(root, 'case-set.json'), changed);
  assert.equal(caseSetMatches(root, hash(changed), current), false);
  console.log('ok: retained path containment and exact-byte frozen-rule evidence');
} finally {
  rmSync(directory, { recursive: true, force: true });
}
