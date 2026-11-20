// Same-owner/workspace synchronization. Workspace key stays on authorized clients.
import { createCipheriv, createDecipheriv, createHmac, hkdfSync, randomBytes } from 'node:crypto';
import { canonicalJson } from '../journal.js';
import { TraceDag } from './trace-dag.js';

const hash = (key, value) => createHmac('sha256', key).update(canonicalJson(value)).digest('hex');
export class WorkflowSync {
  constructor({ url, workspaceKey, ownerScope, token, accessClientId, accessClientSecret, timeoutMs = 10000 }) {
    const endpoint = new URL(url);
    if (endpoint.protocol !== 'https:' && !(endpoint.protocol === 'http:' && ['127.0.0.1', '[::1]'].includes(endpoint.hostname))) throw Error('Workflow sync requires HTTPS or loopback');
    if (!/^[a-f0-9]{64}$/.test(workspaceKey) || !ownerScope || typeof token !== 'string' || token.length < 32) throw Error('Workspace key, owner and client token required');
    this.url = endpoint.origin; this.ownerScope = ownerScope; this.key = Buffer.from(workspaceKey, 'hex'); this.timeoutMs = timeoutMs;
    this.headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
    if (accessClientId && accessClientSecret) Object.assign(this.headers, { 'CF-Access-Client-Id': accessClientId, 'CF-Access-Client-Secret': accessClientSecret });
  }
  identity({ accountScope, template }) {
    if (![accountScope, template].every(v => typeof v === 'string' && v.trim())) throw Error('Explicit account and template required');
    const scope = [this.ownerScope, accountScope, template];
    const id = hash(this.key, ['namespace-v1', scope]);
    const derive = purpose => Buffer.from(hkdfSync('sha256', this.key, Buffer.from(id, 'hex'), Buffer.from(purpose), 32));
    return { id, encryption: derive('fawn-seal-v1'), dagKey: derive('fawn-trace-v1').toString('hex') };
  }
  empty(scope, limits) { return { ...new TraceDag(limits).export(), key: this.identity(scope).dagKey }; }
  version(scope, dag) { return hash(this.identity(scope).encryption, dag); }
  seal(identity, kind, id, value) {
    const iv = randomBytes(12), cipher = createCipheriv('aes-256-gcm', identity.encryption, iv);
    cipher.setAAD(Buffer.from(canonicalJson([1, identity.id, kind, id])));
    const encrypted = Buffer.concat([cipher.update(canonicalJson(value)), cipher.final()]);
    return Buffer.concat([iv, cipher.getAuthTag(), encrypted]).toString('base64');
  }
  open(identity, kind, id, blob) {
    const bytes = Buffer.from(blob, 'base64');
    if (bytes.length < 28 || bytes.toString('base64') !== blob) throw Error('Invalid sealed workflow');
    const cipher = createDecipheriv('aes-256-gcm', identity.encryption, bytes.subarray(0, 12));
    cipher.setAAD(Buffer.from(canonicalJson([1, identity.id, kind, id]))); cipher.setAuthTag(bytes.subarray(12, 28));
    return JSON.parse(Buffer.concat([cipher.update(bytes.subarray(28)), cipher.final()]).toString('utf8'));
  }
  async request(method, id, body) {
    let response;
    try {
      response = await fetch(`${this.url}/v1/workflows/${id}`, { method, headers: this.headers,
        redirect: 'error', signal: AbortSignal.timeout(this.timeoutMs), ...(body ? { body: JSON.stringify(body) } : {}) });
    } catch { throw Object.assign(Error('Workflow registry unreachable'), { offline: true, code: 'workflow-sync-offline' }); }
    if (!response.ok) {
      await response.body?.cancel();
      throw Object.assign(Error(`Workflow registry HTTP ${response.status}`), { status: response.status,
        offline: [502, 503, 504].includes(response.status), code: `workflow-sync-${response.status}` });
    }
    const reader = response.body.getReader(); let bytes = 0; const chunks = [];
    for (;;) {
      const { done, value } = await reader.read(); if (done) break;
      bytes += value.length;
      if (bytes > 5 * 1024 * 1024) { await reader.cancel(); throw Error('Workflow response exceeds limit'); }
      chunks.push(value);
    }
    return JSON.parse(Buffer.concat(chunks).toString('utf8'));
  }
  async exchange(scope, localState, receipts, limits) {
    const identity = this.identity(scope);
    if (localState.key !== identity.dagKey) throw Error('Local cache predates this shared workspace key; use a separate cache directory');
    let merged = TraceDag.restore(localState, limits).export(), revision = 0;
    const batches = [];
    for (let i = 0; i < receipts.length; i += 100) batches.push(receipts.slice(i, i + 100));
    if (!batches.length) batches.push([]);
    for (const batch of batches) {
      let saved = false;
      for (let attempt = 0; attempt < 5; attempt++) {
        const current = await this.request('GET', identity.id);
        if (!Number.isSafeInteger(current.revision) || current.revision < 0) throw Error('Invalid remote revision');
        if (current.revision > 0) {
          if (!/^[a-f0-9]{64}$/.test(current.versionId) || typeof current.blob !== 'string') throw Error('Invalid remote version');
          const remote = this.open(identity, 'graph', current.versionId, current.blob);
          if (hash(identity.encryption, remote) !== current.versionId || remote.key !== identity.dagKey) throw Error('Remote graph identity mismatch');
          merged = TraceDag.merge(merged, remote, limits).export();
        } else if (current.blob !== null || current.versionId !== null) throw Error('Invalid empty namespace');
        const versionId = hash(identity.encryption, merged);
        const body = { expectedRevision: current.revision, versionId, blob: this.seal(identity, 'graph', versionId, merged),
          runs: batch.map(run => ({ id: run.runId, blob: this.seal(identity, 'run', run.runId, { ...run, graphVersion: versionId }) })) };
        try {
          const result = await this.request('PUT', identity.id, body);
          if (!Number.isSafeInteger(result.revision) || result.revision < current.revision || result.versionId !== versionId
            || canonicalJson(result.storedRunIds) !== canonicalJson(batch.map(run => run.runId))) throw Error('Invalid publication acknowledgment');
          revision = result.revision; saved = true; break;
        }
        catch (error) { if (error.status !== 409) throw error; }
      }
      if (!saved) throw Object.assign(Error('Concurrent publication exceeded retry budget'), { code: 'workflow-sync-conflict' });
    }
    return { dag: merged, revision };
  }
}
