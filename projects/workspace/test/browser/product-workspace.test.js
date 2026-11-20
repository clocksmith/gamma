// Real stock Chromium: independent page observations, popup grants, scoped reads and restart.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { createPlaywrightAdapter } from '../../src/adapters/playwright-adapter.js';
import { createCdpAdapter } from '../../src/adapters/cdp-adapter.js';
const server = createServer((req, res) => {
  res.setHeader('content-type', 'text/html');
  res.end(`<title>Private title</title><div id="shared">Shared ${req.url}<input id="inside"><a id="popup" href="/popup" target="_blank">Open popup</a></div><div id="private">Secret outside shared region <input id="outside" value="private-value"></div><form action="http://127.0.0.1:1/forbidden" method="post"><button id="external">External submit</button></form><form id="regional-form" action="/inside" method="post"><button id="regional-submit">Regional submit</button></form><button id="swap" onclick="document.querySelector('#regional-form').action='http://127.0.0.1:1/changed'">Change form destination</button>`);
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const root = mkdtempSync(join(tmpdir(), 'fawn-multipage-'));
try {
  for (const [name, createAdapter] of Object.entries({ playwright: createPlaywrightAdapter, cdp: createCdpAdapter })) {
    const config = loadServiceConfig(undefined, { browserChannel: process.env.FAWN_WORKSPACE_TEST_BROWSER_CHANNEL ?? 'chrome', headless: true });
    let service = await WorkspaceService.open({ stateDir: join(root, name), config, createAdapter });
    try {
      const workspaceId = 'research';
      const admin = { workspaceId, ...await service.createWorkspace({ workspaceId, scopedReads: true }) };
      const owner = { workspaceId, ...await service.assignOwner({ ...admin, ownerId: 'agent' }) };
      await service.inspect(admin);
      const second = await service.openPage(admin);
      const grant = { ...admin, grantId: 'pages', ownerId: 'agent', intents: ['research'], actionKinds: ['navigate', 'fill', 'click', 'submit'],
        targetOrigins: [origin], pageIds: ['main', second.pageId], readRegions: null };
      await service.grantAuthorization(grant);
      const observe = pageId => service.observe({ ...owner, pageId });
      const act = async (pageId, observation, spec) => (await service.submitAction({ ...owner, pageId,
        actionId: randomUUID(), authorizedIntent: 'research', observationVersion: observation.observationVersion, ...spec })).result;
      for (const [pageId, path] of [['main', '/first'], [second.pageId, '/second']]) {
        assert.equal((await act(pageId, await observe(pageId), { kind: 'navigate', target: { url: origin + path } })).outcome, 'completed');
      }
      const first = await observe('main');
      assert.equal(first.targetFormActions['#external'], 'http://127.0.0.1:1/forbidden');
      await assert.rejects(act('main', first, { kind: 'submit', target: first.elements.find(value => value.selector === '#external'),
        completion: { completedWhen: [{ kind: 'element-present', selector: '#receipt' }] } }), /unauthorized-target/);
      const bound = await service.observe({ ...owner, pageId: 'main', regions: ['#regional-submit'] });
      await act('main', bound, { kind: 'click', target: bound.elements.find(value => value.selector === '#swap') });
      const changedForm = await act('main', bound, { kind: 'submit', target: bound.elements.find(value => value.selector === '#regional-submit'),
        observationScope: { kind: 'regions', selectors: ['#regional-submit'] },
        completion: { completedWhen: [{ kind: 'element-present', selector: '#receipt' }] } });
      assert.equal(changedForm.dispatchStatus, 'never-dispatched');
      assert.equal(changedForm.neverDispatched.code, 'target-changed');
      await observe(second.pageId);
      const fresh = await observe('main');
      const target = fresh.elements.find(value => value.selector === '#inside');
      assert.equal((await act('main', fresh, { kind: 'fill', target, params: { value: 'first only' } })).outcome, 'completed');
      assert.equal((await observe(second.pageId)).elements.find(value => value.selector === '#inside').value, '');
      await assert.rejects(act(second.pageId, first, { kind: 'fill', target, params: { value: 'cross page' } }), /observation/i);
      const current = await observe('main');
      assert.equal((await act('main', current, { kind: 'click', target: current.elements.find(value => value.selector === '#popup') })).outcome, 'completed');
      let state;
      for (let i = 0; i < 30; i++) { state = await service.inspect(admin); if (state.pages.length === 3) break; await new Promise(resolve => setTimeout(resolve, 30)); }
      const popup = state.pages.find(value => !['main', second.pageId].includes(value.pageId));
      assert.ok(popup && !popup.closed, `${name}: popup must have its own page identity`);
      assert.equal(popup.openerId, 'main');
      await assert.rejects(observe(popup.pageId), /observation grant/);
      await service.revokeAuthorization({ ...admin, grantId: 'pages' });
      await service.grantAuthorization({ ...grant, grantId: 'region', pageIds: ['main'], readRegions: ['#shared'] });
      const scoped = await observe('main');
      assert.ok(scoped.text.includes('Shared'));
      assert.ok(!JSON.stringify(scoped).includes('private-value'));
      assert.ok(!scoped.text.includes('Secret'));
      assert.equal(scoped.title, '');
      assert.ok(!scoped.elements.some(value => value.selector === '#outside'));
      const blocked = await act('main', scoped, { kind: 'fill', target: scoped.elements.find(value => value.selector === '#inside'), params: { value: 'blocked' },
        preconditions: [{ kind: 'element-absent', selector: '#private' }] });
      assert.equal(blocked.dispatchStatus, 'never-dispatched', 'Out-of-scope absence must not become evidence');
      await service.revokeAuthorization({ ...admin, grantId: 'region' });
      await assert.rejects(observe('main'), /observation grant/);
      await service.close();
      service = await WorkspaceService.open({ stateDir: join(root, name), config, createAdapter });
      const restored = await service.inspect(admin);
      assert.deepEqual(new Set(restored.pages.map(value => value.pageId)), new Set(state.pages.map(value => value.pageId)));
      assert.ok(restored.actions.some(value => value.pageId === second.pageId));
      console.log(`ok: ${name} page identity, popup isolation, regional privacy, live authority and journal restart`);
    } finally { await service.close(); }
  }
} finally { await new Promise(resolve => server.close(resolve)); rmSync(root, { recursive: true, force: true }); }
