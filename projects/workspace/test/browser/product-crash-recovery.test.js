// Real Chromium + real journals. The site commits, then SIGKILL destroys the
// owning product process before outcome persistence; no graceful close is used.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { fork, execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, appendFileSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';
import { WorkspaceService } from '../../src/service.js';
import { WorkspaceController } from '../../src/client/controller.js';
import { createPlaywrightAdapter } from '../../src/adapters/playwright-adapter.js';
import { readVerifiedJournal, sha256Hex } from '../../src/journal.js';
import { testBrowserSelection } from '../support/browser-selection.js';
if (process.platform === 'win32') {
  console.log('skip: the SIGSTOP/SIGKILL boundary test requires a POSIX host; Windows recovery is not exercised');
  process.exit(0);
}
const root = mkdtempSync(join(tmpdir(), 'fawn-product-process-crash-'));
const receipts = join(root, 'tracker-comments.jsonl'), marker = join(root, 'effect-boundary.json');
const comment = 'The selected option must be committed to application state; inspect the change event handler.';
const comments = () => existsSync(receipts) ? readFileSync(receipts, 'utf8').trim().split('\n').filter(Boolean).map(line => JSON.parse(line)) : [];
const escape = text => text.replace(/[&<>"']/g, value => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[value]);
const tracker = createServer((req, res) => {
  if (req.method === 'POST' && req.url === '/comments') {
    let body = ''; req.on('data', bytes => { body += bytes; }); req.on('end', () => {
      appendFileSync(receipts, JSON.stringify({ text: new URLSearchParams(body).get('body') }) + '\n');
      res.writeHead(303, { location: '/issue' }); res.end();
    }); return;
  }
  res.setHeader('content-type', 'text/html');
  res.end(`<title>Crash recovery tracker</title><h1>Combobox investigation</h1><ul id="comments">${comments().map(value => `<li>${escape(value.text)}</li>`).join('')}</ul><form method="post" action="/comments"><label for="body">Comment</label><textarea id="body" name="body"></textarea><button id="post">Post comment</button></form>`);
});
await new Promise(resolve => tracker.listen(0, '127.0.0.1', resolve));
const trackerUrl = `http://127.0.0.1:${tracker.address().port}/issue`;
const client = { ...JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url))), maxTurns: 4 };
let child, childExit, service, controller, output = '', descendants = [];
function processTable() {
  return execFileSync('ps', ['-axo', 'pid=,ppid=,args='], { encoding: 'utf8' }).split('\n').flatMap(line => {
    const match = line.match(/^\s*(\d+)\s+(\d+)\s+(.+)$/); return match ? [{ pid: Number(match[1]), parent: Number(match[2]), command: match[3] }] : [];
  });
}
function ownedDescendants(pid) {
  const table = processTable(), owned = new Set([pid]);
  let changed; do { changed = false; for (const value of table) if (owned.has(value.parent) && !owned.has(value.pid)) { owned.add(value.pid); changed = true; } } while (changed);
  return table.filter(value => value.pid !== pid && owned.has(value.pid));
}
function stopOwnedBrowsers() {
  const current = new Map(processTable().map(value => [value.pid, value.command]));
  // Recheck identity; never use a broad browser-name or process-group kill.
  for (const value of [...descendants].reverse()) if (current.get(value.pid) === value.command) {
    try { process.kill(value.pid, 'SIGKILL'); } catch (error) { if (error.code !== 'ESRCH') throw error; }
  }
}
async function waitFor(predicate, detail) {
  const deadline = Date.now() + 45000;
  while (!predicate()) {
    if (childExit) throw Error(`Child exited before ${detail}: ${JSON.stringify(childExit)}\n${output}`);
    if (Date.now() > deadline) throw Error(`Timed out waiting for ${detail}\n${output}`);
    await delay(20);
  }
}
try {
  child = fork(fileURLToPath(new URL('../support/product-crash-child.js', import.meta.url)), [root, trackerUrl, comment], { stdio: ['ignore', 'pipe', 'pipe', 'ipc'] });
  child.stdout.on('data', bytes => { output += bytes; }); child.stderr.on('data', bytes => { output += bytes; });
  child.on('error', error => { childExit = { error: error.message }; });
  const exited = new Promise(resolve => child.once('exit', (code, signal) => { childExit = { code, signal }; resolve(childExit); }));
  let boundary;
  await waitFor(() => {
    try { boundary = JSON.parse(readFileSync(marker, 'utf8')); return true; }
    catch (error) { if (error.code === 'ENOENT' || error instanceof SyntaxError) return false; throw error; }
  }, 'a committed effect before outcome persistence');
  assert.equal(boundary.pid, child.pid);
  assert.deepEqual(comments(), [{ text: comment }], 'the real site durably accepted exactly one post before the kill');
  const journalPath = join(root, 'service/journal.jsonl');
  const beforeBytes = readFileSync(journalPath);
  const before = readVerifiedJournal(journalPath);
  assert.ok(before.records.some(record => record.type === 'authorization-granted' && record.body.grant.ownerId === 'agent'), 'the crashed process left a real delegated grant');
  assert.ok(before.records.some(record => record.type === 'action-dispatch-started' && record.body.actionId === boundary.actionId));
  assert.ok(!before.records.some(record => record.type === 'action-outcome' && record.body.actionId === boundary.actionId), 'the process is stopped before any outcome append');
  descendants = ownedDescendants(child.pid);
  assert.ok(descendants.some(value => /chrome|chromium/i.test(value.command)), 'the killed process owns a real browser');
  child.kill('SIGKILL');
  assert.deepEqual(await exited, { code: null, signal: 'SIGKILL' });
  stopOwnedBrowsers();
  descendants = [];
  const selected = testBrowserSelection(root);
  service = await WorkspaceService.open({ stateDir: join(root, 'service'), config: selected.config, createAdapter: createPlaywrightAdapter });
  controller = new WorkspaceController({ service, stateDir: join(root, 'client'), config: client });
  await controller.restore();
  const id = boundary.id, recovered = await service.inspect(controller.admin(id));
  const uncertain = recovered.actions.find(action => action.actionId === boundary.actionId);
  assert.equal(uncertain.isUncertain, true);
  assert.equal(uncertain.outcome, 'unknown');
  assert.equal(uncertain.outcomeBasis, 'restart-after-dispatch-start');
  assert.equal(recovered.grants.filter(grant => grant.ownerId === 'agent').length, 0, 'no old agent grant survives process death and takeover');
  assert.equal(controller.store.get(id).run.status, 'needs-attention');
  const saved = controller.store.get(id).artifacts[boundary.evidenceId];
  assert.equal(saved.source.sha256, sha256Hex(saved.source.content));
  assert.match(saved.source.content, /Combobox investigation/);
  await controller.navigate(id, { pageId: 'main', url: trackerUrl });
  let turn = 0;
  controller.planner = { identity: { model: 'controlled-different-returning-agent' }, async next(context) {
    // On resume the service checks the interrupted post's own recorded completion condition on the live
    // site, so the returning agent starts with the outcome established and spends no request on it.
    assert.equal(context.handoff.unresolvedActionCount, 0);
    const established = context.history.find(event => event.event === 'tool-requested' && event.tool === 'reconcile');
    assert.equal(established?.input.actionId, boundary.actionId, 'the returning agent sees how the outcome was established');
    if (turn++ === 0) return { tool: 'observe', input: { pageId: 'main' } };
    const observed = context.history.findLast(event => event.event === 'tool-result' && event.output?.text)?.output;
    assert.ok(observed.text.includes(comment), 'returning agent observes the accepted post on the live site');
    return { tool: 'finish', input: { summary: 'The live tracker confirms the earlier post; no repeat is needed.' } };
  } };
  await controller.delegate(id, { pageIds: ['main'], origins: [new URL(trackerUrl).origin], actionKinds: ['submit', 'navigate'], task: 'Establish the earlier post and finish without duplicating it.', resume: true });
  await controller.active.get(id)?.done;
  assert.equal(controller.store.get(id).run.status, 'completed', JSON.stringify(controller.store.get(id).run));
  assert.equal((await controller.handoff(id)).unresolvedActionCount, 0);
  const settled = await service.action({ ...controller.owner(id), actionId: boundary.actionId });
  assert.equal(settled.reconciliation.result, 'effect-present');
  assert.deepEqual(comments(), [{ text: comment }], 'a different returning agent never duplicates the accepted post');
  const after = readVerifiedJournal(join(root, 'service/journal.jsonl'));
  assert.deepEqual(after.records.slice(0, before.records.length), before.records, 'recovery preserves the complete pre-crash journal');
  assert.ok(readFileSync(journalPath).subarray(0, beforeBytes.length).equals(beforeBytes), 'recovery preserves the exact pre-crash journal bytes');
  console.log('ok: real Chromium post, SIGKILL before outcome append, evidence/grant recovery, live reconciliation, zero duplicate posts');
} finally {
  if (child && !childExit) { descendants = ownedDescendants(child.pid); child.kill('SIGKILL'); }
  stopOwnedBrowsers();
  await controller?.close().catch(() => {}); await service?.close().catch(() => {});
  await new Promise(resolve => tracker.close(resolve));
  rmSync(root, { recursive: true, force: true });
}
