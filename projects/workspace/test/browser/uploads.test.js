// Harmless local bytes only. Both adapters must attach a hidden input through trusted dispatch,
// prove the page kept it, and preserve uncertainty instead of repeating a possible disclosure.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { sha256Hex } from '../../src/journal.js';
import { createPlaywrightAdapter } from '../../src/adapters/playwright-adapter.js';
import { createCdpAdapter } from '../../src/adapters/cdp-adapter.js';

const bytes = Buffer.from('Harmless local upload fixture.\n');
const received = [];
const page = `<!doctype html><title>Upload fixture</title>
<label for="file">Local attachment</label><button type="button">Choose attachment</button>
<input id="file" type="file" accept=".txt" hidden><output id="receipt"></output>
<input id="revert" type="file" hidden><input id="multiple" type="file" multiple hidden>
<input id="disabled" type="file" disabled><input id="other"><a href="/other">Other page</a>
<script>
document.querySelector('#file').addEventListener('change', async event => {
  const file = event.target.files[0];
  await fetch('/uploaded', { method: 'POST', body: await file.arrayBuffer() });
  document.querySelector('#receipt').textContent = file.name + ' accepted';
});
document.querySelector('#revert').addEventListener('change', event => setTimeout(() => { event.target.value = ''; }, 50));
</script>`;
const server = createServer(async (request, response) => {
  if (request.url === '/uploaded') {
    const chunks = [];
    for await (const chunk of request) chunks.push(chunk);
    received.push(sha256Hex(Buffer.concat(chunks)));
    response.end('ok');
  } else { response.setHeader('content-type', 'text/html'); response.end(page); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const root = mkdtempSync(join(tmpdir(), 'fawn-uploads-'));
const base = loadServiceConfig(undefined, { browserChannel: process.env.FAWN_WORKSPACE_TEST_BROWSER_CHANNEL ?? 'chrome', headless: true });
const config = { ...base, dispatch: { ...base.dispatch, completionTimeoutMs: 500, valueSettleMs: 150 } };
try {
  for (const [name, createAdapter] of Object.entries({ playwright: createPlaywrightAdapter, cdp: createCdpAdapter })) {
    const stateDir = join(root, name);
    let service = await WorkspaceService.open({ stateDir, config, createAdapter });
    try {
      const workspaceId = 'uploads';
      const admin = { workspaceId, ...await service.createWorkspace({ workspaceId }) };
      const grant = { ...admin, grantId: 'files', ownerId: 'agent', intents: ['attachment'],
        actionKinds: ['navigate', 'upload'], targetOrigins: [origin], pageIds: ['main'], readRegions: null };
      await assert.rejects(service.grantAuthorization(grant), /explicitly selected/);
      const approved = await service.grantAuthorization({ ...grant,
        uploadFiles: [{ name: 'fixture.txt', base64: bytes.toString('base64') }] });
      const files = approved.uploadFiles;
      const owner = { workspaceId, ...await service.assignOwner({ ...admin, ownerId: 'agent' }) };
      const command = async (selector = '#file', extra = {}) => {
        const observation = await service.observe(owner);
        const target = observation.elements.find(element => element.selector === selector);
        assert.ok(target, `${name}: hidden file input is observable`);
        return { ...owner, actionId: randomUUID(), authorizedIntent: 'attachment', kind: 'upload',
          target: { handle: target.handle }, observationVersion: observation.observationVersion,
          params: { fileIds: files.map(file => file.fileId) },
          effect: { external: true, effectKey: randomUUID() }, completion: { completedWhen: [
            { kind: 'input-files-equal', selector, files: files.map(({ name, byteLength }) => ({ name, byteLength })) },
          ] }, ...extra };
      };
      const observation = await service.observe(owner);
      assert.equal((await (await service.submitAction({ ...owner, actionId: 'navigate', authorizedIntent: 'attachment',
        kind: 'navigate', target: { url: origin }, observationVersion: observation.observationVersion })).result).outcome, 'completed');

      await assert.rejects(service.submitAction(await command('#file', { params: { fileIds: ['unapproved'] } })), error => error.code === 'unauthorized-target');
      await assert.rejects(service.submitAction(await command('#file', { params: { fileIds: [files[0].fileId], path: '/not-authorized' } })), /only distinct approved/);
      await assert.rejects(service.submitAction(await command('#file', { effect: { external: false } })), /discloses file bytes/);
      const wrongInput = await (await service.submitAction(await command('#other'))).result;
      assert.equal(wrongInput.dispatchStatus, 'never-dispatched');
      const disabled = await (await service.submitAction(await command('#disabled'))).result;
      assert.equal(disabled.dispatchStatus, 'never-dispatched');

      const upload = await command();
      upload.completion.completedWhen.push({ kind: 'element-text-includes', selector: '#receipt', value: 'fixture.txt accepted' });
      const completed = await (await service.submitAction(upload)).result;
      assert.equal(completed.outcome, 'completed', JSON.stringify(completed));
      assert.equal(received.at(-1), sha256Hex(bytes), `${name}: fixture server independently received the exact approved bytes`);
      const reverted = await (await service.submitAction(await command('#revert'))).result;
      assert.equal(reverted.outcome, 'unknown');
      assert.equal(reverted.outcomeBasis, 'value-reverted');

      await service.grantAuthorization({ ...admin, grantId: 'wrong-site', ownerId: 'agent', intents: ['other-site'],
        actionKinds: ['upload'], targetOrigins: ['https://not-authorized.invalid'],
        uploadFiles: [{ name: 'fixture.txt', base64: bytes.toString('base64') }] });
      await assert.rejects(service.submitAction(await command('#file', { authorizedIntent: 'other-site' })), error => error.code === 'unauthorized-target');
      const stale = await command();
      await service.observe(owner);
      await assert.rejects(service.submitAction(stale), error => error.code === 'stale-observation');

      // Pending intents are rechecked after revocation, before any browser disclosure.
      await service.close();
      let revoked = false;
      service = await WorkspaceService.open({ stateDir, config, createAdapter, hooks: {
        afterIntentPersisted(request) {
          if (request.kind === 'upload' && !revoked) { revoked = true; void service.revokeAuthorization({ ...admin, grantId: 'files' }); }
        },
      } });
      const fresh = await service.observe(owner);
      await (await service.submitAction({ ...owner, actionId: 'reopen', authorizedIntent: 'attachment', kind: 'navigate',
        target: { url: origin }, observationVersion: fresh.observationVersion })).result;
      // Replacing a grant stages new immutable bytes instead of mutating an old file identity.
      const renewed = await service.grantAuthorization({ ...grant, uploadFiles: [{ name: 'fixture.txt', base64: bytes.toString('base64') }] });
      files.splice(0, files.length, ...renewed.uploadFiles);
      revoked = false;
      const noDisclosure = await (await service.submitAction(await command())).result;
      assert.equal(noDisclosure.dispatchStatus, 'never-dispatched');

      // A staged snapshot that changed after authorization fails before dispatch.
      const restored = await service.grantAuthorization({ ...grant, uploadFiles: [{ name: 'fixture.txt', base64: bytes.toString('base64') }] });
      files.splice(0, files.length, ...restored.uploadFiles);
      revoked = true;
      writeFileSync(join(stateDir, 'uploads', files[0].fileId, 'fixture.txt'), Buffer.alloc(bytes.length));
      const changed = await (await service.submitAction(await command())).result;
      assert.equal(changed.dispatchStatus, 'never-dispatched');
      assert.match(changed.neverDispatched.detail, /bytes changed/);
      const journal = readFileSync(join(stateDir, 'journal.jsonl'), 'utf8');
      assert.ok(!journal.includes(bytes.toString('base64')), 'File bytes stay out of the durable action journal');
      await service.revokeAuthorization({ ...admin, grantId: 'files' });
      await service.revokeAuthorization({ ...admin, grantId: 'wrong-site' });
      await service.close();
      assert.deepEqual(readdirSync(join(stateDir, 'uploads')), [], 'Only after browsers close can revoked files retire');
      service = null;
      console.log(`ok: ${name} upload bytes, hidden input, page receipt, refusal, revocation, uncertainty and staging cleanup`);
    } finally { await service?.close(); }
  }
} finally {
  await new Promise(resolve => server.close(resolve));
  rmSync(root, { recursive: true, force: true });
}
