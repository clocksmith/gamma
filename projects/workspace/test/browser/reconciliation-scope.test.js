// Lost acknowledgments on a second tab must use that tab's current read authority.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { createPlaywrightAdapter } from '../../src/adapters/playwright-adapter.js';
import { createCdpAdapter } from '../../src/adapters/cdp-adapter.js';

const server = createServer((_req, res) => {
  res.setHeader('content-type', 'text/html');
  res.end('<div id="shared"><label>Name <input id="name"></label></div><div id="private">Secret in second tab</div>');
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const root = mkdtempSync(join(tmpdir(), 'fawn-reconcile-scope-'));
try {
  for (const [name, createAdapter] of Object.entries({ playwright: createPlaywrightAdapter, cdp: createCdpAdapter })) {
    let serial = 0, effects = 0, probes = 0;
    const config = loadServiceConfig(undefined, { browserChannel: process.env.FAWN_WORKSPACE_TEST_BROWSER_CHANNEL ?? 'chrome', headless: true });
    const service = await WorkspaceService.open({ stateDir: join(root, name), config,
      createAdapter: options => {
        const adapter = createAdapter(options), execute = adapter.execute.bind(adapter);
        const probe = adapter.probeElement.bind(adapter);
        adapter.execute = async (...args) => {
          const result = await execute(...args);
          if (args[1].kind === 'fill') { effects++; throw Error('Injected loss after the browser applied the fill'); }
          return result;
        };
        adapter.probeElement = (...args) => { probes++; return probe(...args); };
        return adapter;
      } });
    try {
      const workspaceId = 'recovery';
      const admin = { workspaceId, ...await service.createWorkspace({ workspaceId, scopedReads: true }) };
      const owner = { workspaceId, ...await service.assignOwner({ ...admin, ownerId: 'agent' }) };
      await service.openPage({ ...admin, pageId: 'second' });
      const grant = { ...admin, ownerId: 'agent', intents: ['form'], actionKinds: ['navigate', 'fill'], targetOrigins: [origin] };
      await service.grantAuthorization({ ...grant, grantId: 'both', pageIds: ['main', 'second'], readRegions: null });
      const act = async (pageId, spec) => {
        const observation = await service.observe({ ...owner, pageId });
        const actionId = `action-${++serial}`;
        return (await service.submitAction({ ...owner, pageId, actionId, authorizedIntent: 'form',
          observationVersion: observation.observationVersion, ...spec(observation) })).result;
      };
      for (const pageId of ['main', 'second']) await act(pageId, () => ({ kind: 'navigate', target: { url: `${origin}/${pageId}` } }));
      const lostFill = () => act('second', observation => ({ kind: 'fill',
        target: observation.elements.find(element => element.selector === '#name'), params: { value: 'Applied once' } }));
      const lost = await lostFill();
      assert.equal(lost.outcome, 'unknown');
      assert.equal((await service.observe({ ...owner, pageId: 'second' })).elements.find(element => element.selector === '#name').value, 'Applied once');
      await service.revokeAuthorization({ ...admin, grantId: 'both' });
      await service.grantAuthorization({ ...grant, grantId: 'main-only', pageIds: ['main'], readRegions: null });
      const reconcile = (actionId, extra = {}) => service.reconcile({ ...owner, actionId, method: 'application-state',
        effectPresentWhen: [{ kind: 'input-value-equals', selector: '#name', value: 'Applied once' }], ...extra });
      const before = probes;
      for (const extra of [{}, { pageId: 'main' }, { effectPresentWhen: [] }]) {
        await assert.rejects(reconcile(lost.actionId, extra), /observation grant/, 'A main-tab grant cannot read the second tab');
      }
      assert.equal(probes, before, 'Denied reconciliation must not probe page elements');
      assert.equal((await service.action({ ...owner, actionId: lost.actionId })).isUncertain, true);
      await service.revokeAuthorization({ ...admin, grantId: 'main-only' });
      await service.grantAuthorization({ ...grant, grantId: 'second-region', pageIds: ['second'], readRegions: ['#shared'] });
      const resolved = await reconcile(lost.actionId);
      assert.equal(resolved.reconciliation.result, 'effect-present', 'Omitting pageId uses the recorded action page');
      assert.equal(resolved.isUncertain, false);
      assert.equal(resolved.outcome, 'unknown', 'Reconciliation preserves the original uncertain receipt');

      const regional = await lostFill();
      await service.grantAuthorization({ ...grant, grantId: 'main-wide', pageIds: ['main'], readRegions: null });
      const hidden = await reconcile(regional.actionId, { pageId: 'main',
        effectPresentWhen: [{ kind: 'element-text-includes', selector: '#private', value: 'Secret' }] });
      assert.equal(hidden.reconciliation.result, 'inconclusive');
      assert.ok(!JSON.stringify(hidden.reconciliation).includes('Secret in second tab'));
      assert.equal((await reconcile(regional.actionId, { pageId: 'main' })).reconciliation.result, 'effect-present');
      assert.equal(effects, 2, 'Recovery never retries either browser effect');
      console.log(`ok: ${name} recorded-page recovery, revoked/wrong-page rejection, regional isolation and no repeated effects`);
    } finally { await service.close(); }
  }
} finally { await new Promise(resolve => server.close(resolve)); rmSync(root, { recursive: true, force: true }); }
