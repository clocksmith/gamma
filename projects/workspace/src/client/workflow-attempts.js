// Cross-process attempt accounting, independent of graph publication and browser effect truth.
import { PrivateJsonFile } from './private-json-file.js';

const exact = (value, keys) => value && typeof value === 'object' && !Array.isArray(value)
  && Object.keys(value).sort().join() === [...keys].sort().join();
const date = value => typeof value === 'string' && Number.isFinite(Date.parse(value));
const hash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const KEYS = ['runId', 'ownerHash', 'scopeHash', 'mode', 'startedAt', 'updatedAt', 'status',
  'stage', 'context', 'execution', 'publication', 'failureCode'];
const PUBLICATION_KEYS = ['status', 'code', 'revision', 'versionId'];
const EXECUTION_KEYS = ['completed', 'reviewVerified', 'modelCalls', 'cacheSteps', 'elapsedMs', 'fallbackReason', 'interventionRequests'];

export function attemptErrorCode(error) {
  return typeof error?.code === 'string' && /^[a-z][a-z0-9.-]{0,127}$/.test(error.code)
    ? error.code : 'workflow-attempt-failed';
}

export class WorkflowAttempts {
  constructor(path, limits) { this.file = new PrivateJsonFile(path, limits); }
  read() { return this.#validate(this.file.read({ version: 1, attempts: {} })); }
  #validate(state) {
    if (!exact(state, ['version', 'attempts']) || state.version !== 1
      || !state.attempts || Array.isArray(state.attempts) || typeof state.attempts !== 'object') throw Error('Invalid workflow attempts');
    for (const [id, entry] of Object.entries(state.attempts)) {
      if (!exact(entry, KEYS) || id !== entry.runId || !/^[a-f0-9-]{36}$/.test(id)
        || !hash(entry.ownerHash) || !(entry.scopeHash === null || hash(entry.scopeHash))
        || ![null, 'learn', 'reuse', 'fresh'].includes(entry.mode)
        || !date(entry.startedAt) || !date(entry.updatedAt)
        || !['pending', 'finished', 'rejected'].includes(entry.status)
        || !['preflight', 'executing', 'execution-settled', 'finished'].includes(entry.stage)
        || !(entry.failureCode === null || typeof entry.failureCode === 'string')) throw Error('Invalid workflow attempt');
      if (entry.context !== null && (!exact(entry.context, ['verificationId', 'policyHash', 'sourceHashes', 'taskSourceHashes', 'planner'])
        || typeof entry.context.verificationId !== 'string' || !hash(entry.context.policyHash)
        || ![entry.context.sourceHashes, entry.context.taskSourceHashes].every(map => map && !Array.isArray(map)
          && typeof map === 'object' && Object.keys(map).length && Object.values(map).every(hash))
        || !exact(entry.context.planner, ['declaredModel', 'observedModels'])
        || !(entry.context.planner.declaredModel === null || typeof entry.context.planner.declaredModel === 'string')
        || !Array.isArray(entry.context.planner.observedModels)
        || !entry.context.planner.observedModels.every(model => typeof model === 'string'))) throw Error('Invalid workflow attempt context');
      if (entry.execution !== null && (!exact(entry.execution, EXECUTION_KEYS)
        || typeof entry.execution.completed !== 'boolean' || typeof entry.execution.reviewVerified !== 'boolean'
        || !['modelCalls', 'cacheSteps', 'interventionRequests'].every(key => Number.isSafeInteger(entry.execution[key]) && entry.execution[key] >= 0)
        || !Number.isFinite(entry.execution.elapsedMs) || entry.execution.elapsedMs < 0
        || !(entry.execution.fallbackReason === null || typeof entry.execution.fallbackReason === 'string'))) throw Error('Invalid workflow attempt execution');
      if (entry.publication !== null && (!exact(entry.publication, PUBLICATION_KEYS)
        || !['published', 'unchanged', 'failed'].includes(entry.publication.status)
        || !(entry.publication.code === null || typeof entry.publication.code === 'string')
        || !(entry.publication.revision === null || Number.isSafeInteger(entry.publication.revision) && entry.publication.revision >= 0)
        || !(entry.publication.versionId === null || typeof entry.publication.versionId === 'string'))) throw Error('Invalid workflow attempt publication');
    }
    return state;
  }
  async begin({ runId, ownerHash, scopeHash, mode, startedAt }) {
    return this.file.transaction(() => {
      const state = this.read();
      if (state.attempts[runId]) throw Error('Duplicate workflow attempt');
      state.attempts[runId] = { runId, ownerHash, scopeHash, mode, startedAt, updatedAt: startedAt,
        status: 'pending', stage: 'preflight', context: null, execution: null, publication: null, failureCode: null };
      this.#validate(state);
      this.file.write(state);
      return structuredClone(state.attempts[runId]);
    });
  }
  async update(runId, changes) {
    if (Object.keys(changes).some(key => !['status', 'stage', 'context', 'execution', 'publication', 'failureCode'].includes(key))) throw Error('Invalid attempt update');
    return this.file.transaction(() => {
      const state = this.read(), previous = state.attempts[runId];
      if (!previous || previous.status !== 'pending') throw Error('Attempt is absent or already terminal');
      const entry = { ...previous, ...structuredClone(changes), updatedAt: new Date().toISOString() };
      // Validate the new record before replacing the last durable snapshot.
      this.#validate({ version: 1, attempts: { [runId]: entry } });
      state.attempts[runId] = entry;
      this.file.write(state);
      return entry;
    });
  }
  records(ownerHash) {
    return Object.values(this.read().attempts).filter(entry => entry.ownerHash === ownerHash).map(entry => structuredClone(entry));
  }
}
