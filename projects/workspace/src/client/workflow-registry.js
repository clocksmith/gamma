// Sealed same-workspace registry. This service never decrypts a graph or executes browser work.
import { createServer } from 'node:http';
import { createHash, timingSafeEqual } from 'node:crypto';
import { statSync } from 'node:fs';
import { join } from 'node:path';
import { PrivateJsonFile } from './private-json-file.js';

const HASH = /^[a-f0-9]{64}$/;
const exact = (v, keys) => v && typeof v === 'object' && !Array.isArray(v)
  && Object.keys(v).sort().join() === [...keys].sort().join();
const failure = (status, code) => Object.assign(Error(code), { status, code });
const digest = value => createHash('sha256').update(value).digest();
const empty = () => ({ version: 1, workflows: {}, workflowVersions: {}, workflowRuns: {} });
const blob = v => typeof v === 'string' && v.length >= 40 && v.length <= 4 * 1024 * 1024 && /^[A-Za-z0-9+/]+={0,2}$/.test(v);
const receiptId = v => typeof v === 'string' && /^[a-f0-9-]{36}$/.test(v);
export class WorkflowRegistry {
  constructor({ directory, maxBytes = 64 * 1024 * 1024 }) {
    this.file = new PrivateJsonFile(join(directory, 'registry.private.json'), { maxBytes, lockWaitMs: 3000, lockRetryMs: 20 });
    this.state = null; this.stamp = null;
    this.read();
  }
  read() {
    let stamp;
    try { const s = statSync(this.file.path); stamp = `${s.ino}/${s.size}/${s.mtimeMs}/${s.ctimeMs}`; }
    catch (e) { if (e.code !== 'ENOENT') throw e; stamp = 'missing'; }
    if (stamp !== this.stamp) {
      const state = this.file.read(empty());
      this.validate(state); this.state = state; this.stamp = stamp;
    }
    return this.state;
  }
  validate(state) {
    if (!exact(state, ['version', 'workflows', 'workflowVersions', 'workflowRuns']) || state.version !== 1
      || [state.workflows, state.workflowVersions, state.workflowRuns].some(v => !v || Array.isArray(v) || typeof v !== 'object')) throw Error('Invalid registry');
    for (const [key, pointer] of Object.entries(state.workflows)) {
      if (!HASH.test(key) || !exact(pointer, ['revision', 'versionId']) || !Number.isSafeInteger(pointer.revision)
        || pointer.revision < 1 || !HASH.test(pointer.versionId)
        || !state.workflowVersions[key + ':' + pointer.versionId]) throw Error('Invalid registry pointer');
    }
    for (const [key, version] of Object.entries(state.workflowVersions)) {
      if (!/^[a-f0-9]{64}:[a-f0-9]{64}$/.test(key) || !exact(version, ['blob', 'clientId', 'createdAt', 'revision', 'parentVersion']) || !blob(version.blob)
        || !Number.isSafeInteger(version.revision) || version.revision < 1
        || !(version.parentVersion === null || HASH.test(version.parentVersion) && state.workflowVersions[key.split(':')[0] + ':' + version.parentVersion])
        || !state.workflows[key.split(':')[0]] || typeof version.clientId !== 'string' || !Number.isFinite(Date.parse(version.createdAt))) throw Error('Invalid sealed version');
    }
    for (const [key, run] of Object.entries(state.workflowRuns)) {
      const [namespace, id] = key.split(':');
      if (!HASH.test(namespace) || !receiptId(id) || !exact(run, ['blob', 'clientId', 'createdAt']) || !blob(run.blob)
        || !state.workflows[namespace] || typeof run.clientId !== 'string' || !Number.isFinite(Date.parse(run.createdAt))) throw Error('Invalid sealed receipt');
    }
  }
  key(workspace, namespace) {
    if (!HASH.test(namespace)) throw failure(400, 'invalid-namespace');
    return digest(JSON.stringify([workspace, namespace])).toString('hex');
  }
  checkout(workspace, namespace) {
    const state = this.read(), key = this.key(workspace, namespace), pointer = state.workflows[key];
    return pointer ? { ...pointer, blob: state.workflowVersions[key + ':' + pointer.versionId].blob }
      : { revision: 0, versionId: null, blob: null };
  }
  async publish(principal, namespace, request) {
    if (!exact(request, ['expectedRevision', 'versionId', 'blob', 'runs'])
      || !Number.isSafeInteger(request.expectedRevision) || request.expectedRevision < 0
      || !HASH.test(request.versionId) || !blob(request.blob) || !Array.isArray(request.runs)
      || request.runs.length > 100 || !request.runs.every(r => exact(r, ['id', 'blob']) && receiptId(r.id) && blob(r.blob))) {
      throw failure(400, 'invalid-publication');
    }
    const key = this.key(principal.workspaceId, namespace);
    return this.file.transaction(() => {
      // Reload under the cross-process lock. Memory is only a read cache.
      const state = this.file.read(empty()); this.validate(state);
      const pointer = state.workflows[key];
      if ((pointer?.revision ?? 0) !== request.expectedRevision) throw failure(409, 'revision-conflict');
      const versionKey = key + ':' + request.versionId;
      const record = payload => ({ blob: payload, clientId: principal.clientId, createdAt: new Date().toISOString() });
      let changed = false;
      if (pointer?.versionId !== request.versionId) {
        const revision = (pointer?.revision ?? 0) + 1;
        if (!Number.isSafeInteger(revision)) throw failure(409, 'revision-exhausted');
        state.workflowVersions[versionKey] ??= { ...record(request.blob), revision, parentVersion: pointer?.versionId ?? null };
        state.workflows[key] = { revision, versionId: request.versionId }; changed = true;
      }
      for (const run of request.runs) {
        const id = key + ':' + run.id;
        if (!state.workflowRuns[id]) { state.workflowRuns[id] = record(run.blob); changed = true; }
      }
      if (changed) { this.validate(state); this.file.write(state); }
      this.stamp = null; this.read();
      return { ...state.workflows[key], storedRunIds: request.runs.map(r => r.id) };
    });
  }
}

export function registryServer({ registry, clients, maxRequestBytes = 5 * 1024 * 1024 }) {
  if (!Array.isArray(clients) || !clients.length || clients.some(c => !c.workspaceId || !c.clientId || !HASH.test(c.tokenHash))) throw Error('Explicit client credentials required');
  const server = createServer(async (req, res) => {
    const send = (status, data) => { res.writeHead(status, { 'Content-Type': 'application/json',
      'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' }); res.end(JSON.stringify(data)); };
    try {
      // App credential is independent of Cloudflare Access; no trust in spoofable proxy headers.
      const token = /^Bearer ([^\s]{32,256})$/.exec(req.headers.authorization ?? '')?.[1];
      const hash = digest(token ?? '');
      const principal = clients.find(c => timingSafeEqual(hash, Buffer.from(c.tokenHash, 'hex')));
      if (!token || !principal) { req.resume(); return send(401, { error: 'unauthorized' }); }
      if (req.headers.origin) { req.resume(); return send(403, { error: 'browser-origin-denied' }); }
      if (req.method === 'GET' && req.url === '/health') return send(200, { ready: true, format: 1 });
      const route = /^\/v1\/workflows\/([a-f0-9]{64})$/.exec(req.url ?? '');
      if (!route) { req.resume(); return send(404, { error: 'not-found' }); }
      if (req.method === 'GET') return send(200, registry.checkout(principal.workspaceId, route[1]));
      if (req.method !== 'PUT') { req.resume(); return send(405, { error: 'method-not-allowed' }); }
      if (req.headers['content-type'] !== 'application/json') { req.resume(); return send(415, { error: 'json-required' }); }
      let size = 0; const chunks = [];
      for await (const chunk of req) {
        size += chunk.length;
        if (size > maxRequestBytes) throw failure(413, 'request-too-large');
        chunks.push(chunk);
      }
      let body;
      try { body = JSON.parse(Buffer.concat(chunks).toString('utf8')); } catch { throw failure(400, 'invalid-json'); }
      return send(200, await registry.publish(principal, route[1], body));
    } catch (error) {
      const status = error.status ?? (error.code === 'workflow-store-busy' ? 503 : error.code === 'workflow-store-limit' ? 507 : 500);
      if (!res.headersSent) send(status, { error: error.status || error.code ? error.code : 'registry-error' });
    }
  });
  server.requestTimeout = 15000; server.headersTimeout = 10000;
  return server;
}
