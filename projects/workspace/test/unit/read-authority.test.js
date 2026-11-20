// Public API inputs and returned snapshots cannot mutate durable authority; reads expire too.
import assert from 'node:assert/strict';
import { setupWorkspace, ORIGIN } from '../support/harness.js';
const context = await setupWorkspace();
try {
  const { service, clock } = context;
  const workspaceId = 'scoped-reader';
  const admin = { workspaceId, ...await service.createWorkspace({ workspaceId, scopedReads: true }) };
  const owner = { workspaceId, ...await service.assignOwner({ ...admin, ownerId: 'reader' }) };
  const grant = { ...admin, grantId: 'reader', ownerId: 'reader', intents: ['research'], actionKinds: ['navigate', 'fill'],
    targetOrigins: [ORIGIN], pageIds: ['main'], readRegions: null, expiresAt: new Date(clock.now() + 1000).toISOString() };
  await service.grantAuthorization(grant);
  grant.intents.push('not-granted'); grant.targetOrigins.push('https://foreign.invalid');
  const observation = await service.observe(owner);
  const spec = { ...owner, kind: 'navigate', target: { url: 'https://foreign.invalid/' }, observationVersion: observation.observationVersion };
  await assert.rejects(service.submitAction({ ...spec, actionId: 'mutated-input', authorizedIntent: 'not-granted' }), /unauthorized-intent/);
  const exposed = await service.inspect(admin);
  exposed.grants[0].targetOrigins.push('https://foreign.invalid');
  await assert.rejects(service.submitAction({ ...spec, actionId: 'mutated-output', authorizedIntent: 'research' }), /unauthorized-target/);
  const destination = await service.submitAction({ ...spec, actionId: 'allowed', authorizedIntent: 'research', target: { url: `${ORIGIN}/form` } });
  assert.equal((await destination.result).outcome, 'completed');
  const form = await service.observe(owner);
  form.targetDigests['#forged'] = 'injected';
  await assert.rejects(service.submitAction({ ...owner, actionId: 'forged-observation', authorizedIntent: 'research', kind: 'fill',
    target: { selector: '#forged', digest: 'injected' }, params: { value: 'no' }, observationVersion: form.observationVersion }), /unknown-target/);
  clock.advance(1001);
  await assert.rejects(service.observe(owner), /observation grant/);
  console.log('ok: immutable grant inputs, isolated returned snapshots and expiring read authority');
} finally { await context.service.close(); }
