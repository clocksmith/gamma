// Real Chromium. An investigation on a signed-in site loses its session across a forced release
// and restart. The resuming agent may not type a credential and stops for a person; the person
// signs in directly in the browser; a later agent resumes and finishes. The password never
// reaches an observation, a planner, or either journal.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { WorkspaceService } from '../../src/service.js';
import { WorkspaceController } from '../../src/client/controller.js';
import { createPlaywrightAdapter } from '../../src/adapters/playwright-adapter.js';
import { sha256Hex } from '../../src/journal.js';
import { testBrowserSelection } from '../support/browser-selection.js';
if (process.platform === 'win32') { console.log('skip: forced release is not implemented on Windows'); process.exit(0); }

const SECRET = `correct-horse-${randomUUID()}`;
const sessions = new Set(), logins = [];
const site = createServer((req, res) => {
  const session = /(?:^|;\s*)session=([^;]+)/.exec(req.headers.cookie ?? '')?.[1];
  res.setHeader('content-type', 'text/html');
  if (req.method === 'POST' && req.url === '/login') {
    let body = ''; req.on('data', bytes => { body += bytes; }); req.on('end', () => {
      const accepted = new URLSearchParams(body).get('password') === SECRET;
      logins.push({ accepted });
      if (!accepted) { res.writeHead(303, { location: '/login' }); return res.end(); }
      const id = randomUUID(); sessions.add(id);
      res.writeHead(303, { location: '/reports', 'set-cookie': `session=${id}; Max-Age=86400; Path=/; HttpOnly` }); res.end();
    }); return;
  }
  if (req.url === '/reports' && sessions.has(session)) {
    return res.end('<title>Incident reports</title><h1>Incident reports</h1><p id="report">INC-42: checkout latency rose after the cache change.</p>');
  }
  if (req.url === '/reports') { res.writeHead(303, { location: '/login' }); return res.end(); }
  res.end('<title>Sign in</title><h1>Sign in to continue</h1><form method="post" action="/login"><label for="user">User</label><input id="user" name="user">'
    + '<label for="password">Password</label><input id="password" name="password" type="password"><button id="go" type="submit">Sign in</button></form>');
});
await new Promise(resolve => site.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${site.address().port}`;
const root = mkdtempSync(join(tmpdir(), 'fawn-sign-in-handback-'));
const stateDir = join(root, 'service'), clientDir = join(root, 'client');
const client = { ...JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url))), maxTurns: 6 };
const { config } = testBrowserSelection(root);
let service, controller, adapter;
const start = async (planner = null) => {
  service = await WorkspaceService.open({ stateDir, config, createAdapter: options => (adapter = createPlaywrightAdapter(options)) });
  controller = new WorkspaceController({ service, stateDir: clientDir, config: client, planner });
  await controller.restore();
};
// A person at the browser window: typed straight into the page, never through the workspace.
const personSignsIn = async (id) => {
  const page = adapter._page(id, 'main');
  await page.fill('#user', 'investigator'); await page.fill('#password', SECRET);
  return page;
};
const scripted = (decide) => { const seen = []; let turn = 0;
  return { seen, identity: { model: 'controlled-sign-in-loop' }, next: async (context) => { seen.push(context); return decide(context, turn++); } }; };
const latest = context => context.history.findLast(event => event.event === 'tool-result' && event.output?.text)?.output;
const delegation = { pageIds: ['main'], origins: [origin], actionKinds: ['navigate', 'fill', 'click', 'submit'] };
const run = async (id, planner, task, resume) => {
  controller.planner = planner;
  await controller.delegate(id, { ...delegation, task, resume });
  await controller.active.get(id)?.done;
  return controller.store.get(id).run;
};
try {
  await start();
  const { id } = await controller.create({ goal: 'Summarize the incident reports' });
  await controller.navigate(id, { pageId: 'main', url: `${origin}/reports` });
  const page = await personSignsIn(id);
  // The field is filled but not yet submitted: what the workspace can read must not contain it.
  const filled = await service.observe({ ...await controller.humanPage(id, 'main'), pageId: 'main' });
  assert.ok(!JSON.stringify(filled).includes(SECRET), 'an observation never carries a typed password');
  assert.equal(filled.elements.find(element => element.selector === '#password').value, '[hidden]', 'only that the field is filled');
  await assert.rejects(service.submitAction({ ...controller.owner(id), pageId: 'main', actionId: randomUUID(), authorizedIntent: 'human', kind: 'fill',
    target: { selector: '#password', digest: filled.elements.find(element => element.selector === '#password').digest }, params: { value: 'typed through the workspace' }, observationVersion: filled.observationVersion }),
  /password field/, 'the service refuses a password as a journaled action, even from the person');
  await Promise.all([page.waitForURL(`${origin}/reports`), page.click('#go')]);

  // Session A: a signed-in agent reads and saves the report.
  const first = await run(id, scripted((context, turn) => turn === 0 ? { tool: 'observe', input: { pageId: 'main' } }
    : turn === 1 ? { tool: 'capture', input: { pageId: 'main' } } : { tool: 'finish', input: { summary: 'Saved the report.' } }),
  'Read the incident reports and save them as evidence.', false);
  assert.equal(first.status, 'completed', JSON.stringify(first));
  const evidence = Object.values(controller.store.get(id).artifacts).find(value => value.kind === 'evidence');
  assert.match(evidence.source.content, /INC-42/);

  // The site forgets the session (days pass) and the browser has to be ended at shutdown.
  sessions.clear();
  await controller.close({ release: async () => { const releases = await adapter.close({ timeoutMs: 0 }); await service.close(); return { releases }; } });
  assert.deepEqual(logins, [{ accepted: true }]);

  // Session B, another agent: it finds a sign-in page. Guessing a password is stopped before the browser.
  await start();
  await controller.navigate(id, { pageId: 'main', url: `${origin}/reports` });
  const guesser = scripted((context, turn) => {
    if (turn === 0) return { tool: 'observe', input: { pageId: 'main' } };
    const field = latest(context).elements.find(element => element.inputType === 'password');
    return { tool: 'act', input: { pageId: 'main', kind: 'fill', target: { handle: field.handle }, params: { value: 'guessed-password' } } };
  });
  const guessed = await run(id, guesser, 'Continue the incident summary.', true);
  assert.equal(guessed.status, 'needs-attention');
  assert.match(guessed.detail, /Passwords are entered by a person/);
  assert.equal(guesser.seen[0].handoff.lastBrowserRelease.forced, true, 'the resuming agent is told the browser was ended');
  assert.match(latest(guesser.seen[1]).title, /Sign in/);

  // Session B again: the agent asks for the sign-in instead.
  const asker = scripted((context, turn) => turn === 0 ? { tool: 'observe', input: { pageId: 'main' } }
    : { tool: 'ask_human', input: { reason: `Sign in at ${origin}/login; the session for the incident reports is gone.` } });
  const asked = await run(id, asker, 'Continue the incident summary.', true);
  assert.equal(asked.status, 'needs-attention');
  assert.match(asked.detail, /Sign in at/);
  assert.equal(logins.length, 1, 'no agent submitted the sign-in form');

  // The person takes over, signs in at the browser and hands the work back.
  await controller.takeOver(id);
  const again = await personSignsIn(id);
  await Promise.all([again.waitForURL(`${origin}/reports`), again.click('#go')]);
  controller.humanNote(id, 'Signed in again; continue.');
  const finisher = scripted((context, turn) => {
    if (turn === 0) return { tool: 'observe', input: { pageId: 'main' } };
    if (turn === 1) { assert.match(latest(context).text, /INC-42/, 'the returning agent is signed in'); return { tool: 'capture', input: { pageId: 'main' } }; }
    if (turn === 2) return { tool: 'record', input: { kind: 'finding', text: 'INC-42 follows the cache change.', dependsOn: [evidence.id] } };
    return { tool: 'finish', input: { summary: 'Summary recorded from the signed-in report.' } };
  });
  const finished = await run(id, finisher, 'Continue the incident summary.', true);
  assert.equal(finished.status, 'completed', JSON.stringify(finished));
  assert.ok(finisher.seen[0].handoff.human.some(entry => entry.event === 'note' && /Signed in again/.test(entry.text)));
  assert.ok(finisher.seen[0].handoff.sessions.some(session => /Sign in at/.test(session.finishProposal?.text ?? '')), 'the handoff shows that an agent asked for the sign-in');
  const project = controller.store.get(id);
  assert.ok(Object.values(project.artifacts).some(value => value.kind === 'finding'));
  const saved = project.artifacts[evidence.id];
  assert.equal(saved.source.sha256, sha256Hex(saved.source.content), 'evidence from before the restart is intact');
  assert.deepEqual(logins, [{ accepted: true }, { accepted: true }], 'only the person signed in, once each time');
  await controller.close({ release: () => service.close() });
  for (const file of [join(stateDir, 'journal.jsonl'), join(clientDir, 'investigations', 'investigation.jsonl')]) {
    const bytes = readFileSync(file, 'utf8');
    assert.ok(!bytes.includes(SECRET), `${file} never contains the password`);
    assert.ok(!bytes.includes('guessed-password') || file.includes('investigation'), 'a rejected guess is not journaled by the service');
  }
  for (const context of [...guesser.seen, ...asker.seen, ...finisher.seen]) assert.ok(!JSON.stringify(context).includes(SECRET), 'no planner ever receives the password');
  console.log('ok: session lost across a forced release, agent stopped from typing a password, human sign-in at the browser, resumed completion, password absent from observations, planners and journals');
} finally {
  await controller?.close().catch(() => {}); await service?.close().catch(() => {});
  site.close(); rmSync(root, { recursive: true, force: true });
}
