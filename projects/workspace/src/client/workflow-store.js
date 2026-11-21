// Personal workflow persistence on one host. Only verified runs publish; no graph import API.
// Exclusive file creation serializes processes. A crashed lock is never automatically stolen.
import { randomUUID } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { PrivateJsonFile } from './private-json-file.js';
import { canonicalJson, sha256Hex } from '../journal.js';
import { TraceDag } from './trace-dag.js';
import { runWorkflow } from './workflow-agent.js';
import { WorkflowAttempts, attemptErrorCode } from './workflow-attempts.js';

const VERSION = 1;
const HASH = /^[a-f0-9]{64}$/;
const SOURCE_FILES = ['private-json-file.js', 'workflow-attempts.js', 'workflow-sync.js', 'workflow-store.js', 'workflow-agent.js', 'trace-dag.js', 'trace-graph-dp.js', 'suffix-eligibility.js', 'field-group-scope.js', 'controller.js',
  'agent.js', '../adapters/page-query.js', '../service.js'];
const STATIC_SOURCE_HASHES = Object.freeze(Object.fromEntries(SOURCE_FILES.map(path => [path,
  sha256Hex(readFileSync(new URL(path, import.meta.url)))])));
const VALIDATED_DAG_CACHE = new Map();
const ALLOWED_DAG_OPTIONAL_KEYS = new Set(['goalTerminals', 'suffixProfiles', 'slotRoles']);
function hasValidDagKeys(dag) {
  if (!dag || typeof dag !== 'object' || Array.isArray(dag)) return false;
  const baseKeys = Object.keys(dag).filter(k => !ALLOWED_DAG_OPTIONAL_KEYS.has(k)).sort().join(',');
  return baseKeys === 'key,limits,nodes,version'
    && Object.keys(dag).every(k => ['version', 'key', 'limits', 'nodes'].includes(k) || ALLOWED_DAG_OPTIONAL_KEYS.has(k));
}
const exactKeys = (value, keys) => value && typeof value === 'object'
  && !Array.isArray(value) && Object.keys(value).sort().join() === [...keys].sort().join();
const identifier = value => typeof value === 'string' && value.trim().length > 0;
const fail = (code, message) => { throw Object.assign(Error(message), { code }); };
const locatorValid = value => Array.isArray(value) && value.length === 4
  && value.every(part => typeof part === 'string');
const hashMapValid = value => value && !Array.isArray(value) && typeof value === 'object'
  && Object.keys(value).length > 0 && Object.values(value).every(hash => typeof hash === 'string' && HASH.test(hash));
const RUN_KEYS = ['runId', 'startedAt', 'completedAt', 'mode', 'completed', 'reviewVerified',
  'verificationId', 'policyHash', 'sourceHashes', 'taskSourceHashes', 'planner', 'modelCalls',
  'cacheSteps', 'elapsedMs', 'fallbackReason', 'interventionRequests', 'workflowId', 'baseVersion', 'resultVersion'];

/** Trusted host API, not an HTTP body or a public recipe importer. The caller supplies an
 * independently implemented account verifier and task review oracle, never model callbacks.
 * Limits and lock timing are explicit host policy. The whole export, including key, is sensitive.
 */
export class WorkflowStore {
  constructor({ directory, ownerScope, limits, maxBytes, lockWaitMs, lockRetryMs, sync = null, attemptMaxBytes = maxBytes }) {
    if (typeof process.getuid !== 'function') throw Error('Private workflow store requires POSIX permissions');
    if (!identifier(ownerScope) || !identifier(directory)
      || [maxBytes, lockWaitMs, lockRetryMs].some(value => !Number.isSafeInteger(value) || value < 1)) {
      throw Error('Workflow store requires owner scope, directory, byte limit and bounded lock timings');
    }
    new TraceDag(limits);
    this.directory = resolve(directory);
    this.path = join(this.directory, 'workflows.private.json');
    this.lockPath = join(this.directory, 'workflows.lock');
    this.file = new PrivateJsonFile(this.path, { maxBytes, lockWaitMs, lockRetryMs });
    this.file.lockPath = this.lockPath;
    this.attempts = new WorkflowAttempts(join(this.directory, 'workflow-attempts.private.json'), {
      maxBytes: attemptMaxBytes, lockWaitMs, lockRetryMs });
    if (sync && sync.ownerScope !== ownerScope) throw Error('Sync owner differs from local owner');
    this.sync = sync;
    this.ownerScope = ownerScope;
    this.limits = Object.freeze({ ...limits });
    this.maxBytes = maxBytes;
    this.lockWaitMs = lockWaitMs;
    this.lockRetryMs = lockRetryMs;
  }
  #namespace({ accountScope, template }) {
    if (!identifier(accountScope) || !identifier(template)) throw Error('Explicit account scope and template are required');
    return sha256Hex(canonicalJson([this.ownerScope, accountScope, template]));
  }
  #read() {
    return this.#validate(this.file.read({ version: VERSION, workflows: {}, workflowVersions: {}, workflowRuns: [] }));
  }
  #validate(state) {
    if (!exactKeys(state, ['version', 'workflows', 'workflowVersions', 'workflowRuns']) || state.version !== VERSION
      || [state.workflows, state.workflowVersions].some(value => !value || Array.isArray(value) || typeof value !== 'object')
      || !Array.isArray(state.workflowRuns)) throw Error('Invalid workflow store');
    for (const [id, pointer] of Object.entries(state.workflows)) {
      if (!HASH.test(id) || !exactKeys(pointer, ['revision', 'currentVersion'])
        || !Number.isSafeInteger(pointer.revision) || pointer.revision < 0
        || state.workflowVersions[pointer.currentVersion]?.workflowId !== id
        || state.workflowVersions[pointer.currentVersion]?.revision !== pointer.revision) throw Error('Invalid workflow pointer');
    }
    for (const [verId, entry] of Object.entries(state.workflowVersions)) {
      if (!exactKeys(entry, ['workflowId', 'revision', 'parentVersion', 'dag']) || !state.workflows[entry.workflowId]
        || !Number.isSafeInteger(entry.revision) || entry.revision < 0
        || !hasValidDagKeys(entry.dag)) throw Error('Invalid workflow namespace');
      const cacheKey = `${verId}:${canonicalJson(this.limits)}:${sha256Hex(canonicalJson(entry.dag))}`;
      if (!VALIDATED_DAG_CACHE.has(cacheKey)) {
        TraceDag.restore(entry.dag, this.limits);
        if (VALIDATED_DAG_CACHE.size > 512) VALIDATED_DAG_CACHE.clear();
        VALIDATED_DAG_CACHE.set(cacheKey, true);
      }
      if (entry.revision === 0 ? entry.parentVersion !== null
        : state.workflowVersions[entry.parentVersion]?.revision !== entry.revision - 1
          || state.workflowVersions[entry.parentVersion]?.workflowId !== entry.workflowId
          || state.workflowVersions[entry.parentVersion]?.dag.key !== entry.dag.key) throw Error('Invalid workflow lineage');
    }
    for (const run of state.workflowRuns) {
      if (!exactKeys(run, RUN_KEYS) || !identifier(run.runId) || !state.workflows[run.workflowId]
        || state.workflowVersions[run.baseVersion]?.workflowId !== run.workflowId
        || state.workflowVersions[run.resultVersion]?.workflowId !== run.workflowId
        || !['learn', 'reuse', 'fresh'].includes(run.mode)
        || typeof run.completed !== 'boolean' || typeof run.reviewVerified !== 'boolean'
        || !identifier(run.verificationId) || !HASH.test(run.policyHash)
        || !hashMapValid(run.sourceHashes) || !hashMapValid(run.taskSourceHashes)
        || !exactKeys(run.planner, ['declaredModel', 'observedModels'])
        || !(run.planner.declaredModel === null || typeof run.planner.declaredModel === 'string')
        || !Array.isArray(run.planner.observedModels) || !run.planner.observedModels.every(identifier)
        || ![run.startedAt, run.completedAt].every(value => typeof value === 'string' && Number.isFinite(Date.parse(value)))
        || ![run.modelCalls, run.cacheSteps, run.interventionRequests].every(value => Number.isSafeInteger(value) && value >= 0)
        || !Number.isFinite(run.elapsedMs) || run.elapsedMs < 0
        || !(run.fallbackReason === null || typeof run.fallbackReason === 'string')) throw Error('Invalid workflow run');
    }
    return state;
  }
  #write(state) { this.#validate(state); this.file.write(state); }
  async #transaction(update) { return this.file.transaction(() => update(this.#read())); }
  summary(scope) {
    const id = this.#namespace(scope);
    const state = this.#read();
    const pointer = state.workflows[id];
    if (!pointer) return { revision: 0, hasLearnedGraph: false };
    const dag = state.workflowVersions[pointer.currentVersion].dag;
    return { revision: pointer.revision, hasLearnedGraph: Object.keys(dag.nodes).length > 0 };
  }
  async checkout(scope) {
    const id = this.#namespace(scope);
    const initial = this.#read();
    const snapshot = state => {
      const pointer = state.workflows[id];
      return structuredClone({ revision: pointer.revision, versionId: pointer.currentVersion,
        dag: state.workflowVersions[pointer.currentVersion].dag });
    };
    if (initial.workflows[id]) return snapshot(initial);
    return this.#transaction(state => {
      if (!state.workflows[id]) {
        const versionId = randomUUID();
        state.workflowVersions[versionId] = { workflowId: id, revision: 0, parentVersion: null,
          dag: this.sync ? this.sync.empty(scope, this.limits) : new TraceDag(this.limits).export() };
        state.workflows[id] = { revision: 0, currentVersion: versionId };
        this.#write(state);
      }
      return snapshot(state);
    });
  }
  async synchronize(scope) {
    if (!this.sync) return { status: 'disabled' };
    const local = await this.checkout(scope);
    const state = this.#read();
    const runs = state.workflowRuns.filter(run => run.workflowId === this.#namespace(scope)).map(run => ({ ...run,
      baseGraph: this.sync.version(scope, state.workflowVersions[run.baseVersion].dag),
      resultGraph: this.sync.version(scope, state.workflowVersions[run.resultVersion].dag) }));
    runs.push(...this.readAttempts().filter(attempt => attempt.scopeHash === this.#namespace(scope)
      && attempt.status !== 'pending').map(attempt => ({
      // Separate deterministic UUID-shaped receipt identity; legacy run IDs remain immutable.
      runId: sha256Hex(`workflow-attempt/v1:${attempt.runId}`).slice(0, 32)
        .replace(/(.{8})(.{4})(.{4})(.{4})(.{12})/, '$1-$2-$3-$4-$5'),
      schema: 'fawn.workflow-attempt/v1', attempt })));
    const remote = await this.sync.exchange(scope, local.dag, runs, this.limits);
    return this.#transaction(state => {
      const id = this.#namespace(scope), pointer = state.workflows[id];
      const latest = state.workflowVersions[pointer.currentVersion];
      const merged = TraceDag.merge(latest.dag, remote.dag, this.limits).export();
      if (canonicalJson(merged) !== canonicalJson(latest.dag)) {
        const versionId = randomUUID();
        state.workflowVersions[versionId] = { workflowId: id, revision: pointer.revision + 1,
          parentVersion: pointer.currentVersion, dag: merged };
        state.workflows[id] = { revision: pointer.revision + 1, currentVersion: versionId };
        this.#write(state);
      }
      return { status: 'synced', revision: remote.revision };
    });
  }
  async #complete(scope, checkout, trace, receipt) {
    return this.#transaction(state => {
      const id = this.#namespace(scope), pointer = state.workflows[id];
      const latest = state.workflowVersions[pointer?.currentVersion];
      if (!latest || latest.dag.key !== checkout.dag.key || latest.revision < checkout.revision) {
        fail('workflow-store-lineage', 'Workflow lineage changed; refusing publication');
      }
      const dag = TraceDag.restore(latest.dag, this.limits);
      if (trace) {
        dag.publish(trace.records, trace.terminal, trace.repairs, {
          ...(trace.suffixProfiles ? { suffixProfiles: trace.suffixProfiles } : {}),
          ...(trace.slotRoles ? { slotRoles: trace.slotRoles } : {}),
        });
      }
      const next = dag.export();
      if (canonicalJson(next) !== canonicalJson(latest.dag)) {
        if (!Number.isSafeInteger(latest.revision + 1)) throw Error('Workflow revision exhausted');
        const versionId = randomUUID();
        state.workflowVersions[versionId] = { workflowId: id, revision: latest.revision + 1,
          parentVersion: pointer.currentVersion, dag: next };
        state.workflows[id] = { revision: latest.revision + 1, currentVersion: versionId };
      }
      const current = state.workflows[id];
      state.workflowRuns.push({ ...receipt, workflowId: id, baseVersion: checkout.versionId,
        resultVersion: current.currentVersion });
      this.#write(state);
      return { status: trace ? 'published' : 'unchanged', revision: current.revision,
        versionId: current.currentVersion, receiptStored: true };
    });
  }
  readAttempts() { return this.attempts.records(sha256Hex(this.ownerScope)); }
  async run(input) {
    const runId = randomUUID(), startedAt = new Date().toISOString();
    const scopeHash = identifier(input?.accountScope) && identifier(input?.template)
      ? this.#namespace(input) : null;
    const accounting = { runId, startedAt, execution: null };
    // Fail closed if even the start cannot be persisted. No verifier, model or browser is called.
    try {
      await this.attempts.begin({ runId, startedAt, ownerHash: sha256Hex(this.ownerScope), scopeHash,
        mode: ['learn', 'reuse', 'fresh'].includes(input?.mode) ? input.mode : null });
    } catch (error) {
      error.attempt = { runId, receiptStored: false, code: attemptErrorCode(error) };
      throw error;
    }
    let result;
    try { result = await this.#run(input, accounting); }
    catch (cause) {
      const error = cause instanceof Error ? cause : Error('Workflow attempt failed');
      try {
        await this.attempts.update(runId, { status: 'rejected', stage: 'finished', failureCode: attemptErrorCode(error) });
        error.attempt = { runId, receiptStored: true };
      } catch (storageError) { error.attempt = { runId, receiptStored: false, code: attemptErrorCode(storageError) }; }
      throw error;
    }
    let attempt;
    try {
      const persistence = result.persistence;
      await this.attempts.update(runId, { status: 'finished', stage: 'finished', execution: accounting.execution,
        publication: { status: persistence.status, code: persistence.code ?? null,
          revision: persistence.revision ?? null, versionId: persistence.versionId ?? null } });
      attempt = { runId, receiptStored: true };
    } catch (error) { attempt = { runId, receiptStored: false, code: attemptErrorCode(error) }; }
    if (this.sync && attempt.receiptStored) {
      try { result.synchronization = await this.synchronize(input); }
      catch (error) { result.synchronization = { status: 'pending', code: error.code ?? 'workflow-sync-failed' }; }
    }
    return { ...result, attempt };
  }
  async #run({ accountScope, verifyAccount, verificationId, taskSourceHashes, disclosurePolicy, ...options }, accounting) {
    if (typeof verifyAccount !== 'function' || typeof options.verifyReview !== 'function'
      || !identifier(verificationId) || !hashMapValid(taskSourceHashes)) {
      throw Error('Trusted account and review verifiers are required');
    }
    const frozenTaskSources = structuredClone(taskSourceHashes);
    const fieldGroups = options.fieldGroups ? structuredClone(options.fieldGroups) : null;
    const learnRepairs = options.learnRepairs ?? true;
    if (typeof learnRepairs !== 'boolean') throw Error('Explicit boolean repair-learning policy required');
    // Snapshot trusted disclosure rules before any asynchronous work. Models cannot add rules.
    const policy = structuredClone(disclosurePolicy);
    if (!exactKeys(policy, ['origin', 'fields', 'intermediateClicks'])
      || !['http:', 'https:'].includes(new URL(policy.origin).protocol)
      || new URL(policy.origin).origin !== policy.origin || !Array.isArray(policy.fields)
      || !Array.isArray(policy.intermediateClicks) || !policy.intermediateClicks.every(locatorValid)
      || !policy.fields.every(field => exactKeys(field, ['kind', 'slot', 'locator'])
        && ['fill', 'select'].includes(field.kind) && identifier(field.slot) && locatorValid(field.locator))) {
      throw Error('Explicit origin, slot-to-field rules and intermediate click policy are required');
    }
    const scope = { accountScope, template: options.template };
    const sourceHashes = { ...STATIC_SOURCE_HASHES };
    const policyHash = sha256Hex(canonicalJson({ disclosure: policy, fieldGroups, learnRepairs,
      observationScope: 'authorized-controls-v1' }));
    accounting.context = { verificationId,
      policyHash,
      sourceHashes, taskSourceHashes: frozenTaskSources,
      planner: { declaredModel: options.planner?.identity?.model ?? null, observedModels: [] } };
    await this.attempts.update(accounting.runId, { context: accounting.context });
    const identity = { service: options.service, owner: options.owner, pageId: options.pageId };
    const assertContext = async () => {
      options.signal.throwIfAborted();
      if (await verifyAccount(identity) !== accountScope) fail('workflow-account-mismatch', 'Website account does not match this private workflow scope');
    };
    await assertContext();
    let synchronization = { status: 'disabled' };
    if (this.sync) {
      try { synchronization = await this.synchronize(scope); }
      catch (error) {
        if (!error.offline) throw error;
        synchronization = { status: 'offline', code: error.code };
      }
    }
    const checkout = await this.checkout(scope);
    const observedModels = new Set();
    const planner = { identity: options.planner?.identity, next: async (...args) => {
      const proposal = await options.planner.next(...args);
      for (const model of proposal.usage?.models ?? []) observedModels.add(model);
      return proposal;
    } };
    const startedAt = accounting.startedAt;
    let learned = null;
    await this.attempts.update(accounting.runId, { stage: 'executing' });
    const result = await runWorkflow({ ...options, learnRepairs,
      observationLocators: [...policy.fields.map(field => field.locator), ...policy.intermediateClicks],
      fieldGroups, accountScope, planner, dag: TraceDag.restore(checkout.dag, this.limits),
      intermediateClicks: policy.intermediateClicks, assertContext,
      authorizeStep: async step => {
        const permitted = step.origin === policy.origin && (step.kind === 'click'
          ? policy.intermediateClicks.some(locator => canonicalJson(locator) === canonicalJson(step.locator))
          : policy.fields.some(field => field.kind === step.kind && field.slot === step.slot
            && canonicalJson(field.locator) === canonicalJson(step.locator)));
        if (!permitted) fail('workflow-disclosure-denied', 'Input slot is not authorized for this field and origin');
      },
      publishTrace: async trace => { learned = trace; },
    });
    let persistence;
    accounting.execution = { completed: result.completed, reviewVerified: result.verification?.completed === true,
      modelCalls: result.modelCalls, cacheSteps: result.cacheSteps, elapsedMs: result.elapsedMs,
      fallbackReason: result.fallbackReason, interventionRequests: result.interventionRequests };
    accounting.context.planner.observedModels = [...observedModels];
    try {
      await this.attempts.update(accounting.runId, { stage: 'execution-settled', execution: accounting.execution,
        context: accounting.context });
      if (result.completed && learned) await assertContext();
      persistence = await this.#complete(scope, checkout, result.completed ? learned : null, {
        runId: accounting.runId, startedAt, completedAt: new Date().toISOString(), mode: options.mode,
        completed: result.completed, reviewVerified: result.verification?.completed === true,
        verificationId, policyHash, sourceHashes, taskSourceHashes: frozenTaskSources,
        planner: { declaredModel: options.planner?.identity?.model ?? null, observedModels: [...observedModels] },
        modelCalls: result.modelCalls, cacheSteps: result.cacheSteps, elapsedMs: result.elapsedMs,
        fallbackReason: result.fallbackReason, interventionRequests: result.interventionRequests,
      });
    } catch (error) {
      // A verified browser result remains true even if saving fails. Never rerun its effects.
      persistence = { status: 'failed', receiptStored: false,
        code: error.code ?? 'workflow-publication-failed', detail: error.message };
    }
    return { ...result, persistence, synchronization };
  }
}
