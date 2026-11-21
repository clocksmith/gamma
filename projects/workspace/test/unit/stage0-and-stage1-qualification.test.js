import assert from 'node:assert/strict';
import test from 'node:test';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';
import { runStage1SuffixAblation } from '../../qualification/stage1-suffix-ablation.js';

test('Stage 0 (#85): observe(ifCurrentVersion) reuses only while revision, owner generation, expiry and URL are current', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'gammatron-stage0-unit-'));
  const config = loadServiceConfig();
  let snapshotCalls = 0;
  const service = await WorkspaceService.open({
    stateDir: dir,
    config,
    createAdapter: () => {
      const inner = new FakeAdapter(join(dir, 'receipts.jsonl'));
      const origSnapshot = inner.snapshot.bind(inner);
      inner.snapshot = async (...args) => {
        snapshotCalls += 1;
        return origSnapshot(...args);
      };
      return inner;
    },
  });

  try {
    const workspaceId = 'stage0-rev';
    const admin = { workspaceId, ...await service.createWorkspace({ workspaceId }) };
    await service.grantAuthorization({
      ...admin,
      grantId: 'g1',
      ownerId: 'agent',
      intents: ['form:fill'],
      actionKinds: ['navigate', 'fill', 'click'],
      targetOrigins: [ORIGIN],
    });
    const owner = { workspaceId, ...await service.assignOwner({ ...admin, ownerId: 'agent' }) };

    const obs0 = await service.observe(owner);
    const navRes = await (await service.submitAction({
      ...owner,
      actionId: 'nav-1',
      authorizedIntent: 'form:fill',
      kind: 'navigate',
      target: { url: `${ORIGIN}/form` },
      observationVersion: obs0.observationVersion,
    })).result;
    assert.equal(navRes.outcome, 'completed');
    const snapsBeforeReuse = snapshotCalls;

    // 1. Reuse while current revision matches `postObservationVersion`: 0 extra adapter snapshots, version unchanged.
    const reused = await service.observe({ ...owner, ifCurrentVersion: navRes.postObservationVersion });
    assert.equal(reused.observationVersion, navRes.postObservationVersion);
    assert.equal(snapshotCalls, snapsBeforeReuse, 'Current revision reuse must not trigger a redundant browser snapshot');

    // 2. Stale `ifCurrentVersion` falls through and records a fresh observation snapshot.
    const fresh = await service.observe({ ...owner, ifCurrentVersion: navRes.postObservationVersion - 1 });
    assert.equal(fresh.observationVersion, navRes.postObservationVersion + 1);
    assert.equal(snapshotCalls, snapsBeforeReuse + 1);

    // 3. Owner handoff invalidates cached observations across generations.
    const nextOwner = { workspaceId, ...await service.assignOwner({ ...admin, ownerId: 'agent' }) };
    const afterHandoff = await service.observe({ ...nextOwner, ifCurrentVersion: fresh.observationVersion });
    assert.equal(afterHandoff.observationVersion, fresh.observationVersion + 1);
    assert.equal(snapshotCalls, snapsBeforeReuse + 2);
  } finally {
    await service.close();
    rmSync(dir, { recursive: true, force: true });
  }
});

test('Stage 1 (#88 / #85): offline snapshot ablation beats exact-hash with 0 unsafe certifications across 4 workflow families', async () => {
  const receipt = await runStage1SuffixAblation();
  assert.equal(receipt.allStage1GatesPassed, true);
  assert.equal(receipt.gates.zeroUnsafeCertifications, true);
  assert.equal(receipt.gates.zeroSkippedApprovals, true);
  assert.equal(receipt.gates.certifiedRejoinK2AtLeast60Pct, true);
  assert.equal(receipt.gates.certifiedRejoinK3AtLeast75Pct, true);
  assert.equal(receipt.gates.plannerCallRatioAtMost065x, true);
});
