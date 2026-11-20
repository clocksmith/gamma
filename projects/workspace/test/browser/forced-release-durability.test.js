// Real Chromium. A workspace released by the forced path (the browser is ended because it did
// not exit in time) must keep every journal byte, restore the same recorded work, and report the
// site's live state afterwards instead of what it remembered from before the release.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { WorkspaceService } from '../../src/service.js';
import { createPlaywrightAdapter } from '../../src/adapters/playwright-adapter.js';
import { profileBrowserPids } from '../../src/adapters/bounded-close.js';
import { readVerifiedJournal } from '../../src/journal.js';
import { testBrowserSelection } from '../support/browser-selection.js';
if (process.platform === 'win32') { console.log('skip: forced release is not implemented on Windows'); process.exit(0); }

const seen = [];
const site = createServer((req, res) => {
  const signedIn = /(^|;\s*)session=s1(;|$)/.test(req.headers.cookie ?? '');
  seen.push({ url: req.url, signedIn });
  res.setHeader('content-type', 'text/html');
  if (req.url === '/signin') res.setHeader('set-cookie', 'session=s1; Max-Age=86400; Path=/; HttpOnly');
  res.end(req.url === '/signin' ? '<title>Signed in</title><p id="state">Session started</p>'
    : `<title>Account</title><p id="state">${signedIn ? 'Signed in as investigator' : 'Signed out'}</p>`);
});
await new Promise(resolve => site.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${site.address().port}`;
const root = mkdtempSync(join(tmpdir(), 'fawn-forced-release-')), stateDir = join(root, 'service'), workspaceId = 'investigation';
const { config } = testBrowserSelection(root);
let service, adapter;
const open = async () => WorkspaceService.open({ stateDir, config, createAdapter: options => (adapter = createPlaywrightAdapter(options)) });
const go = async (owner, actionId, path) => {
  const observation = await service.observe(owner);
  const result = await (await service.submitAction({ ...owner, actionId, authorizedIntent: 'investigate', kind: 'navigate',
    target: { url: origin + path }, observationVersion: observation.observationVersion })).result;
  assert.equal(result.outcome, 'completed', `${path}: ${JSON.stringify(result)}`);
};
try {
  service = await open();
  let admin = { workspaceId, ...await service.createWorkspace({ workspaceId }) };
  await service.grantAuthorization({ ...admin, grantId: 'investigate', ownerId: 'agent', intents: ['investigate'],
    actionKinds: ['navigate'], targetOrigins: [origin], pageIds: ['main'], readRegions: null });
  let owner = { workspaceId, ...await service.assignOwner({ ...admin, ownerId: 'agent' }) };
  await go(owner, 'sign-in', '/signin');
  await go(owner, 'account-before', '/account');
  const remembered = await service.observe(owner);
  assert.match(remembered.text, /Signed in as investigator/);
  const recorded = (await service.inspect(admin)).actions.map(({ actionId, kind, outcome }) => ({ actionId, kind, outcome }));
  const journalPath = join(stateDir, 'journal.jsonl'), beforeBytes = readFileSync(journalPath);

  // The browser is ended without being given time to exit: the forced path, not a graceful close.
  const profileDir = join(stateDir, 'profiles', workspaceId);
  const browserPids = profileBrowserPids(profileDir);
  assert.equal(browserPids.length, 1, `one main browser owns ${profileDir}`);
  assert.deepEqual(await adapter.close({ timeoutMs: 0 }), [{ workspaceId, release: 'forced' }]);
  assert.deepEqual(profileBrowserPids(profileDir), [], 'no browser is left on the profile');
  await service.close();
  assert.ok(readFileSync(journalPath).subarray(0, beforeBytes.length).equals(beforeBytes), 'the forced release preserves every journal byte');
  readVerifiedJournal(journalPath);

  // Restart on the same state: recorded work is intact and the profile opens again.
  service = await open();
  const restored = (await service.inspect(admin)).actions.map(({ actionId, kind, outcome }) => ({ actionId, kind, outcome }));
  assert.deepEqual(restored, recorded, 'every recorded action and outcome survives');
  owner = { workspaceId, ...await service.assignOwner({ ...admin, ownerId: 'agent' }) };
  await service.grantAuthorization({ ...admin, grantId: 'investigate-again', ownerId: 'agent', intents: ['investigate'],
    actionKinds: ['navigate'], targetOrigins: [origin], pageIds: ['main'], readRegions: null });
  await go(owner, 'account-after', '/account');
  const live = await service.observe(owner);
  const siteSaw = seen.findLast(request => request.url === '/account');
  // Whether the session cookie reached disk before the forced exit is the browser's business. Either
  // way the workspace must show what the site answers now, never the state it observed before.
  assert.match(live.text, siteSaw.signedIn ? /Signed in as investigator/ : /Signed out/);
  assert.ok(live.observationVersion > remembered.observationVersion);
  console.log(`ok: forced release keeps the journal and recorded actions, reopens the profile and reports live site state (session ${siteSaw.signedIn ? 'survived' : 'was lost and is shown as signed out'})`);
} finally {
  await service?.close().catch(() => {});
  site.close();
  rmSync(root, { recursive: true, force: true });
}
