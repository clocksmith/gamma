// Host-only orchestration for already-authorized, review-only recipes.
import { randomUUID } from 'node:crypto';
import { join } from 'node:path';
import { sha256Hex } from '../journal.js';
import { PrivateJsonFile } from './private-json-file.js';

const TERMINAL = new Set(['reviewed', 'stopped', 'cancelled', 'interrupted']);
const OCCUPIED = new Set(['running', 'cancelling', 'needs-attention']);
const itemLimit = 32;
const wallLimitMs = 15 * 60 * 1000;
const text = value => typeof value === 'string' && value.length > 0 && value.length <= 256;
const uuid = value => text(value) && /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/.test(value);
const stop = (code, message) => Object.assign(Error(message), { code });
const codeFor = error => /^[a-z][a-z0-9.-]{0,127}$/.test(error?.code ?? '') ? error.code : 'batch-child-failed';

export function prepareReviewBatch(input, policy, maxInputBytes) {
  const { template, versionId, items, budgetMs } = input ?? {};
  if (!policy || typeof policy.verifyRecord !== 'function' || typeof policy.authorizeReadOnlyStep !== 'function'
    || !Number.isSafeInteger(policy.maxItems) || policy.maxItems < 1 || policy.maxItems > itemLimit
    || !Number.isSafeInteger(policy.maxWallMs) || policy.maxWallMs < 1 || policy.maxWallMs > wallLimitMs) {
    throw stop('batch-review-policy-required', 'An installed trusted review-only batch policy is required');
  }
  if (!text(template) || !uuid(versionId) || !Number.isSafeInteger(budgetMs) || budgetMs < 1
    || budgetMs > policy.maxWallMs || !Array.isArray(items) || !items.length || items.length > policy.maxItems) {
    throw stop('batch-invalid', 'Provide a pinned recipe, bounded duration and an explicit record manifest');
  }
  const seen = new Set();
  const manifest = items.map(item => {
    const { recordId, pageId, inputs } = item ?? {};
    if (!text(recordId) || seen.has(recordId) || !text(pageId) || !inputs
      || typeof inputs !== 'object' || Array.isArray(inputs) || Object.values(inputs).some(value => typeof value !== 'string')
      || Buffer.byteLength(JSON.stringify(inputs)) > maxInputBytes) {
      throw stop('batch-invalid-item', 'Each item needs a distinct record, open page and bounded inputs');
    }
    seen.add(recordId);
    return { recordId, pageId, inputs: structuredClone(inputs) };
  });
  return { template, versionId, budgetMs, manifest,
    policy: { verifyRecord: policy.verifyRecord, authorizeReadOnlyStep: policy.authorizeReadOnlyStep } };
}

export class ReviewBatches {
  constructor(directory) {
    this.directory = directory;
  }
  #file(projectId) {
    return new PrivateJsonFile(join(this.directory, sha256Hex(projectId) + '.json'),
      { maxBytes: 64 * 1024, lockWaitMs: 1000, lockRetryMs: 10 });
  }
  read(projectId) {
    const job = this.#file(projectId).read(null);
    if (job !== null && (job.schema !== 1 || !uuid(job.id) || job.projectId !== projectId
      || (!OCCUPIED.has(job.status) && !TERMINAL.has(job.status)) || !Array.isArray(job.items))) {
      throw stop('batch-invalid-journal', 'Invalid batch journal; no work admitted');
    }
    return job;
  }
  async #change(projectId, fn) {
    const file = this.#file(projectId);
    return file.transaction(() => {
      const job = this.read(projectId);
      const next = fn(job);
      if (next !== job) file.write(next);
      return next;
    });
  }
  assertAdmission(projectId, batchId = null) {
    const job = this.read(projectId);
    if (batchId !== null
      ? job?.id !== batchId || job.status !== 'running'
      : OCCUPIED.has(job?.status)) {
      throw stop('batch-owns-workspace', 'A different or cancelled batch owns this workspace');
    }
  }
  reserve(projectId, { template, versionId, budgetMs, manifest }) {
    return this.#change(projectId, previous => {
      if (OCCUPIED.has(previous?.status)) throw stop('batch-owns-workspace', 'An existing batch owns this workspace');
      const startedAt = Date.now();
      return { schema: 1, id: randomUUID(), projectId, template, versionId, budgetMs,
        startedAt, deadline: startedAt + budgetMs, status: 'running', failureCode: null,
        items: manifest.map(({ recordId, pageId }) => ({ recordDigest: sha256Hex(recordId), pageId,
          status: 'pending', attemptId: null, receiptStored: false })) };
    });
  }
  setItem(projectId, id, index, status, attempt = null) {
    return this.#change(projectId, job => {
      if (job?.id !== id) throw stop('batch-lost-reservation', 'Batch reservation changed');
      const previous = job.items[index];
      const valid = status === 'running' ? job.status === 'running' && previous?.status === 'pending'
        : ['reviewed', 'stopped'].includes(status) && previous?.status === 'running';
      if (!valid) throw stop('batch-item-transition', 'Batch item cannot transition');
      const items = job.items.map((item, i) => i === index ? { ...item, status,
        attemptId: uuid(attempt?.runId) ? attempt.runId : null, receiptStored: attempt?.receiptStored === true } : item);
      return { ...job, items };
    });
  }
  cancel(projectId) {
    return this.#change(projectId, job => job?.status === 'running' ? { ...job, status: 'cancelling' } : job);
  }
  finish(projectId, id, status, failureCode = null) {
    return this.#change(projectId, job => {
      if (!OCCUPIED.has(job?.status) || (id !== null && job.id !== id)) return job;
      const items = status === 'reviewed' ? job.items
        : job.items.map(item => item.status === 'running' ? { ...item, status: 'interrupted' } : item);
      return { ...job, status: job.status === 'cancelling' && !['interrupted', 'needs-attention'].includes(status) ? 'cancelled' : status,
        failureCode, items, finishedAt: Date.now() };
    });
  }
}

export async function driveReviewBatch(journal, job, manifest, signal, start) {
  let status = 'stopped', failure = null;
  try {
    for (const [index, item] of manifest.entries()) {
      signal.throwIfAborted();
      if (Date.now() >= job.deadline) throw stop('batch-deadline', 'Batch deadline reached');
      journal.assertAdmission(job.projectId, job.id);
      await journal.setItem(job.projectId, job.id, index, 'running');
      let attempt = null;
      let reviewed = false;
      try {
        signal.throwIfAborted();
        const child = await start(item);
        const result = await child.done;
        attempt = result.attempt;
        reviewed = !signal.aborted && result.completed === true && result.verification?.completed === true
          && attempt?.receiptStored === true && uuid(attempt?.runId);
        if (!reviewed) throw stop('batch-review-unconfirmed', 'Child did not leave a verified review receipt');
      } catch (error) {
        attempt ??= error.attempt;
        throw error;
      } finally {
        await journal.setItem(job.projectId, job.id, index, reviewed ? 'reviewed' : 'stopped', attempt);
      }
    }
    signal.throwIfAborted();
    status = 'reviewed';
  } catch (error) {
    const errorCode = codeFor(error);
    if (['batch-child-cleanup-failed', 'workflow-setup-cleanup-failed'].includes(errorCode)) {
      status = 'needs-attention';
      failure = errorCode;
    } else {
      failure = signal.reason?.name === 'TimeoutError' ? 'batch-deadline' : errorCode;
    }
  }
  return journal.finish(job.projectId, job.id, status, failure);
}
