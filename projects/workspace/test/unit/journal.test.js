// Journal durability: chain verification, torn-tail repair, corruption and lock handling.
import assert from 'node:assert/strict';
import { appendFileSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { Journal } from '../../src/journal.js';

const FILES = { fileName: 'journal.jsonl', lockFileName: 'journal.lock' };
const DEAD_PID = 2 ** 22 + 17;

function freshDirectory() {
  return mkdtempSync(join(tmpdir(), 'fawn-journal-'));
}

{
  const directory = freshDirectory();
  const journal = Journal.open({ directory, ...FILES });
  journal.append('a', { n: 1 });
  journal.append('b', { n: 2, nested: { z: 1, a: [1, 2] } });
  assert.throws(() => Journal.open({ directory, ...FILES }), { code: 'journal-locked' });
  journal.close();
  const reopened = Journal.open({ directory, ...FILES });
  assert.equal(reopened.records.length, 2);
  assert.equal(reopened.records[1].prevHash, reopened.records[0].hash);
  assert.deepEqual(reopened.recovery, { lockRecoveredFromPid: null, tornTail: null });
  reopened.close();
}

{
  const directory = freshDirectory();
  const journal = Journal.open({ directory, ...FILES });
  journal.append('a', { n: 1 });
  journal.close();
  appendFileSync(join(directory, FILES.fileName), '{"seq":2,"type":"partial');
  const repaired = Journal.open({ directory, ...FILES });
  assert.equal(repaired.records.length, 1);
  assert.equal(repaired.recovery.tornTail.discardedBytes, '{"seq":2,"type":"partial'.length);
  repaired.append('b', { n: 2 });
  repaired.close();
  const text = readFileSync(join(directory, FILES.fileName), 'utf8');
  assert.equal(text.trim().split('\n').length, 2);
  Journal.open({ directory, ...FILES }).close();
}

{
  const directory = freshDirectory();
  const journal = Journal.open({ directory, ...FILES });
  journal.append('a', { n: 1 });
  journal.append('b', { n: 2 });
  journal.close();
  const path = join(directory, FILES.fileName);
  writeFileSync(path, readFileSync(path, 'utf8').replace('"n":1', '"n":9'));
  assert.throws(() => Journal.open({ directory, ...FILES }), { code: 'journal-corrupt' });
  assert.throws(() => Journal.open({ directory, ...FILES }), { code: 'journal-corrupt' });
}

{
  const directory = freshDirectory();
  Journal.open({ directory, ...FILES }).close();
  writeFileSync(join(directory, FILES.lockFileName), JSON.stringify({ pid: DEAD_PID }));
  const recovered = Journal.open({ directory, ...FILES });
  assert.equal(recovered.recovery.lockRecoveredFromPid, DEAD_PID);
  recovered.close();
}

console.log('ok: journal');

// Optional fields and missing usage must hash exactly the JSON bytes that survive restart.
{
  const directory = freshDirectory();
  const journal = Journal.open({ directory, ...FILES });
  const body = { optional: undefined, usage: [undefined, null], nested: { present: true, omitted: undefined } };
  journal.append('json-body', body);
  body.nested.present = false;
  for (const invalid of [NaN, Infinity, () => {}]) assert.throws(() => journal.append('invalid', { invalid }), /finite JSON/);
  journal.append('after-rejection', { valid: true });
  journal.close();
  const restored = Journal.open({ directory, ...FILES });
  assert.deepEqual(restored.records[0].body, { usage: [null, null], nested: { present: true } });
  assert.equal(restored.records.length, 2);
  restored.close();
}
